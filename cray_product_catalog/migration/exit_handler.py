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
File contains logic to handle exit scenarios:
a. graceful
b. non-graceful
c. Rollback case
"""

import logging
from typing import List
from re import fullmatch


from cray_product_catalog.migration import CONFIG_MAP_TEMP, CRAY_DATA_CATALOG_LABEL, \
    PRODUCT_CONFIG_MAP_PATTERN
from cray_product_catalog.migration import PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
from cray_product_catalog.migration.kube_apis import KubernetesApi

LOGGER = logging.getLogger(__name__)


def _is_product_config_map(config_map_name: str) -> bool:
    """Function to check product config map pattern
    returns True if pattern match found
    """
    if config_map_name is None or config_map_name == "":
        return False
    elif fullmatch(PRODUCT_CONFIG_MAP_PATTERN, config_map_name):
        return True
    else:
        return False


class ExitHandler:
    """Class to handle exit and rollback classes"""

    def __init__(self):
        self.k8api = KubernetesApi()  # kubernetes API object

    @staticmethod
    def graceful_exit() -> None:
        LOGGER.info("Migration not possible, no exception occurred.")

    @staticmethod
    def exception_exit() -> None:
        LOGGER.error("Migration not possible, exception occurred.")

    def __get_all_created_product_config_maps(self) -> List:
        """Get all created product config maps"""
        cm_name = filter(_is_product_config_map,
                         self.k8api.list_config_map_names(
                             label=CRAY_DATA_CATALOG_LABEL,
                             namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)
                         )
        return list(cm_name)

    def rollback(self):
        """Method to handle roll back
        1. Deleting temp config map
        2. Deleting all created product config map
        """
        LOGGER.warning("Initiating rollback")
        product_config_maps = self.__get_all_created_product_config_maps()  # collecting product config map

        LOGGER.info("deleting Product ConfigMaps")  # attempting to delete product config maps
        non_deleted_product_config_maps = []
        for config_map in product_config_maps:
            LOGGER.debug("deleting Product ConfigMap %s", config_map)
            if not self.k8api.delete_config_map(name=config_map, namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE):
                non_deleted_product_config_maps.append(config_map)

        if len(non_deleted_product_config_maps) > 0:  # checking if any product config map is not deleted
            LOGGER.error("Error in deleting ConfigMap/s %s. Delete this/these manually",
                         non_deleted_product_config_maps)
            return

        LOGGER.info("rollback successful")
