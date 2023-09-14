#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2020-2023 Hewlett Packard Enterprise Development LP
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
#

"""
This script takes a PRODUCT and PRODUCT_VERSION and applies the content of
a YAML file to a Kubernetes ConfigMap as follows:

{PRODUCT}:
  {PRODUCT_VERSION}:
    {content of yaml file}

Since updates to a ConfigMap are not atomic, this script will continue to
attempt to update the ConfigMap until it has been patched successfully.
"""

import logging
import os
import random
import time

import urllib3
import yaml
from jsonschema.exceptions import ValidationError
from kubernetes.client.api_client import ApiClient
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.rest import ApiException
from kubernetes import client
from urllib3.util.retry import Retry

from cray_product_catalog.logging import configure_logging
from cray_product_catalog.schema.validate import validate
from cray_product_catalog.util.k8s import load_k8s
from cray_product_catalog.util.merge_dict import merge_dict
from cray_product_catalog.util.catalog_data_helper import split_catalog_data, format_product_cm_name
from cray_product_catalog.constants import PRODUCT_CATALOG_CONFIG_MAP_LABEL


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Parameters to identify ConfigMap and content in it to update
PRODUCT = os.environ.get("PRODUCT").strip()  # required
PRODUCT_VERSION = os.environ.get("PRODUCT_VERSION").strip()  # required
MAIN_CONFIG_MAP = os.environ.get("CONFIG_MAP", "cray-product-catalog").strip()
CONFIG_MAP_NAMESPACE = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()
# One of (YAML_CONTENT_FILE, YAML_CONTENT_STRING) required. For backwards compatibility, YAML_CONTENT
# may also be given in place of YAML_CONTENT_FILE.
YAML_CONTENT_FILE = (os.environ.get("YAML_CONTENT_FILE") or os.environ.get("YAML_CONTENT", "")).strip()
YAML_CONTENT_STRING = os.environ.get("YAML_CONTENT_STRING", "").strip()   # see above
SET_ACTIVE_VERSION = bool(os.environ.get("SET_ACTIVE_VERSION"))
REMOVE_ACTIVE_FIELD = bool(os.environ.get("REMOVE_ACTIVE_FIELD"))
VALIDATE_SCHEMA = bool(os.environ.get("VALIDATE_SCHEMA"))
UPDATE_OVERWRITE = bool(os.environ.get("UPDATE_OVERWRITE"))

ERR_NOT_FOUND = 404
ERR_CONFLICT = 409

LOGGER = logging.getLogger(__name__)


def validate_schema(data):
    """ Validate data against the schema. """
    LOGGER.debug(
        "Validating data against schema because VALIDATE_SCHEMA was set"
    )
    try:
        validate(data)
    except ValidationError as err:
        LOGGER.error("Data failed schema validation: %s", err)
        raise SystemExit(1) from err


def read_yaml_content(yaml_file):
    """ Read and return the raw content contained in the `yaml_file`. """
    LOGGER.debug("Retrieving content from %s", yaml_file)
    with open(yaml_file) as yfile:
        return yaml.safe_load(yfile)


def read_yaml_content_string(yaml_string):
    """ Read and return the raw content contained in the `yaml_string` string. """
    LOGGER.debug("Retrieving raw content specified as a string")
    return yaml.safe_load(yaml_string)


def set_active_version(product_data):
    """ Modify product_data in place to set the 'active' key for PRODUCT_VERSION.

    This also sets the 'active' key for other versions in product_data to False."""
    # Set the current version to 'active'
    for version in product_data:
        product_data[version]['active'] = version == PRODUCT_VERSION


def current_version_is_active(product_data):
    """ Return True if PRODUCT_VERSION is active and no other version of the product is active."""
    current_version = product_data[PRODUCT_VERSION]
    other_versions = [version for version in product_data if version != PRODUCT_VERSION]

    return current_version.get('active') and not any(
               product_data[version].get('active') for version in other_versions
           )


def remove_active_field(product_data):
    """ Remove the 'active' field for a given product. """
    LOGGER.info("Deleting 'active' field for all versions of %s", PRODUCT)
    for version in product_data:
        if "active" in product_data[version]:
            del product_data[version]["active"]


def active_field_exists(product_data):
    """ Return True if any version of the given product is using the 'active' field."""
    return any("active" in product_data[version] for version in product_data)


def create_config_map(api_instance, name, namespace):
    """Create new product ConfigMap."""
    try:
        new_cm = V1ConfigMap()
        new_cm.metadata = V1ObjectMeta(name=name, labels=PRODUCT_CATALOG_CONFIG_MAP_LABEL)
        api_instance.create_namespaced_config_map(
            namespace=namespace, body=new_cm
        )
        LOGGER.info("Created product ConfigMap %s/%s", namespace, name)
        return True
    except ApiException:
        LOGGER.error("Error calling create_namespaced_config_map")
        return False


def update_config_map(data: dict, name, namespace):
    """
    Get the ConfigMap `data` to be added.

    1. Wait for the ConfigMap to be present in the namespace
    2. Read the ConfigMap
    3. Patch the ConfigMap
    4. Read back the ConfigMap
    5. Repeat steps 2-4 if ConfigMap does not include the changes requested,
       or if step 3 failed due to a conflict.
    """
    k8sclient = ApiClient()
    retries = 100
    retry = Retry(
        total=retries, read=retries, connect=retries, backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504)
    )
    k8sclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
    api_instance = client.CoreV1Api(k8sclient)
    attempt = 0

    while attempt < retries:

        # Wait a while to check the ConfigMap in case multiple products are
        # attempting to update the same ConfigMap, or the ConfigMap doesn't
        # exist yet
        attempt += 1
        sleepy_time = random.randint(1, 3)
        LOGGER.debug("Resting %ss before reading ConfigMap", sleepy_time)
        time.sleep(sleepy_time)

        # Read in the ConfigMap
        try:
            response = api_instance.read_namespaced_config_map(name, namespace)
        except ApiException as err:
            LOGGER.exception("Error calling read_namespaced_config_map")

            # ConfigMap doesn't exist yet
            if err.status != ERR_NOT_FOUND:
                raise   # unrecoverable
            if name == MAIN_CONFIG_MAP:
                # If main ConfigMap is not found wait until it is available
                LOGGER.warning("ConfigMap %s/%s doesn't exist, attempting again", namespace, name)
            else:
                # If product ConfigMap is not available then create
                LOGGER.info("Product ConfigMap %s/%s doesn't exist, attempting to create", namespace, name)
                if not create_config_map(api_instance, name, namespace):
                    raise   # unrecoverable
            continue

        # Determine if ConfigMap needs to be updated
        config_map_data = response.data or {}  # if no ConfigMap data exists
        if PRODUCT not in config_map_data:
            LOGGER.info("Product=%s does not exist; will update", PRODUCT)
            config_map_data[PRODUCT] = product_data = {PRODUCT_VERSION: {}}
        # Product exists in ConfigMap
        else:
            product_data = yaml.safe_load(config_map_data[PRODUCT])
            if PRODUCT_VERSION not in product_data:
                LOGGER.info(
                    "Version=%s does not exist; will update", PRODUCT_VERSION
                )
                product_data[PRODUCT_VERSION] = {}
            # Key with same version exists in ConfigMap
            else:
                # Data to insert matches data found in ConfigMap.
                merged_product_data = None
                if UPDATE_OVERWRITE:
                    product_data[PRODUCT_VERSION] = data
                else:
                    merged_product_data = merge_dict(
                        data, product_data[PRODUCT_VERSION]) == product_data[PRODUCT_VERSION]

                if merged_product_data or UPDATE_OVERWRITE:
                    if SET_ACTIVE_VERSION and REMOVE_ACTIVE_FIELD:
                        # This should not happen (see main method).
                        raise SystemExit(1)
                    if SET_ACTIVE_VERSION:
                        if current_version_is_active(product_data):
                            LOGGER.debug("ConfigMap data updates exist and desired version is active; Exiting")
                            break
                    elif REMOVE_ACTIVE_FIELD:
                        if not active_field_exists(product_data):
                            LOGGER.debug("ConfigMap data updates exist and 'active' field has been cleared; Exiting")
                            break
                    else:
                        LOGGER.debug("ConfigMap data updates exist; Exiting")
                        break

        # Patch the ConfigMap if needed
        product_data[PRODUCT_VERSION] = merge_dict(data, product_data[PRODUCT_VERSION])
        if SET_ACTIVE_VERSION:
            set_active_version(product_data)
        if REMOVE_ACTIVE_FIELD:
            remove_active_field(product_data)
        config_map_data[PRODUCT] = yaml.safe_dump(
            product_data, default_flow_style=False
        )
        LOGGER.debug("ConfigMap update attempt=%s", attempt)
        try:
            new_config_map = V1ConfigMap(data=config_map_data)
            new_config_map.metadata = V1ObjectMeta(
                name=name, resource_version=response.metadata.resource_version
            )
            api_instance.patch_namespaced_config_map(
                name, namespace, body=new_config_map
            )
        except ApiException as err:
            if err.status == ERR_CONFLICT:
                # A conflict is raised if the resourceVersion field was unexpectedly
                # incremented, e.g. if another process updated the ConfigMap. This
                # provides concurrency protection.
                LOGGER.warning("Conflict updating ConfigMap")
            else:
                LOGGER.exception("Error calling replace_namespaced_config_map")

    if attempt == retries:
        LOGGER.error("Exceeded number of attempts; Not updating ConfigMap %s/%s.", namespace, name)


def main():
    """ Main function """
    configure_logging()
    LOGGER.info(
        "Updating ConfigMap=%s in namespace=%s for product/version=%s/%s",
        MAIN_CONFIG_MAP, CONFIG_MAP_NAMESPACE, PRODUCT, PRODUCT_VERSION
    )

    if SET_ACTIVE_VERSION and REMOVE_ACTIVE_FIELD:
        LOGGER.error(
            "SET_ACTIVE_VERSION and REMOVE_ACTIVE_FIELD cannot both be set"
        )
        raise SystemExit(1)

    if SET_ACTIVE_VERSION:
        LOGGER.info(
            "Setting %s:%s to active because SET_ACTIVE_VERSION was set",
            PRODUCT, PRODUCT_VERSION
        )

    elif REMOVE_ACTIVE_FIELD:
        LOGGER.info(
            "Product %s will have 'active' value cleared because REMOVE_ACTIVE_FIELD was set", PRODUCT
        )

    load_k8s()
    if YAML_CONTENT_FILE:
        data = read_yaml_content(YAML_CONTENT_FILE)
    elif YAML_CONTENT_STRING:
        data = read_yaml_content_string(YAML_CONTENT_STRING)
    else:
        LOGGER.error(
            "One of the environment variables YAML_CONTENT_FILE or "
            "YAML_CONTENT_STRING must be specified"
        )
        raise SystemExit(1)
    if VALIDATE_SCHEMA:
        validate_schema(data)

    product_config_map = format_product_cm_name(MAIN_CONFIG_MAP, PRODUCT)

    LOGGER.debug("Splitting cray-product-catalog data")
    main_cm_data, prod_cm_data = split_catalog_data(data)

    if prod_cm_data and product_config_map == '':
        LOGGER.error("Not updating ConfigMaps because the provided product name is invalid: '%s'", PRODUCT)
        raise SystemExit(1)

    update_config_map(main_cm_data, MAIN_CONFIG_MAP, CONFIG_MAP_NAMESPACE)

    # If product_config_map is not an empty string and prod_cm_data is not an empty dict
    if prod_cm_data:
        update_config_map(prod_cm_data, product_config_map, CONFIG_MAP_NAMESPACE)


if __name__ == "__main__":
    main()
