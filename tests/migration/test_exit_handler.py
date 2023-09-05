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
File contains unit test classes for validating exit handler cases.
"""

import unittest
from unittest import mock

from cray_product_catalog.migration.exit_handler import _is_product_config_map


class MockKubernetesApi:
    def delete_config_map(self, name, namespace):
        return True



class TestExitHandler(unittest.TestCase):
    """unittest class for Data catalog ConfigMap deletion logic"""

    def setUp(self) -> None:
        self.mock_k8api = mock.patch('cray_product_catalog.migration.exit_handler.KubernetesApi').start()

    def tearDown(self) -> None:
        mock.patch.stopall()

    def test_product_config_map_pattern(self):
        """Test cases for checking all valid patterns of product config map"""
        base_str = "cray-product-catalog"
        valid_patterns = (
            f"{base_str}-cos",
            f"{base_str}-90-lojp",
            f"{base_str}-cos.89-1234jk",
        )

        for valid_pattern in valid_patterns:
            self.assertTrue(_is_product_config_map(valid_pattern))

    def test_product_config_map_invalid_pattern(self):
        """Test cases for checking all invalid patterns of product config map"""
        base_str = "cray-product-catalog"
        invalid_patterns = (
            f"{base_str}",
            f"90-lojp",
            f"cos2.3.45.x86"
        )

        for invalid_pattern in invalid_patterns:
            self.assertFalse(_is_product_config_map(invalid_pattern))



    def test_rollback_failure_from_temp_config_map(self):
        self.mock_k8api.return_value

# mock the API
# test the roll back
