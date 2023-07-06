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
# Unit tests for the cray_product_catalog.util.catalog_data_helper module

import yaml
import datetime
from typing import Dict
from cray_product_catalog.util.catalog_data_helper import split_catalog_data, format_product_cm_name

# Data for testing
yaml_data = """
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

yaml_data_missing_prod_cm_data = """
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

yaml_data_missing_main_data = """
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


def test_split_data_sanity():
    """sanity check of split of yaml into main and prod specific data | +ve test case"""

    # expected data
    main_cm_data_expected = {
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
    prod_cm_data_expected = {
        'component_versions':
            {
                'docker': [
                    {'name': 'artifactory.algol60.net/uan-docker/stable/cray-uan-config', 'version': '1.11.1'},
                    {'name': 'artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update',
                     'version': '1.3.2'}],
                'helm': [
                    {'name': 'cray-uan-install', 'version': '1.11.1'}],
                'repositories': [
                    {'members': ['uan-2.6.0-sle-15sp4'], 'name': 'uan-2.6-sle-15sp4', 'type': 'group'}],
                'manifests': ['config-data/argo/loftsman/uan/2.6.0-rc.1/manifests/uan.yaml']
            }
    }

    # yaml raw to py object
    yaml_object: Dict = yaml.safe_load(yaml_data)

    main_cm_data: Dict
    prod_cm_data: Dict
    main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

    assert main_cm_data == main_cm_data_expected
    assert prod_cm_data == prod_cm_data_expected


def test_split_missing_prod_cm_data():
    """missing prod cm data check"""

    # expected data
    main_cm_data_expected = {
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
    prod_cm_data_expected = {}

    # yaml raw to py object
    yaml_object: Dict = yaml.safe_load(yaml_data_missing_prod_cm_data)

    main_cm_data: Dict
    prod_cm_data: Dict
    main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

    assert main_cm_data == main_cm_data_expected
    assert prod_cm_data == prod_cm_data_expected


def test_split_missing_main_cm_data():
    """missing main cm data check"""

    # expected data
    main_cm_data_expected = {}
    prod_cm_data_expected = {
        'component_versions':
            {
                'docker': [
                    {'name': 'artifactory.algol60.net/uan-docker/stable/cray-uan-config', 'version': '1.11.1'},
                    {'name': 'artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update',
                     'version': '1.3.2'}],
                'helm': [
                    {'name': 'cray-uan-install', 'version': '1.11.1'}],
                'repositories': [
                    {'members': ['uan-2.6.0-sle-15sp4'], 'name': 'uan-2.6-sle-15sp4', 'type': 'group'}],
                'manifests': ['config-data/argo/loftsman/uan/2.6.0-rc.1/manifests/uan.yaml']
            }
    }

    # yaml raw to py object
    yaml_object: Dict = yaml.safe_load(yaml_data_missing_main_data)

    main_cm_data: Dict
    prod_cm_data: Dict
    main_cm_data, prod_cm_data = split_catalog_data(yaml_object)

    assert main_cm_data == main_cm_data_expected
    assert prod_cm_data == prod_cm_data_expected


def test_format_product_cm_name_sanity():
    """Unit test case for product name formatting"""
    product_name = "dummy-valid-1"
    config_map = "cm"
    assert format_product_cm_name(config_map, product_name) == f"{config_map}-{product_name}"


def test_format_product_name_transform():
    """Unit test case for valid product name transformation"""
    product_name = "23dummy_valid-1.x86"
    config_map = "cm"
    assert format_product_cm_name(config_map, product_name) == f"{config_map}-23dummy-valid-1.x86"


def test_format_product_name_invalid_cases():
    """Unit test case for valid product name transformation"""

    # case with special characters
    product_name = "po90-$_invalid"
    config_map = "cm"
    assert format_product_cm_name(config_map, product_name) == ""

    # large name cases
    product_name = "ola-9" * 60
    config_map = "cm"
    assert format_product_cm_name(config_map, product_name) == ""
