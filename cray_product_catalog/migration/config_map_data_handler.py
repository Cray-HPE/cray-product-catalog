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

"""
This script splits the data in ConfigMap `cray-product-catalog` into multiple smaller
ConfigMaps with each product's `component_versions` data in its own Product ConfigMap
"""

import logging
import yaml

from kubernetes.client.rest import ApiException

from cray_product_catalog.logging import configure_logging
from cray_product_catalog.util.catalog_data_helper import split_catalog_data, format_product_cm_name
from cray_product_catalog.migration.kube_apis import KubernetesApi
from cray_product_catalog.constants import (
        PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
        PRODUCT_CATALOG_CONFIG_MAP_LABEL
    )
from cray_product_catalog.migration import CONFIG_MAP_TEMP

LOGGER = logging.getLogger(__name__)

class ConfigMapDataHandler:
    """ Class to migrate ConfigMap data to multiple ConfigMaps """

    def __init__(self) -> None:
        self.k8s_obj = KubernetesApi()
        self.config_map_data_replica = {}
        configure_logging()

    def create_product_config_maps(self, product_config_map_data_list):
        """Create new product ConfigMap for each product in product_config_map_data_list

        Args:
            product_config_map_data_list (list): list of data to be stored in each product ConfigMap
        """
        for product_data in product_config_map_data_list:
            product_name = list(product_data.keys())[0]
            LOGGER.debug("Creating ConfigMap for product %s", product_name)
            prod_cm_name = format_product_cm_name(PRODUCT_CATALOG_CONFIG_MAP_NAME, product_name)

            if self.k8s_obj.create_config_map(prod_cm_name, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, product_data,
                                        PRODUCT_CATALOG_CONFIG_MAP_LABEL):
                LOGGER.debug("Created product ConfigMap %s/%s", PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, prod_cm_name)
                return True
            LOGGER.info("Failed to create product ConfigMap %s/%s", PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, prod_cm_name)
            return False

    def create_temp_config_map(self, config_map_data):
        """Create temporary main ConfigMap `cray-product-catalog-temp`

        Args:
            config_map_data (dict): Data to be stored in the ConfigMap `cray-product-catalog-temp`
        """

        if self.k8s_obj.create_config_map(CONFIG_MAP_TEMP,
                                            PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                            config_map_data, PRODUCT_CATALOG_CONFIG_MAP_LABEL):
            LOGGER.debug("Created temp ConfigMap %s/%s",
                            PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, CONFIG_MAP_TEMP)
            return True
        LOGGER.info("Creating ConfigMap %s/%s failed", PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, CONFIG_MAP_TEMP)
        return False

    def read_config_map_data(self):
        """Read main ConfigMap data

        Returns:
            {Dictionary}: data reperesenting the ConfigMap output

        """

        response = self.k8s_obj.read_config_map(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)
        if response:
            return response.data
        return None

    def migrate_config_map_data(self, config_map_data):
        """Migrate cray-product-catalog ConfigMap data to multiple product ConfigMaps with
        `component_versions` data for each product

        Returns:
            {Dictionary, List}: Main ConfigMap Data, list of product ConfigMap data
        """

        LOGGER.info(
            "Migrating data in ConfigMap=%s in namespace=%s to multiple ConfigMaps",
            PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
        )
        # Backed up ConfigMap Data
        self.config_map_data_replica = config_map_data
        # Get list of products
        products_list = list(config_map_data.keys())
        product_config_map_data_list = []
        for product in products_list:
            product_data = yaml.safe_load(config_map_data[product])
            # Get list of versions associated with product
            product_versions_list = list(product_data.keys())
            product_versions_data = {}
            main_versions_data = {}
            for version_data in product_versions_list:
                LOGGER.debug("Splitting cray-product-catalog data for product %s", product)
                main_cm_data, prod_cm_data = split_catalog_data(product_data[version_data])
                # prod_cm_data is not an empty dictionary
                if prod_cm_data:
                    product_config_map_data = {}
                    product_versions_data[version_data] = prod_cm_data
                # main_cm_data is not an empty dictionary
                if main_cm_data:
                    main_versions_data[version_data] = main_cm_data
            # If `component_versions` data exists for a product, create new product config map
            if product_versions_data:
                product_config_map_data[product] = yaml.safe_dump( product_versions_data, default_flow_style=False)
                #create_product_config_map(k8s_obj, product, product_config_map_data)
                product_config_map_data_list.append(product_config_map_data)
            # Data with key other than `component_versions` should be updated to config_map_data,
            # so that new main ConfigMap will not have data with key `component_versions`
            if main_versions_data:
                config_map_data[product] = yaml.safe_dump( main_versions_data, default_flow_style=False)
            else:
                config_map_data[product] = ""
        return config_map_data, product_config_map_data_list
