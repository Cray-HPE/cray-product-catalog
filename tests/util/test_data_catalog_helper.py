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
Unit tests for the cray_product_catalog.util.catalog_data_helper module
"""

import unittest
from tests.mocks import (
  YAML_DATA, YAML_DATA_MISSING_MAIN_DATA,
  YAML_DATA_MISSING_PROD_CM_DATA,
  MAIN_CM_DATA, PROD_CM_DATA
)
import yaml
from typing import Dict
from cray_product_catalog.util.catalog_data_helper import split_catalog_data, format_product_cm_name


class TestCatalogDataHelper(unittest.TestCase):
    """Tests for catalog_data_helper."""

    def test_split_data_sanity(self):
        """Sanity check of split of YAML into main and product-specific data | +ve test case"""

        # expected data
        main_cm_data_expected = MAIN_CM_DATA
        prod_cm_data_expected = PROD_CM_DATA

        # YAML raw to Python object
        yaml_object: Dict = yaml.safe_load(YAML_DATA)

        main_cm_data: Dict
        prod_cm_data: Dict
        main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

        self.assertEqual(main_cm_data, main_cm_data_expected)
        self.assertEqual(prod_cm_data, prod_cm_data_expected)

    def test_split_missing_prod_cm_data(self):
        """Missing product ConfigMap data check"""

        # expected data
        main_cm_data_expected = MAIN_CM_DATA
        prod_cm_data_expected = {}

        # YAML raw to Python object
        yaml_object: Dict = yaml.safe_load(YAML_DATA_MISSING_PROD_CM_DATA)

        main_cm_data: Dict
        prod_cm_data: Dict
        main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

        self.assertEqual(main_cm_data, main_cm_data_expected)
        self.assertEqual(prod_cm_data, prod_cm_data_expected)

    def test_split_missing_main_cm_data(self):
        """Missing main ConfigMap data check"""

        # expected data
        main_cm_data_expected = {}
        prod_cm_data_expected = PROD_CM_DATA

        # YAML raw to Python object
        yaml_object: Dict = yaml.safe_load(YAML_DATA_MISSING_MAIN_DATA)

        main_cm_data: Dict
        prod_cm_data: Dict
        main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

        self.assertEqual(main_cm_data, main_cm_data_expected)
        self.assertEqual(prod_cm_data, prod_cm_data_expected)

    def test_format_product_cm_name_sanity(self):
        """Unit test case for product name formatting"""
        product_name = "dummy-valid-1"
        config_map = "cm"
        self.assertEqual(format_product_cm_name(config_map, product_name), f"{config_map}-{product_name}")

    def test_format_product_name_transform(self):
        """Unit test case for valid product name transformation"""
        product_name = "23dummy_valid-1.x86"
        config_map = "cm"
        self.assertEqual(format_product_cm_name(config_map, product_name), f"{config_map}-23dummy-valid-1.x86")

    def test_format_product_name_invalid_cases(self):
        """Unit test case for invalid product names"""

        # case with special characters
        product_name = "po90-$_invalid"
        config_map = "cm"
        self.assertEqual(format_product_cm_name(config_map, product_name), "")

        # large name with non-blank ConfigMap case
        product_name = "ola-9" * 60
        config_map = "cm"
        self.assertEqual(format_product_cm_name(config_map, product_name), "")

        # large name with blank ConfigMap case
        product_name = "ola-9" * 60
        config_map = ""
        self.assertEqual(format_product_cm_name(config_map, product_name), "")


if __name__ == '__main__':
    unittest.main()
