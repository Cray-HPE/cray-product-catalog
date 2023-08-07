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
File contains unit test classes for validating ConfigMap deletion logic.
Deleting keys/Product or a specific version of a product from ConfigMap
"""
import unittest
from unittest.mock import patch, call

from cray_product_catalog.catalog_delete import ModifyConfigMapUtil


class TestModifyConfigMapUtil(unittest.TestCase):
    """unittest class for Data catalog ConfigMap deletion logic"""

    def setUp(self) -> None:
        self.mock_modify_config_map = patch('cray_product_catalog.catalog_delete.modify_config_map').start()

        self.modify_config_map_util = ModifyConfigMapUtil()
        self.modify_config_map_util.main_cm = "main_cm"
        self.modify_config_map_util.product_cm = "product_cm"
        self.modify_config_map_util.cm_namespace = "cm_namespace"
        self.modify_config_map_util.product_name = "product_name"
        self.modify_config_map_util.product_version = "product_version"
        self.modify_config_map_util.max_retries_for_main_cm = 100
        self.modify_config_map_util.max_retries_for_prod_cm = 10
        self.modify_config_map_util.key = "key"
        self.modify_config_map_util.main_cm_fields = ["main_a", "main_b", "main_c"]
        self.modify_config_map_util.product_cm_fields = ["prod_1", "prod_2", "prod_3"]

    def tearDown(self) -> None:
        patch.stopall()

    def test_object_properties(self):
        """Test cases for checking objects properties are not wrongly arranged"""
        mcmu = ModifyConfigMapUtil()
        mcmu.main_cm = "1"
        mcmu.product_cm = "2"
        mcmu.cm_namespace = "3"
        mcmu.product_name = "4"
        mcmu.product_version = "5"
        mcmu.max_retries_for_main_cm = "6"
        mcmu.max_retries_for_prod_cm = "6.1"
        mcmu.key = "7"
        mcmu.main_cm_fields = ["8", "9", "10"]
        mcmu.product_cm_fields = ["11", "12", "13"]

        self.assertEqual(mcmu.main_cm, "1")
        self.assertEqual(mcmu.product_cm, "2")
        self.assertEqual(mcmu.cm_namespace, "3")
        self.assertEqual(mcmu.product_name, "4")
        self.assertEqual(mcmu.product_version, "5")
        self.assertEqual(mcmu.max_retries_for_main_cm, "6")
        self.assertEqual(mcmu.max_retries_for_prod_cm, "6.1")
        self.assertEqual(mcmu.key, "7")
        self.assertEqual(mcmu.main_cm_fields, ["8", "9", "10"])
        self.assertEqual(mcmu.product_cm_fields, ["11", "12", "13"])

        del mcmu

    def test_delete_from_both_config_map(self):
        """Test cases to assert delete calls into both main and product ConfigMap"""
        self.modify_config_map_util.key = None
        self.modify_config_map_util.modify()

        self.mock_modify_config_map.assert_has_calls(
            calls=[
                # main ConfigMap call
                call(self.modify_config_map_util.main_cm,
                     self.modify_config_map_util.cm_namespace,
                     self.modify_config_map_util.product_name,
                     self.modify_config_map_util.product_version,
                     self.modify_config_map_util.key,
                     self.modify_config_map_util.max_retries_for_main_cm,
                     ),
                # product ConfigMap call
                call(self.modify_config_map_util.product_cm,
                     self.modify_config_map_util.cm_namespace,
                     self.modify_config_map_util.product_name,
                     self.modify_config_map_util.product_version,
                     self.modify_config_map_util.key,
                     self.modify_config_map_util.max_retries_for_prod_cm,
                     )]
        )

    def test_delete_from_main_config_map(self):
        """Test cases to assert delete calls into main ConfigMap"""
        self.modify_config_map_util.key = "main_a"
        self.modify_config_map_util.modify()

        self.mock_modify_config_map.assert_called_once_with(
            self.modify_config_map_util.main_cm,
            self.modify_config_map_util.cm_namespace,
            self.modify_config_map_util.product_name,
            self.modify_config_map_util.product_version,
            self.modify_config_map_util.key,
            self.modify_config_map_util.max_retries_for_main_cm,
        )

    def test_delete_from_product_config_map(self):
        """Test cases to assert delete calls into product ConfigMap"""
        self.modify_config_map_util.key = "prod_3"
        self.modify_config_map_util.modify()

        self.mock_modify_config_map.assert_called_once_with(
            self.modify_config_map_util.product_cm,
            self.modify_config_map_util.cm_namespace,
            self.modify_config_map_util.product_name,
            self.modify_config_map_util.product_version,
            self.modify_config_map_util.key,
            self.modify_config_map_util.max_retries_for_prod_cm,
        )

    def test_invalid_key(self):
        """Test cases to assert invalid key"""
        self.modify_config_map_util.key = "invalid string key"
        self.modify_config_map_util.modify()
        self.mock_modify_config_map.assert_not_called()

        self.modify_config_map_util.key = 909  # non string is invalid as well
        self.modify_config_map_util.modify()
        self.mock_modify_config_map.assert_not_called()
