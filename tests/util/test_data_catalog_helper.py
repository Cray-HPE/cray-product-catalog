import yaml
import datetime
from typing import Dict
from cray_product_catalog.util.catalog_data_helper import split_catalog_data


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
                    {'name': 'artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update', 'version': '1.3.2'}],
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
