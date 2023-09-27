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
Mock data for ConfigMapDataHandler
"""

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
    'analytics': """
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
        'analytics': """1.4.18:
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


class MockYaml:
    """Mock class created to test test_create_product_catalog_invalid_product_data."""

    def __init__(self, resource_version):
        """Initialize metadata and data object of ConfigMap data."""
        self.metadata = MetaData(resource_version)
        self.data = {
            'sat': '\t',
        }


class MetaData:
    """
    Class to provide dummy metadata object with name and resource_version
    """
    def __init__(self, resource_version):
        """Initialize ConfigMap name and resoource_version"""
        self.name = 'cray-product-catalog'
        self.resource_version = resource_version
