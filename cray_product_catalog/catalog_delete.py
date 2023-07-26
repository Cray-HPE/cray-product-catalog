#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2021-2023 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

"""
This script takes a PRODUCT and PRODUCT_VERSION and deletes the content
in a Kubernetes ConfigMap in one of two ways:

If a 'key' is specified within a PRODUCT/PRODUCT_VERSION:

{PRODUCT}:
  {PRODUCT_VERSION}:
    {key}        # <- content to delete

If a 'key' is not specified:

{PRODUCT}:
  {PRODUCT_VERSION}: # <- delete entire version

Since updates to a ConfigMap are not atomic, this script will continue to
attempt to modify the ConfigMap until it has been patched successfully.
"""

import logging
import os
import random
import time
import urllib3
from urllib3.util.retry import Retry

from kubernetes import client
from kubernetes.client.api_client import ApiClient
from kubernetes.client.rest import ApiException
import yaml

from cray_product_catalog.logging import configure_logging
from cray_product_catalog.util import load_k8s
from cray_product_catalog.util.catalog_data_helper import format_product_cm_name
from cray_product_catalog.constants import (
    CONFIG_MAP_FIELDS,
    PRODUCT_CM_FIELDS,
)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = logging.getLogger(__name__)

ERR_NOT_FOUND = 404
ERR_CONFLICT = 409

CONFIG_MAP = os.environ.get("CONFIG_MAP", "cray-product-catalog").strip()
MAX_RETRIES = 100
MAX_RETRIES_FOR_PROD_CM = 10


def modify_config_map(name, namespace, product, product_version, key=None, max_attempts=MAX_RETRIES):
    """Remove a product version from the catalog ConfigMap.

    If a key is specified, delete the `key` content from a specific section
    of the catalog ConfigMap. If there are no more keys after it has been
    removed, remove the version mapping as well.

    1. Wait for the ConfigMap to be present in the namespace
    2. Patch the ConfigMap
    3. Read back the ConfigMap
    4. Repeat steps 2-3 if ConfigMap does not reflect the changes requested
    """
    k8sclient = ApiClient()
    retries = max_attempts
    retry = Retry(
        total=retries, read=retries, connect=retries, backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504)
    )
    k8sclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
    api_instance = client.CoreV1Api(k8sclient)
    attempt = 0

    while True:

        # Wait a while to check the ConfigMap in case multiple products are
        # attempting to update the same ConfigMap, or the ConfigMap doesn't
        # exist yet
        attempt += 1
        sleepy_time = random.randint(1, 3)
        LOGGER.info("Resting %ss before reading ConfigMap", sleepy_time)
        time.sleep(sleepy_time)

        # Read in the ConfigMap
        try:
            response = api_instance.read_namespaced_config_map(name, namespace)
        except ApiException as err:
            LOGGER.exception("Error calling read_namespaced_config_map")

            # ConfigMap doesn't exist yet
            if err.status == ERR_NOT_FOUND and attempt < max_attempts:
                LOGGER.warning("ConfigMap %s/%s doesn't exist, attempting again.", namespace, name)
                continue
            raise  # unrecoverable

        # Determine if ConfigMap needs to be updated
        config_map_data = response.data or {}  # if no ConfigMap data exists
        if product not in config_map_data:
            break  # product doesn't exist, don't need to remove anything

        # Product exists in ConfigMap
        product_data = yaml.safe_load(config_map_data[product])
        if product_version not in product_data:
            LOGGER.info(
                "Version %s not in ConfigMap", product_version
            )
            break  # product version is gone, we are done

        # Product version exists in ConfigMap
        if key:
            # Key exists, remove it
            if key in product_data[product_version]:
                LOGGER.info(
                    "key=%s in version=%s exists; to be removed",
                    key, product_version
                )
                product_data[product_version].pop(key)
            else:
                # No keys left
                if not product_data[product_version].keys():
                    LOGGER.info(
                        "No keys remain in version=%s; removing version",
                        product_version
                    )
                    product_data.pop(product_version)
                else:
                    break  # key is gone, we are done
        else:
            LOGGER.info(
                "Removing product=%s, version=%s",
                product, product_version
            )
            product_data.pop(product_version)

        # Patch the ConfigMap
        config_map_data[product] = yaml.safe_dump(
            product_data, default_flow_style=False
        )
        LOGGER.info("ConfigMap update attempt=%s", attempt)
        try:
            api_instance.patch_namespaced_config_map(
                name, namespace, client.V1ConfigMap(data=config_map_data)
            )
            LOGGER.info("ConfigMap update attempt %s successful", attempt)
        except ApiException as e:
            if e.status == ERR_CONFLICT:
                # A conflict is raised if the resourceVersion field was unexpectedly
                # incremented, e.g. if another process updated the ConfigMap. This
                # provides concurrency protection.
                LOGGER.warning("Conflict updating ConfigMap")
            else:
                LOGGER.exception("Error calling patch_namespaced_config_map")


def main():
    """ Main function """
    configure_logging()
    # Parameters to identify ConfigMap and product/version to remove
    PRODUCT = os.environ.get("PRODUCT").strip()  # required
    PRODUCT_VERSION = os.environ.get("PRODUCT_VERSION").strip()  # required
    CONFIG_MAP_NS = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()
    PRODUCT_CONFIG_MAP = format_product_cm_name(CONFIG_MAP, PRODUCT)
    KEY = os.environ.get("KEY", "").strip() or None

    load_k8s()

    if KEY:
        if KEY in CONFIG_MAP_FIELDS:
            args = (CONFIG_MAP, CONFIG_MAP_NS, PRODUCT, PRODUCT_VERSION, KEY, MAX_RETRIES)
        elif KEY in PRODUCT_CM_FIELDS:
            args = (PRODUCT_CONFIG_MAP, CONFIG_MAP_NS, PRODUCT, PRODUCT_VERSION, KEY, MAX_RETRIES_FOR_PROD_CM)
        else:
            LOGGER.error(
                "Invalid KEY=%s is input so exiting...",
                KEY
            )
            return
        LOGGER.info(
            "Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
            *args
        )
        modify_config_map(*args)
    else:
        args = (CONFIG_MAP, CONFIG_MAP_NS, PRODUCT, PRODUCT_VERSION, KEY, MAX_RETRIES)
        LOGGER.info(
            "Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
            *args
        )
        modify_config_map(*args)

        args = (PRODUCT_CONFIG_MAP, CONFIG_MAP_NS, PRODUCT, PRODUCT_VERSION, KEY, MAX_RETRIES_FOR_PROD_CM)
        LOGGER.info(
            "Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
            *args
        )
        modify_config_map(*args)


if __name__ == "__main__":
    main()
