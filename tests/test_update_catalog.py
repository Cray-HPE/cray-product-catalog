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


"""Unit tests for cray_product_catalog.catalog_update module"""

import unittest
import os
from unittest import mock
from tests.mock_update_catalog import (
    UPDATE_DATA, ApiInstance, ApiException
)
from cray_product_catalog.catalog_update import (
    create_config_map,
    update_config_map,
    main
)


class TestCatalogUpdate(unittest.TestCase):
    """
    Tests for catalog update
    """
    def setUp(self):
        """Set up mocks."""
        self.mock_v1configmap = mock.patch('cray_product_catalog.catalog_update.V1ConfigMap').start()
        self.mock_load_k8s = mock.patch('cray_product_catalog.catalog_update.load_k8s').start()
        self.mock_ApiClient = mock.patch('cray_product_catalog.catalog_update.ApiClient').start()
        self.mock_client = mock.patch('cray_product_catalog.catalog_update.client').start()

    def test_create_config_map_success_log(self):
        """
        Test for validating create_config_map method logs
        Verify expected log is generated based on the passed arguments
        """
        name = "cos"
        namespace = "product"
        self.mock_v1configmap.metadata = None
        with self.assertLogs() as captured:
            # call method under test
            create_config_map(ApiInstance(raise_exception=False), name, namespace)
            self.assertEqual(len(captured.records), 1)  # check that there is only one log message

            expected_log = "Created product ConfigMap " + namespace + "/" + name
            self.assertEqual(captured.records[0].getMessage(), expected_log)  # Verify the exact log message

    def test_create_config_map_failure_exception(self):
        """
        Verify if expected logs are generated in exception
        """
        name = "cos"
        namespace = "product"
        self.mock_v1configmap.metadata = None

        with self.assertLogs() as captured:
            try:
                # call method under test
                create_config_map(ApiInstance(raise_exception=True), name, namespace)
            except ApiException as err:
                pass
            self.assertEqual(len(captured.records), 1)  # check that there is only one log message
            self.assertEqual(captured.records[0].getMessage(),
                             "Error calling create_namespaced_config_map")  # Verify the exact log message

    def test_update_config_map_max_retries(self):
        """
        Verify update_config_map exits after max retries if Kubernetes API raise exception.
        """
        name = "cos"
        namespace = "product"
        self.mock_v1configmap.metadata = None

        self.mock_read_config_map = mock.patch(
            'cray_product_catalog.catalog_update.client.CoreV1Api.read_namespaced_config_map'
            ).start().side_effect = ApiException()

        with self.assertLogs() as captured:
            with mock.patch(
                    'cray_product_catalog.catalog_update.random.randint', return_value=0
            ):
                # call method under test
                update_config_map(UPDATE_DATA, name, namespace)
                # Verify the exact log message
                self.assertEqual(captured.records[-1].getMessage(),
                                 f"Exceeded number of attempts; Not updating ConfigMap {namespace}/{name}.")

    def test_update_config_map(self):
        """
        Verify `create_config_map` is called if provided `name` is of product and not `CONFIG_MAP` (main cm)
        """
        name = "cos"
        namespace = "product"
        data = UPDATE_DATA

        # mock some additional functions
        self.mock_create_config_map = mock.patch('cray_product_catalog.catalog_update.create_config_map').start()
        self.mock_v1_object_Meta = mock.patch('cray_product_catalog.catalog_update.V1ObjectMeta').start()

        with mock.patch(
                'cray_product_catalog.catalog_update.client.CoreV1Api', return_value=ApiInstance(raise_exception=True)
        ):
            with mock.patch(
                    'cray_product_catalog.catalog_update.random.randint', return_value=0.5
            ):
                # call method under test
                update_config_map(data, name, namespace)

                # verify if create-config_map is called. Couldn't verify it with arguments as one of the arg is object.
                self.mock_create_config_map.assert_called()

    def test_main_valid_product_configmap(self):
        """
        Verify `update_config_map` is called with proper data if provided product information is available
        """
        # Initialise some random data, need not to be exact format
        prod_cm = {"Some random text for product"}
        main_cm = {"Some random text for main"}

        self.mock_update_config_map = mock.patch('cray_product_catalog.catalog_update.update_config_map').start()
        self.mock_create_config_map = mock.patch('cray_product_catalog.catalog_update.create_config_map').start()
        self.mock_v1_object_Meta = mock.patch('cray_product_catalog.catalog_update.V1ObjectMeta').start()

        # mocking function to return custom data
        def mock_split_catalog_data():
            return main_cm, prod_cm

        with mock.patch(
                'cray_product_catalog.catalog_update.split_catalog_data', return_value=mock_split_catalog_data()
        ):
            # Call method under test
            main()
            # sat is from PRODUCT environment variable.
            expected_product_cm = 'cray-product-catalog-sat'
            # myNamespace is from CONFIG_MAP_NAMESPACE environment variable.
            expected_namespace = 'myNamespace'
            self.mock_update_config_map.assert_called_with(prod_cm, expected_product_cm, expected_namespace)

    def test_main_for_empty_product_configmap(self):
        """
        Verify `main` throws exception when PRODUCT_CONFIG_MAP=''
        """
        prod_cm = {"Some random text for product"}
        main_cm = {"Some random text for main"}

        self.mock_update_config_map = mock.patch('cray_product_catalog.catalog_update.update_config_map').start()
        self.mock_create_config_map = mock.patch('cray_product_catalog.catalog_update.create_config_map').start()
        self.mock_v1_object_Meta = mock.patch('cray_product_catalog.catalog_update.V1ObjectMeta').start()

        # mocking function to return custom data
        def mock_split_catalog_data():
            return main_cm, prod_cm

        with mock.patch(
                'cray_product_catalog.catalog_update.split_catalog_data', return_value=mock_split_catalog_data()
        ):
            with mock.patch(
                    'cray_product_catalog.catalog_update.format_product_cm_name', return_value=''
            ):
                with self.assertRaises(SystemExit) as context:
                    # call method under test
                    main()
                    # Verify the log message in exception
                    self.assertTrue(
                        "ERROR Not updating ConfigMaps because the provided product name is invalid: 'sat'"
                        in context.exception
                    )
                    # Verify that update config map is not called in case of exception
                    self.mock_update_config_map.assert_not_called()


if __name__ == '__main__':
    unittest.main()
