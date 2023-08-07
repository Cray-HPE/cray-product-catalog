#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2023 Hewlett Packard Enterprise Development LP
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

# kubernetes API response code
ERR_NOT_FOUND = 404
ERR_CONFLICT = 409

# retries
MAX_RETRIES = 100
MAX_RETRIES_FOR_PROD_CM = 10


class ModifyConfigMapUtil:
    """Utility class to manage the config map modification
    """

    def __init__(self):
        self.__main_cm = None
        self.__product_cm = None
        self.__cm_namespace = None
        self.__product_name = None
        self.__product_version = None
        self.__max_retries_for_main_cm = None
        self.__max_retries_for_prod_cm = None
        self.__key = None
        self.__main_cm_fields = None
        self.__product_cm_fields = None

    # property definitions
    @property
    def main_cm(self):
        return self.__main_cm

    @main_cm.setter
    def main_cm(self, __main_cm):
        self.__main_cm = __main_cm

    @property
    def product_cm(self):
        return self.__product_cm

    @product_cm.setter
    def product_cm(self, __product_cm):
        self.__product_cm = __product_cm

    @property
    def cm_namespace(self):
        return self.__cm_namespace

    @cm_namespace.setter
    def cm_namespace(self, __cm_namespace):
        self.__cm_namespace = __cm_namespace

    @property
    def product_name(self):
        return self.__product_name

    @product_name.setter
    def product_name(self, __product_name):
        self.__product_name = __product_name

    @property
    def product_version(self):
        return self.__product_version

    @product_version.setter
    def product_version(self, __product_version):
        self.__product_version = __product_version

    @property
    def max_retries_for_main_cm(self):
        return self.__max_retries_for_main_cm

    @max_retries_for_main_cm.setter
    def max_retries_for_main_cm(self, __max_reties_for_main_cm):
        self.__max_retries_for_main_cm = __max_reties_for_main_cm

    @property
    def max_retries_for_prod_cm(self):
        return self.__max_retries_for_prod_cm

    @max_retries_for_prod_cm.setter
    def max_retries_for_prod_cm(self, __max_reties_for_prod_cm):
        self.__max_retries_for_prod_cm = __max_reties_for_prod_cm

    @property
    def key(self):
        return self.__key

    @key.setter
    def key(self, __key):
        self.__key = __key

    @property
    def main_cm_fields(self):
        return self.__main_cm_fields

    @main_cm_fields.setter
    def main_cm_fields(self, __main_cm_fields):
        self.__main_cm_fields = __main_cm_fields

    @property
    def product_cm_fields(self):
        return self.__product_cm_fields

    @product_cm_fields.setter
    def product_cm_fields(self, __product_cm_fields):
        self.__product_cm_fields = __product_cm_fields

    # private methods
    def __key_belongs_to_main_cm_fields(self):
        return self.__key in self.__main_cm_fields

    def __key_belongs_to_prod_cm_fields(self):
        return self.__key in self.__product_cm_fields

    def __modify_main_cm(self):
        LOGGER.info("Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
                    self.main_cm, self.cm_namespace, self.product_name, self.product_version, self.key)
        modify_config_map(self.__main_cm, self.__cm_namespace, self.__product_name, self.__product_version,
                          self.__key, self.__max_retries_for_main_cm, )

    def __modify_product_cm(self):
        LOGGER.info("Removing from config_map=%s in namespace=%s for %s/%s (key=%s)",
                    self.product_cm, self.cm_namespace, self.product_name, self.product_version, self.key)
        modify_config_map(self.__product_cm, self.__cm_namespace, self.__product_name, self.__product_version,
                          self.__key, self.__max_retries_for_prod_cm, )

    # public method
    def modify(self):
        """
        Method to initiate modification of ConfigMaps.
        Before executing this method make sure to set these properties of the class:
        *    main_cm # name of main ConfigMap
        *    product_cm # name of product specific CofigMap
        *    cm_namespace  # Namespace containing all config map
        *    product_name  # Product name
        *    product_version  # Product version
        *    max_reties_for_main_cm  # Max failure retries for main ConfigMap
        *    max_reties_for_prod_cm  # Max failure retries for product ConfigMap
        *    key  # Key to delete, if you want to execute complete product or a particular version, ignore it
        *    main_cm_fields  # Fields present in main ConfigMap
        *    product_cm_fields  # Fields present in product specific ConfigMap
        """
        if self.__key:
            if self.__key_belongs_to_main_cm_fields():
                self.__modify_main_cm()

            elif self.__key_belongs_to_prod_cm_fields():
                self.__modify_product_cm()

            else:
                LOGGER.warning("key=%s NOT present in Main/Product ConfigMap, exiting", self.key)

            return

        self.__modify_main_cm()
        self.__modify_product_cm()


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
        except ApiException as exc:
            if exc.status == ERR_CONFLICT:
                # A conflict is raised if the resourceVersion field was unexpectedly
                # incremented, e.g. if another process updated the ConfigMap. This
                # provides concurrency protection.
                LOGGER.warning("Conflict updating ConfigMap")
            else:
                LOGGER.exception("Error calling patch_namespaced_config_map")


def main():
    """ Main function """

    # logging configuration
    configure_logging()

    # Parameters to identify ConfigMap and product/version to remove
    PRODUCT = os.environ.get("PRODUCT").strip()  # required
    PRODUCT_VERSION = os.environ.get("PRODUCT_VERSION").strip()  # required
    CONFIG_MAP_NS = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()
    CONFIG_MAP = os.environ.get("CONFIG_MAP", "cray-product-catalog").strip()
    PRODUCT_CONFIG_MAP = format_product_cm_name(CONFIG_MAP, PRODUCT)
    KEY = os.environ.get("KEY", "").strip() or None

    # k8 related configurations
    load_k8s()

    # building the utility class
    modify_config_map_util = ModifyConfigMapUtil()
    modify_config_map_util.main_cm = CONFIG_MAP
    modify_config_map_util.product_cm = PRODUCT_CONFIG_MAP
    modify_config_map_util.cm_namespace = CONFIG_MAP_NS
    modify_config_map_util.product_name = PRODUCT
    modify_config_map_util.product_version = PRODUCT_VERSION
    modify_config_map_util.max_retries_for_main_cm = MAX_RETRIES
    modify_config_map_util.max_retries_for_prod_cm = MAX_RETRIES_FOR_PROD_CM
    modify_config_map_util.key = KEY
    modify_config_map_util.main_cm_fields = CONFIG_MAP_FIELDS
    modify_config_map_util.product_cm_fields = PRODUCT_CM_FIELDS

    # Modifying ConfigMap
    modify_config_map_util.modify()


if __name__ == "__main__":
    main()
