# MIT License
#
# (C) Copyright 2021-2023 Hewlett Packard Enterprise Development LP
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
Mock data for ProductCatalog and InstalledProductVersion unit tests
"""

from yaml import safe_dump
import datetime

from cray_product_catalog.query import InstalledProductVersion

# Two versions of a product named SAT where:
# - The two versions have have no docker images in common with one another.
# - Both have configurations, but neither have images or recipes
SAT_VERSIONS = {
    '2.0.0': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-sat', 'version': '1.0.0'},
                {'name': 'cray/sat-cfs-install', 'version': '1.4.0'}
            ],
            'repositories': [
                {'name': 'sat-sle-15sp2', 'type': 'group', 'members': ['sat-2.0.0-sle-15sp2']},
                {'name': 'sat-2.0.0-sle-15sp2', 'type': 'hosted'}
            ]
        },
        "configuration": {
           "clone_url": "https://vcs.machine.dev.cray.com/vcs/cray/sat-config-management.git",
           "commit": "5b7e74714c7f789e474ac9dbc2cae5c04d0e8e33",
           "import_branch": "cray/sat/2.0.0",
           "import_date": "2021-07-07T22:13:32.462655Z",
           "ssh_url": "git@vcs.machine.dev.cray.com:cray/sat-config-management.git"
        }
    },
    '2.0.1': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-sat', 'version': '1.0.1'},
                {'name': 'cray/sat-other-image', 'version': '1.4.0'}
            ],
            'repositories': [
                {'name': 'sat-sle-15sp2', 'type': 'group', 'members': ['sat-2.0.1-sle-15sp2']},
                {'name': 'sat-2.0.1-sle-15sp2', 'type': 'hosted'}
            ]
        },
        "configuration": {
            "clone_url": "https://vcs.machine.dev.cray.com/vcs/cray/sat-config-management.git",
            "commit": "e1fa10b6865fb47ced6c1a6cfab2bc28fe149a74",
            "import_branch": "cray/sat/2.0.1",
            "import_date": "2021-10-26T15:23:06.078295Z",
            "ssh_url": "git@vcs.machine.dev.cray.com:cray/sat-config-management.git"
        }
    },
}

# Two versions of a product named COS where:
# - The two versions have one docker image name and version in common
# - The first version has docker and manifests but not helm charts, repositories, configuration, images, or recipes
# - The second version has docker, helm charts, repositories, configuration, images, and recipes, but not manifests
COS_VERSIONS = {
    '2.0.0': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-cos', 'version': '1.0.0'},
                {'name': 'cray/cos-cfs-install', 'version': '1.4.0'}
            ],
            'manifests': [
                'config-data/argo/loftsman/cos/2.0.0/manifests/cos-services.yaml'
            ]
        }
    },
    '2.0.1': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-cos', 'version': '1.0.1'},
                {'name': 'cray/cos-cfs-install', 'version': '1.4.0'}
            ],
            'helm': [
                {'name': 'cos-config', 'version': '0.4.76'},
                {'name': 'cos-sle15sp3-artifacts', 'version': '1.3.23'},
                {'name': 'cray-cps', 'version': '1.8.15'}
            ],
            'repositories': [
                {'name': 'cos-sle-15sp2', 'type': 'group', 'members': ['cos-2.0.1-sle-15sp2']},
                {'name': 'cos-2.0.1-sle-15sp2', 'type': 'hosted'}
            ]
        },
        "configuration": {
            "clone_url": "https://vcs.machine.dev.cray.com/vcs/cray/cos-config-management.git",
            "commit": "f0b17e13fcf7dd3b896196776e4547fdb98f1da7",
            "import_branch": "cray/cos/2.0.1",
            "import_date": "2021-11-24T12:04:25.210495Z",
            "ssh_url": "git@vcs.machine.dev.cray.com:cray/cos-config-management.git"
        },
        "images": {
            "cray-shasta-compute-sles15sp2.x86_64-1.5.66": {
                "id": "e2d58d7e-42b7-434d-b689-31ca3d053c51"
            }
        },
        "recipes": {
            "cray-shasta-compute-sles15sp2.x86_64-1.5.66": {
                "id": "54bc9447-73ba-4b06-a647-e5225451596d"
            }
        }
    },
}

# One version of "cpe" product that has repositories, s3, configuration, images, and recipes
CPE_VERSION = {
    '2.0.0': {
        'component_versions': {
            'repositories': [
                {'name': 'cpe-2.0-sles15-sp4', 'type': 'hosted'},
                {'name': 'cpe-sles15-sp4', 'type': 'group', 'members': ['cpe-2.0-sles15-sp4']}
            ],
            's3': [
                {'bucket': 'boot-images', 'key': 'PE/CPE-base.x86_64-2.0.squashfs'},
                {'bucket': 'boot-images', 'key': 'PE/CPE-amd.x86_64-2.0.squashfs'}
            ]
        },
        "configuration": {
            "clone_url": "https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/cpe-config-management.git",
            "commit": "cbfa9669ed253499406f268022b0081509036906",
            "import_branch": "cray/cpe/2.0.0",
            "import_date": "2023-03-23T12:04:25.210495Z",
            "ssh_url": "git@vcs.machine.dev.cray.com:cray/cpe-config-management.git"
        },
        "images": {
            "cpe-barebones-sles15sp4.x86_64-2.0.0": {
                "id": "cf9c87ea-014c-448a-86ac-3ef3e9d2178f"
            }
        },
        "recipes": {
            "cpe-barebones-sles15sp4.x86_64-2.0.0": {
                "id": "a30ad9b4-a1ce-4734-bbc1-6de2c1e3781a"
            }
        }
    }
}

# One version of "Other Product" that also uses cray/cray-sat:1.0.1
OTHER_PRODUCT_VERSION = {
    '2.0.0': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-sat', 'version': '1.0.1'},
            ],
            'repositories': [
                {'name': 'sat-sle-15sp2', 'type': 'group', 'members': ['sat-2.0.0-sle-15sp2']},
                {'name': 'sat-2.0.0-sle-15sp2', 'type': 'hosted'}
            ]
        }
    }
}

# Multiple versions of products named 'cos', 'sat', and 'cpe' that has valid YAML but not matching schema
# - 'cos' product with invalid component manifests
# - 'sat' product with invalid component docker
# - 'cpe' product with invalid component s3
MOCK_INVALID_PRODUCT_DATA = {
    'cos': {
        '2.1': {
            'component_versions': {
                'manifests': 'should be an array'
            }
        }
    },
    'sat': {
        '2.1': {
            'component_versions': {
                'docker': 'should be an array'
            }
        }
    },
    'cpe': {
        '2.1': {
            'component_versions': {
                's3': 'should be an array'
            }
        }
    }
}

# A mock version of the data returned when querying the Product Catalog ConfigMap
MOCK_PRODUCT_CATALOG_DATA = {
    'sat': safe_dump(SAT_VERSIONS),
    'cos': safe_dump(COS_VERSIONS),
    'cpe': safe_dump(CPE_VERSION),
    'other_product': safe_dump(OTHER_PRODUCT_VERSION)
}

# A mock version of the data returned after loading the ConfigMap data
MOCK_PRODUCTS = \
    [InstalledProductVersion('sat', version, SAT_VERSIONS.get(version)) for version in SAT_VERSIONS.keys()] + \
    [InstalledProductVersion('cos', version, COS_VERSIONS.get(version)) for version in COS_VERSIONS.keys()] + \
    [InstalledProductVersion('cpe', version, CPE_VERSION.get(version)) for version in CPE_VERSION.keys()] + \
    [InstalledProductVersion('other_product', version, OTHER_PRODUCT_VERSION.get(version))
     for version in OTHER_PRODUCT_VERSION.keys()]


class MockInvalidYaml:
    """Mock class created to test test_create_product_catalog_invalid_product_data."""

    def __init__(self):
        """Initialize metadata and data object of ConfigMap data."""
        self.metadata = Name()
        self.data = {
            'sat': '\t',
        }


class Name:
    """
    Class to provide dummy metadata object with name and resource_version
    """
    def __init__(self):
        """Initialize ConfigMap name and resoource_version"""
        self.name = 'cray-product-catalog'
        self.resource_version = 1


# Helper variables for catalog_data_helper: Start
YAML_DATA = """
  active: false
  component_versions:
    docker:
    - name: artifactory.algol60.net/uan-docker/stable/cray-uan-config
      version: 1.11.1
    - name: artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update
      version: 1.3.2
    helm:
    - name: cray-uan-install
      version: 1.11.1
    repositories:
    - members:
      - uan-2.6.0-sle-15sp4
      name: uan-2.6-sle-15sp4
      type: group
    manifests:
    - config-data/argo/loftsman/uan/2.6.0-rc.1/manifests/uan.yaml
  configuration:
    clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/uan-config-management.git
    commit: 6a5f52dfbfe7ea1a5f8ea5079c50995112c17025
    import_branch: cray/uan/2.6.0-rc.1-3-gcc65df9
    import_date: 2023-04-12 14:31:40.364230
    ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/uan-config-management.git
    images:
      cray-application-sles15sp4.x86_64-0.5.19:
        id: 8159f93f-7e18-4875-a8a8-b0fb83c48f07"""

YAML_DATA_MISSING_PROD_CM_DATA = """
  active: false
  configuration:
    clone_url: https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/uan-config-management.git
    commit: 6a5f52dfbfe7ea1a5f8ea5079c50995112c17025
    import_branch: cray/uan/2.6.0-rc.1-3-gcc65df9
    import_date: 2023-04-12 14:31:40.364230
    ssh_url: git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/uan-config-management.git
    images:
      cray-application-sles15sp4.x86_64-0.5.19:
        id: 8159f93f-7e18-4875-a8a8-b0fb83c48f07"""

YAML_DATA_MISSING_MAIN_DATA = """
  component_versions:
    docker:
    - name: artifactory.algol60.net/uan-docker/stable/cray-uan-config
      version: 1.11.1
    - name: artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update
      version: 1.3.2
    helm:
    - name: cray-uan-install
      version: 1.11.1
    repositories:
    - members:
      - uan-2.6.0-sle-15sp4
      name: uan-2.6-sle-15sp4
      type: group
    manifests:
    - config-data/argo/loftsman/uan/2.6.0-rc.1/manifests/uan.yaml"""

MAIN_CM_DATA = {
    'active': False,
    'configuration':
    {
        'clone_url': 'https://vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net/vcs/cray/uan-config-management.git',
        'commit': '6a5f52dfbfe7ea1a5f8ea5079c50995112c17025',
        'import_branch': 'cray/uan/2.6.0-rc.1-3-gcc65df9',
        'import_date': datetime.datetime(2023, 4, 12, 14, 31, 40, 364230),
        'ssh_url': 'git@vcs.cmn.lemondrop.hpc.amslabs.hpecorp.net:cray/uan-config-management.git',
        'images': {'cray-application-sles15sp4.x86_64-0.5.19': {'id': '8159f93f-7e18-4875-a8a8-b0fb83c48f07'}}
    }
}

PROD_CM_DATA = {
    'component_versions':
    {
        'docker': [
            {'name': 'artifactory.algol60.net/uan-docker/stable/cray-uan-config', 'version': '1.11.1'},
            {'name': 'artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update', 'version': '1.3.2'}
        ],
        'helm': [
            {'name': 'cray-uan-install', 'version': '1.11.1'}
        ],
        'repositories': [
            {'members': ['uan-2.6.0-sle-15sp4'], 'name': 'uan-2.6-sle-15sp4', 'type': 'group'}
        ],
        'manifests': ['config-data/argo/loftsman/uan/2.6.0-rc.1/manifests/uan.yaml']
    }
}

# Helper variables for catalog_data_helper: End
