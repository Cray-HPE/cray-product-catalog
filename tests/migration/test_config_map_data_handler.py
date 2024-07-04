#
# MIT License
#
# (C) Copyright 2023-2024 Hewlett Packard Enterprise Development LP
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
Tests for validating ConfigMapDataHandler
"""

import unittest
from unittest.mock import patch, call, Mock
from typing import Dict, List

from cray_product_catalog.migration.main import main
from cray_product_catalog.migration.config_map_data_handler import ConfigMapDataHandler
from cray_product_catalog.constants import (
    PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
    PRODUCT_CATALOG_CONFIG_MAP_LABEL
)
from cray_product_catalog.migration import CONFIG_MAP_TEMP
from tests.migration.migration_mock import (
    MAIN_CM_DATA_EXPECTED, PROD_CM_DATA_LIST_EXPECTED, INITIAL_MAIN_CM_DATA, MockYaml
)


def mock_split_catalog_data():
    """Mocking function to return custom data"""
    return MAIN_CM_DATA_EXPECTED, PROD_CM_DATA_LIST_EXPECTED


class TestConfigMapDataHandler(unittest.TestCase):
    """ Tests for validating ConfigMapDataHandler """

    def setUp(self) -> None:
        """Set up mocks."""
        self.mock_load_k8s_mig = patch('cray_product_catalog.migration.kube_apis.load_k8s').start()
        self.mock_corev1api_mig = patch('cray_product_catalog.migration.kube_apis.client.CoreV1Api').start()
        self.mock_ApiClient_mig = patch('cray_product_catalog.migration.kube_apis.ApiClient').start()
        self.mock_client_mig = patch('cray_product_catalog.migration.kube_apis.client').start()

        self.mock_k8api_read = patch(
            'cray_product_catalog.migration.config_map_data_handler.KubernetesApi.read_config_map').start()
        self.mock_k8api_create = patch(
            'cray_product_catalog.migration.config_map_data_handler.KubernetesApi.create_config_map').start()
        self.mock_k8api_delete = patch(
            'cray_product_catalog.migration.config_map_data_handler.KubernetesApi.delete_config_map').start()

    def tearDown(self) -> None:
        patch.stopall()

    def test_migrate_config_map_data(self):
        """ Validating the migration of data into multiple product ConfigMaps data """

        main_cm_data: Dict
        prod_cm_data_list: List
        cmdh = ConfigMapDataHandler()
        main_cm_data, prod_cm_data_list = cmdh.migrate_config_map_data(INITIAL_MAIN_CM_DATA)

        self.assertEqual(main_cm_data, MAIN_CM_DATA_EXPECTED)
        self.assertEqual(prod_cm_data_list, PROD_CM_DATA_LIST_EXPECTED)

    def test_create_product_config_maps(self):
        """ Validating product ConfigMaps are created """

        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()

        with self.assertLogs() as captured:
            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.create_product_config_maps(PROD_CM_DATA_LIST_EXPECTED)

            dummy_prod_cm_names = ['cray-product-catalog-hfp-firmware', 'cray-product-catalog-analytics']

            self.mock_k8api_create.assert_has_calls(calls=[  # Create ConfigMap called twice
                call(
                    dummy_prod_cm_names[0], PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                    PROD_CM_DATA_LIST_EXPECTED[0], PRODUCT_CATALOG_CONFIG_MAP_LABEL), call().__bool__(),
                call(
                    dummy_prod_cm_names[1], PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                    PROD_CM_DATA_LIST_EXPECTED[1], PRODUCT_CATALOG_CONFIG_MAP_LABEL), call().__bool__(),
            ]
            )

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Created product ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{dummy_prod_cm_names[0]}")

            self.assertEqual(
                captured.records[1].getMessage(),
                f"Created product ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{dummy_prod_cm_names[1]}")

    def test_create_second_product_config_map_failed(self):
        """ Validating scenario where creation of second product ConfigMap failed """

        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()

        with self.assertLogs() as captured:
            self.mock_k8api_create.side_effect = [True, False]

            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.create_product_config_maps(PROD_CM_DATA_LIST_EXPECTED)

            dummy_prod_cm_names = ['cray-product-catalog-hfp-firmware', 'cray-product-catalog-analytics']

            self.mock_k8api_create.assert_has_calls(calls=[  # Create ConfigMap called twice
                call(
                    dummy_prod_cm_names[0], PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                    PROD_CM_DATA_LIST_EXPECTED[0], PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(
                    dummy_prod_cm_names[1], PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                    PROD_CM_DATA_LIST_EXPECTED[1], PRODUCT_CATALOG_CONFIG_MAP_LABEL),
            ]
            )

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Created product ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{dummy_prod_cm_names[0]}")

            self.assertEqual(
                captured.records[1].getMessage(),
                f"Failed to create product ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{dummy_prod_cm_names[1]}")

    def test_create_first_product_config_map_failed(self):
        """ Validating scenario where creation of first product ConfigMap failed. """

        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()

        with self.assertLogs() as captured:
            self.mock_k8api_create.side_effect = [False, False]

            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.create_product_config_maps(PROD_CM_DATA_LIST_EXPECTED)

            dummy_prod_cm_names = ['cray-product-catalog-hfp-firmware', 'cray-product-catalog-analytics']

            self.mock_k8api_create.assert_called_once_with(
                dummy_prod_cm_names[0], PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                PROD_CM_DATA_LIST_EXPECTED[0], PRODUCT_CATALOG_CONFIG_MAP_LABEL
            )

            # Verify the exact log message
            self.assertEqual(len(captured.records), 1)

            self.assertEqual(
                captured.records[0].getMessage(),
                f"Failed to create product ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{dummy_prod_cm_names[0]}")

    def test_create_temp_config_map(self):
        """ Validating temp main ConfigMap is created """

        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()

        with self.assertLogs(level='DEBUG') as captured:
            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.create_temp_config_map(MAIN_CM_DATA_EXPECTED)

            self.mock_k8api_create.assert_called_once_with(
                CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL
            )

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Created temp ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{CONFIG_MAP_TEMP}")

    def test_create_temp_config_map_failed(self):
        """ Validating temp main ConfigMap creation failed """

        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()
        self.mock_k8api_create.return_value = False

        with self.assertLogs() as captured:
            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.create_temp_config_map(MAIN_CM_DATA_EXPECTED)

            self.mock_k8api_create.assert_called_once_with(
                CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL
            )

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Creating ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE}/{CONFIG_MAP_TEMP} failed")

    def test_rename_config_map(self):
        """ Validating product ConfigMaps are created """

        with self.assertLogs(level="DEBUG") as captured:
            # call method under test
            self.mock_k8api_delete.return_value = True
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)

            cmdh = ConfigMapDataHandler()
            cmdh.rename_config_map(rename_from=CONFIG_MAP_TEMP,
                                   rename_to=PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                   namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                   label=PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            self.mock_k8api_delete.assert_has_calls(calls=[  # Delete ConfigMap called twice
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                     PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                call(CONFIG_MAP_TEMP,
                     PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
            ]
            )

            self.mock_k8api_read.assert_called_once_with(CONFIG_MAP_TEMP,
                                                         PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)

            self.mock_k8api_create.assert_called_once_with(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                           PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                                           MAIN_CM_DATA_EXPECTED,
                                                           PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                "Renaming ConfigMap successful")

    def test_rename_config_map_failed_1(self):
        """ Validating rename ConfigMap failure scenario where:
            deleting cray-product-catalog ConfigMap failed. """

        with self.assertLogs() as captured:
            self.mock_k8api_delete.side_effect = [False, False]
            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.rename_config_map(CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                   PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            self.mock_k8api_delete.assert_called_once_with(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                           PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Failed to delete ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAME}")

    def test_rename_config_map_failed_2(self):
        """ Validating rename ConfigMap failure scenario where:
            creating cray-product-catalog ConfigMap failed. """

        with self.assertLogs(level="DEBUG") as captured:
            self.mock_k8api_create.return_value = False
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)

            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.rename_config_map(CONFIG_MAP_TEMP,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                   PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            self.mock_k8api_delete.assert_called_once_with(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                           PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)
            calls = [  # Delete ConfigMap called twice
                call(
                    PRODUCT_CATALOG_CONFIG_MAP_NAME,
                    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                call(
                    CONFIG_MAP_TEMP,
                    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
            ]
            self.mock_k8api_create.assert_has_calls(calls=[
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),
                call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                     MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL),

            ])

            # Verify the exact log message
            self.assertEqual(
                captured.records[0].getMessage(),
                f"Failed to create ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAME}, retrying..")

    def test_rename_config_map_failed_3(self):
        """ Validating rename ConfigMap failure scenario where:
            first operation of deleting cray-product-catalog-temp ConfigMap failed but later passed. """

        with self.assertLogs(level="DEBUG") as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_k8api_delete.side_effect = [True, False, True]

            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.rename_config_map(CONFIG_MAP_TEMP,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                   PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            self.mock_k8api_delete.assert_has_calls(calls=[   # Delete ConfigMap called twice
                  call(
                      PRODUCT_CATALOG_CONFIG_MAP_NAME,
                      PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                  call(
                      CONFIG_MAP_TEMP,
                      PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                ])
            self.mock_k8api_create.assert_called_once_with(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                           PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                                           MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            # Verify the exact log message
            self.assertEqual(2, len(captured.records))
            self.assertEqual(
                        captured.records[0].getMessage(),
                        f"Failed to delete ConfigMap {CONFIG_MAP_TEMP}, retrying..")
            self.assertEqual(
                        captured.records[1].getMessage(),
                        "Renaming ConfigMap successful")

    def test_rename_config_map_failed_4(self):
        """ Validating rename ConfigMap failure scenario where:
            everytime deleting cray-product-catalog-temp ConfigMap failed. """

        with self.assertLogs(level="DEBUG") as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_k8api_delete.side_effect = [True, False, False, False, False, False, False, False,
                                                  False, False, False, False]

            # call method under test
            cmdh = ConfigMapDataHandler()
            cmdh.rename_config_map(CONFIG_MAP_TEMP,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                   PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                   PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            self.mock_k8api_delete.assert_has_calls(calls=[
                  call(
                      PRODUCT_CATALOG_CONFIG_MAP_NAME,
                      PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                  call(
                      CONFIG_MAP_TEMP,
                      PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                ])
            self.mock_k8api_create.assert_called_once_with(PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                           PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                                           MAIN_CM_DATA_EXPECTED, PRODUCT_CATALOG_CONFIG_MAP_LABEL)

            # Verify the exact log message
            self.assertEqual(12, len(captured.records))
            self.assertEqual(
                        captured.records[-2].getMessage(),
                        f"Failed to delete ConfigMap {CONFIG_MAP_TEMP}, retrying..")
            self.assertEqual(
                        captured.records[-1].getMessage(),
                        f"Failed to delete ConfigMap {CONFIG_MAP_TEMP}, but migration is successful")

    def test_main_for_successful_migration(self):
        """Validating that migration is successful"""
        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertLogs(level="DEBUG") as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = True
            self.mock_create_temp_cm.return_value = True
            self.mock_rename_cm.return_value = True

            # Call method under test
            main()

            self.assertEqual(
                        captured.records[-1].getMessage(),
                        "Migration successful")

    def test_main_failed_1(self):
        """Validating that migration failed as renaming failed"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = True
            self.mock_create_temp_cm.return_value = True
            self.mock_rename_cm.return_value = False

            # Call method under test
            main()

            self.assertTrue(
              "Renaming cray-product-catalog-temp to cray-product-catalog ConfigMap failed, "
              "calling rollback handler..." in captured.exception
            )

            self.assertTrue(
              "Rollback successful" in captured.exception
            )

    def test_main_failed_2(self):
        """Validating that migration failed as create temp cm failed"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = True
            self.mock_create_temp_cm.return_value = False

            # Call method under test
            main()

            self.assertTrue(
              "Rollback successful" in captured.exception
            )

            self.mock_rename_cm.assert_not_called()

    def test_main_failed_3(self):
        """Validating that migration failed as create product ConfigMaps failed"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = False

            # Call method under test
            main()

            self.assertTrue(
              "Rollback successful" in captured.exception
            )

            self.mock_create_temp_cm.assert_not_called()
            self.mock_rename_cm.assert_not_called()

    def test_main_failed_4(self):
        """Validating that migration failed as migrate_config_map failed with exception"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
            self.mock_migrate_config_map.return_value = Exception()

            # Call method under test
            main()

            self.assertTrue(
              "Failed to split ConfigMap Data, exiting migration process..." in captured.exception
            )

            self.mock_create_prod_cms.assert_not_called()
            self.mock_create_temp_cm.assert_not_called()
            self.mock_rename_cm.assert_not_called()

    def test_main_failed_6(self):
        """Validating that migration failed as read_config_map returned empty response / data."""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.return_value = Mock(data="")

            # Call method under test
            main()

            self.assertTrue(
              "Error reading ConfigMap, exiting migration process..." in captured.exception
            )

            self.mock_migrate_config_map.assert_not_called()
            self.mock_create_prod_cms.assert_not_called()
            self.mock_create_temp_cm.assert_not_called()
            self.mock_rename_cm.assert_not_called()

    def test_main_failed_7(self):
        """Validating that migration failed as initial and final resource version is different"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()
        self.mock_is_migrated = patch(
            'cray_product_catalog.migration.main.is_migrated'
        ).start()

        with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.side_effect = [MockYaml(1),
                                                MockYaml(2),
                                                MockYaml(1),
                                                MockYaml(2)]
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = True
            self.mock_create_temp_cm.return_value = True
            self.mock_is_migrated.return_value = False

            # Call method under test
            main()

            self.assertTrue(
              "Re-trying migration process..." in captured.exception
            )

            self.assertTrue(
              "Rollback successful" in captured.exception
            )

            self.assertTrue(
                f"ConfigMap {PRODUCT_CATALOG_CONFIG_MAP_NAME} is modified, exiting migration process..."
            )
            self.mock_rename_cm.assert_not_called()

    def test_main_failed_8(self):
        """Validating that migration is successful in second attempt as initial and final resource
           version is different in first attempt"""

        self.mock_migrate_config_map = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.migrate_config_map_data'
        ).start()
        self.mock_create_prod_cms = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_product_config_maps'
        ).start()
        self.mock_create_temp_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.create_temp_config_map'
        ).start()
        self.mock_rename_cm = patch(
            'cray_product_catalog.migration.config_map_data_handler.ConfigMapDataHandler.rename_config_map'
        ).start()
        self.mock_is_migrated = patch(
            'cray_product_catalog.migration.main.is_migrated'
        ).start()

        with self.assertLogs(level="DEBUG") as captured:
            # with self.assertRaises(SystemExit) as captured:
            self.mock_k8api_read.side_effect = [MockYaml(1),
                                                MockYaml(2),
                                                MockYaml(1),
                                                MockYaml(1)]
            self.mock_migrate_config_map.return_value = mock_split_catalog_data()
            self.mock_create_prod_cms.return_value = True
            self.mock_create_temp_cm.return_value = True
            self.mock_rename_cm.return_value = True
            self.mock_is_migrated.return_value = False

            # Call method under test
            main()
            # Verify the exact log message
            self.assertEqual(10, len(captured.records))
            self.assertEqual(
                captured.records[3].getMessage(),
                "Re-trying migration process..."
            )
            self.assertEqual(
                captured.records[6].getMessage(),
                "Rollback successful"
            )

            self.assertEqual(
                captured.records[-1].getMessage(),
                "Migration successful"
            )
