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
Tests for validating ConfigMapDataHandler
"""

import unittest
from unittest.mock import patch, call, Mock
from typing import Dict, List

from kubernetes.config import ConfigException
from kubernetes import client
from kubernetes.client.api_client import ApiClient

from cray_product_catalog.migration.config_map_data_handler import ConfigMapDataHandler
from cray_product_catalog.migration.kube_apis import KubernetesApi
from cray_product_catalog.constants import (
    PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
    PRODUCT_CATALOG_CONFIG_MAP_LABEL
    )
from cray_product_catalog.util.catalog_data_helper import format_product_cm_name
from tests.mock_update_catalog import (
    ApiInstance, ApiException
)
from cray_product_catalog.migration import CONFIG_MAP_TEMP

YAML_DATA = """
  HFP-firmware: |
    22.10.2:
      component_versions:
        docker:
        - name: cray-product-catalog-update
          version: 0.1.3
    23.01.1:
      component_versions:
        docker:
        - name: cray-product-catalog-update
          version: 0.1.3
    23.1.2:
      component_versions:
        repositories:
        - name: HFP-firmware-23.1.2
          type: hosted
        - members:
          - HFP-firmware-23.1.2
          name: HFP-firmware
          type: group
        - members:
          - HFP-firmware-23.1.2
          name: shasta-firmware
          type: group
  analytics: |
    1.4.18:
      component_versions:
        s3:
        - bucket: boot-images
          key: Analytics/Cray-Analytics.x86_64-1.4.18.squashfs
      configuration:
        clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
        commit: 4f1aee2086b58b319d4a9ee167086004fca09e47
        import_branch: cray/analytics/1.4.18
        import_date: 2023-02-28 04:37:34.914586
        ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git
    1.4.20:
      component_versions:
        s3:
        - bucket: boot-images
          key: Analytics/Cray-Analytics.x86_64-1.4.20.squashfs
      configuration:
        clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
        commit: 8424f5f97f12a3403afc57ac55deca0dadc8f3dd
        import_branch: cray/analytics/1.4.20
        import_date: 2023-03-23 16:55:22.295666
        ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git"""

INITIAL_MAIN_CM_DATA = {
    'HFP-firmware': """
        22.10.2:
            component_versions:
                docker:
                    - name: cray-product-catalog-update
                      version: 0.1.3
        23.01.1:
            component_versions:
                docker:
                    - name: cray-product-catalog-update
                      version: 0.1.3""",
    'analytics':"""
        1.4.18:
            component_versions:
                s3:
                - bucket: boot-images
                  key: Analytics/Cray-Analytics.x86_64-1.4.18.squashfs
            configuration:
                clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
                commit: 4f1aee2086b58b319d4a9ee167086004fca09e47
                import_branch: cray/analytics/1.4.18
                import_date: 2023-02-28 04:37:34.914586
                ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git
        1.4.20:
            component_versions:
                s3:
                - bucket: boot-images
                  key: Analytics/Cray-Analytics.x86_64-1.4.20.squashfs
            configuration:
                clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
                commit: 8424f5f97f12a3403afc57ac55deca0dadc8f3dd
                import_branch: cray/analytics/1.4.20
                import_date: 2023-03-23 16:55:22.295666
                ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git"""
    }

MAIN_CM_DATA_EXPECTED = {
    'HFP-firmware': '', 
    'analytics': """1.4.18:
  configuration:
    clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
    commit: 4f1aee2086b58b319d4a9ee167086004fca09e47
    import_branch: cray/analytics/1.4.18
    import_date: 2023-02-28 04:37:34.914586
    ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git
1.4.20:
  configuration:
    clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/analytics-config-management.git
    commit: 8424f5f97f12a3403afc57ac55deca0dadc8f3dd
    import_branch: cray/analytics/1.4.20
    import_date: 2023-03-23 16:55:22.295666
    ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/analytics-config-management.git\n"""
}

PROD_CM_DATA_LIST_EXPECTED = [
{
    'HFP-firmware': """22.10.2:
  component_versions:
    docker:
    - name: cray-product-catalog-update
      version: 0.1.3
23.01.1:
  component_versions:
    docker:
    - name: cray-product-catalog-update
      version: 0.1.3\n"""
},
{
    'analytics':"""1.4.18:
  component_versions:
    s3:
    - bucket: boot-images
      key: Analytics/Cray-Analytics.x86_64-1.4.18.squashfs
1.4.20:
  component_versions:
    s3:
    - bucket: boot-images
      key: Analytics/Cray-Analytics.x86_64-1.4.20.squashfs\n"""
}
]


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
        
        
    def tearDown(self) -> None:
        patch.stopall()
    
    def test_migrate_config_map_data(self):
        """ Validating the migration of data into multiple product ConfigMaps data """
        #self.mock_k8api_read.return_value = INITIAL_MAIN_CM_DATA
        
        main_cm_data: Dict
        prod_cm_data_list: List
        cmdh = ConfigMapDataHandler()
        main_cm_data, prod_cm_data_list = cmdh.migrate_config_map_data(INITIAL_MAIN_CM_DATA)

        self.assertEqual(main_cm_data, MAIN_CM_DATA_EXPECTED)
        self.assertEqual(prod_cm_data_list, PROD_CM_DATA_LIST_EXPECTED)

    def test_create_product_config_map(self):
        """ Validating product config maps are created """
        
        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()
        
        with patch(
                'cray_product_catalog.migration.kube_apis.client.CoreV1Api', return_value=True
        ):               
            with self.assertLogs() as captured:
        
                # call method under test
                cmdh = ConfigMapDataHandler()
                cmdh.create_product_config_maps(PROD_CM_DATA_LIST_EXPECTED)
                
                dummy_prod_cm_names = ['cray-product-catalog-hfp-firmware', 'cray-product-catalog-analytics']

                self.mock_k8api_create.assert_has_calls(calls=[ # Create ConfigMap called twice
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

    def test_create_temp_config_map(self):
        """ Validating product config maps are created """
        
        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()
        
        with patch(
                'cray_product_catalog.migration.kube_apis.client.CoreV1Api', return_value=True
        ):               
            with self.assertLogs(level="DEBUG") as captured:
        
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

    def test_rename_config_map(self):
        """ Validating product config maps are created """
        
        # mock some additional functions
        self.mock_v1_object_Meta_mig = patch('cray_product_catalog.migration.kube_apis.V1ObjectMeta').start()
        self.mock_k8api_delete = patch('cray_product_catalog.migration.config_map_data_handler.KubernetesApi.delete_config_map').start()
        
        with patch(
                'cray_product_catalog.migration.kube_apis.client.CoreV1Api', return_value=True
        ):               
            with self.assertLogs(level="DEBUG") as captured:
        
                # call method under test
                cmdh = ConfigMapDataHandler()
                cmdh.rename_config_map(CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                       PRODUCT_CATALOG_CONFIG_MAP_LABEL)
                
                self.mock_k8api_delete.assert_has_calls(calls=[ # Delete ConfigMap called twice
                      call(PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                      call(CONFIG_MAP_TEMP, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE),
                      call().__bool__(),
                    ]
                )
                
                self.mock_k8api_read.assert_called_once_with(CONFIG_MAP_TEMP,
                                                               PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)
                self.mock_k8api_read.return_value = Mock(data=MAIN_CM_DATA_EXPECTED)
                self.mock_k8api_create.assert_called_once_with(self.mock_k8api_read.return_value.data,
                                                               PRODUCT_CATALOG_CONFIG_MAP_NAME,
                                                               PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                                                               PRODUCT_CATALOG_CONFIG_MAP_LABEL)
                
                self.mock_k8api_delete.assert_called_once_with(CONFIG_MAP_TEMP,
                                                               PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE)

                # Verify the exact log message
                self.assertEqual(
                            captured.records[0].getMessage(), 
                            "Renaming ConfigMap successful")
