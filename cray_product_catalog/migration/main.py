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
#

import logging

from cray_product_catalog.constants import PRODUCT_CATALOG_CONFIG_MAP_LABEL
from cray_product_catalog.migration.config_map_data_handler import ConfigMapDataHandler
from cray_product_catalog.migration import (
    PRODUCT_CATALOG_CONFIG_MAP_NAME,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
    CONFIG_MAP_TEMP, RESOURCE_VERSION
)
from cray_product_catalog.migration.exit_handler import ExitHandler

LOGGER = logging.getLogger(__name__)


def main():
    """Main function"""
    LOGGER.info("Migrating %s ConfigMap data to multiple product ConfigMaps", PRODUCT_CATALOG_CONFIG_MAP_NAME)
    config_map_obj = ConfigMapDataHandler()
    exit_handler = ExitHandler()
    attempt = 0
    max_attempts = 2

    while (attempt < max_attempts):
        attempt += 1
        migration_failed = False
        init_resource_version = ''
        curr_resource_version = ''
        response = config_map_obj.k8s_obj.read_config_map(
            PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
            )
        if response:
            if not response.metadata.resource_version:
                LOGGER.error("Error reading resourceVersion, exiting migration process...")
            else:
                init_resource_version = response.metadata.resource_version
            if not response.data:
                LOGGER.error("Error reading ConfigMap data, exiting migration process...")
            else:
                config_map_data = response.data
        else:
            LOGGER.info("Error reading ConfigMap, exiting migration process...")
            raise SystemExit(1)

        try:
            main_config_map_data, product_config_map_data_list = config_map_obj.migrate_config_map_data(config_map_data)
        except Exception:
            LOGGER.error("Failed to split ConfigMap Data, exiting migration process...")
            raise SystemExit(1)

        # Create ConfigMaps for each product with `component_versions` data
        if not config_map_obj.create_product_config_maps(product_config_map_data_list):
            LOGGER.info("Calling rollback handler...")
            exit_handler.rollback()
            raise SystemExit(1)
        # Create temporary main ConfigMap with all data except `component_versions` for all products
        if not config_map_obj.create_temp_config_map(main_config_map_data):
            LOGGER.info("Calling rollback handler...")
            exit_handler.rollback()
            raise SystemExit(1)

        LOGGER.info("Verifying resource_version value is same to confirm there is no change in %s",
                    PRODUCT_CATALOG_CONFIG_MAP_NAME)

        response = config_map_obj.k8s_obj.read_config_map(
            PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
            )
        if response:
            if not response.metadata.resource_version:
                LOGGER.error("Error reading resourceVersion, exiting migration process...")
                exit_handler.rollback()
                raise SystemExit(1)
            else:
                curr_resource_version = response.metadata.resource_version

        if curr_resource_version != init_resource_version:
            migration_failed = True
            LOGGER.info("resource_version has changed, so cannot rename %s ConfigMap to %s ConfigMap",
                        CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME)
            LOGGER.info("Re-trying migration process...")
            exit_handler.rollback()
            continue
        else:
            break

    if migration_failed:
        LOGGER.info("ConfigMap %s is modified by other process, exiting migration process...",
                    PRODUCT_CATALOG_CONFIG_MAP_NAME)
        raise SystemExit(1)

    LOGGER.info("Renaming %s ConfigMap name to %s ConfigMap",
                CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME)

    # Creating main ConfigMap `cray-product-catalog` using the data in `cray-product-catalog-temp`
    if config_map_obj.rename_config_map(
        CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME,
        PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, PRODUCT_CATALOG_CONFIG_MAP_LABEL
    ):
        LOGGER.info("Migration successful")
    else:
        LOGGER.info("Renaming %s to %s ConfigMap failed, calling rollback handler...",
                    CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME)
        exit_handler.rollback()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
