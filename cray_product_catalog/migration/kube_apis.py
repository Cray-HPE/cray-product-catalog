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
Kubernets API
"""

import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.client.api_client import ApiClient
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError
from cray_product_catalog.logging import configure_logging
from cray_product_catalog.util.k8s import load_k8s
from . import retry_count
# retry_count=10

# from kubernetes import configs
# def load_k8s():
#     """ Load Kubernetes configuration """
#     try:
#         config.load_incluster_config()
#     except Exception:
#         config.load_kube_config()


class KubernetesApi:
    """Class for wrapping Kubernetes api"""
    def __init__(self):
        configure_logging()
        self.logger = logging.getLogger(__name__)
        load_k8s()

        retry = Retry(
            total=retry_count, read=retry_count, connect=retry_count, backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504)
        )
        self.kclient = ApiClient()
        self.kclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
        self.api_instance = client.CoreV1Api(self.kclient)

    def create_config_map(self, data, name, namespace, label):
        """Creates Config Map
        :param dict data: Content of configmap
        :param str name: config map name to be created
        :param str namespace: namespace in which configmap has to be created
        :param dict label: label with which configmap has to be created
        :return: bool
        """
        try:
            cm_body = V1ConfigMap(
                metadata=V1ObjectMeta(
                    name=name,
                    labels=label
                ),
                data=data
            )
            self.api_instance.create_namespaced_config_map(
                namespace=namespace, body=cm_body
            )
            return True
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return False
        except ApiException as err:
            self.logger.exception('ApiException- Error:{0}'.format(err))
            return False

    def list_config_map(self, namespace, label):
        """ Reads all the Config Map with certain label in particular namespace
        :param str namespace: Value of namespace from where config map has to be listed
        :param str label: string format of label "type=xyz"
        :return: V1ConfigMapList
                 If there is any error, returns None
        """
        if not all((label, namespace)):
            self.logger.info("Either label or namespace is empty, not reading config map.")
            return None
        try:
            return self.api_instance.list_namespaced_config_map(namespace, label_selector=label)
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return None
        except ApiException as err:
            self.logger.exception('ApiException- Error:{0}'.format(err))
            return None

    def read_config_map(self, name, namespace):
        """Reads config Map based on provided name and namespace
        :param Str name: name of ConfigMap to read
        :param Str namespace: namespace from which Config Map has to be read
        :return: V1ConfigMap
                 Returns None in case of any error
        """
        # Check if both values are not empty
        if not all((name, namespace)):
            self.logger.exception("Either name or namespace is empty, not reading config map.")
            return None
        try:
            return self.api_instance.read_namespaced_config_map(name, namespace)
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return None
        except ApiException as err:
            self.logger.exception('ApiException- Error:{0}'.format(err))
            return None

    def delete_config_map(self, name, namespace):
        """Delete the Config Map
        :param Str name: name of ConfigMap to be deleted
        :param Str namespace: namespace from which Config Map has to be deleted
        :return: bool; If success True else False
        """
        try:
            self.api_instance.delete_namespaced_config_map(name, namespace)
            return True
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return False
        except ApiException as err:
            self.logger.exception('ApiException- Error:{0}'.format(err))
            return False

    def rename_config_map(self, rename_from, rename_to, namespace, label):
        """ Renaming is actually deleting one Config Map and then updating the name of other Config Map and patch it.
        :param str rename_from: Name of Config Map to rename
        :param str rename_to: Name of Config Map to be renamed to
        :param str namespace: namespace in which Config Map has to be updated
        :param dict label: label of config map to be renamed
        :return: bool, If Success True else False
        """

        self.k8s_obj.delete_config_map(rename_to, namespace)
        attempt = 0
        del_failed = False

        while attempt < 10:
            attempt += 1
            response = self.read_config_map(rename_from, namespace)
            if not response:
                self.logger.info("Failed to read ConfigMap %s, retrying..", rename_from)
                continue
            if self.create_config_map(response.data, rename_to, namespace, label):
                if self.delete_config_map(rename_from, namespace):
                    return True
                else:
                    self.logger.info("Failed to delete ConfigMap %s, retrying..", rename_from)
                    del_failed = True
                    break
            else:
                self.logger.info("Failed to create ConfigMap %s, retrying..", rename_to)
                continue
        # Since only delete of backed up ConfigMap failed, retrying only delete operation
        if del_failed:
            while attempt < 10:
                attempt += 1
                if self.delete_config_map(rename_from, namespace):
                    return True
                else:
                    self.logger.info("Failed to delete ConfigMap %s, retrying..", rename_from)
                    continue
        return False

    def update_role_permission(self, name, namespace, action: str, is_grant: bool):
        """Updates specific role for permission
        :param str name: name of role to be updated
        :param str namespace: namespace where role is present
        :param str action: Role to be updated for
        :param bool is_grant: To add or remove, if True will add, if False will remove
        :return: bool; If success True else False
        """
        if action not in ('get', 'create', 'update', 'patch', 'delete', 'proxy'):
            return False
        # body =
        role_api_instance = client.api.rbac_authorization_v1_api.RbacAuthorizationV1Api()
        try:
            role = role_api_instance.read_namespaced_role(name, namespace)
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return False
        except ApiException as err:
            self.logger.exception('ApiException in read_namespaced_role - Error:{0}'.format(err))
            return False

        patch_needed = False
        if is_grant:
            if action not in role.rules[0].verbs:
                role.rules[0].verbs.append(action)
                patch_needed = True
        else:
            if action in role.rules[0].verbs:
                role.rules[0].verbs.remove(action)
                patch_needed = True

        if not patch_needed:
            return True

        try:
            role_api_instance.patch_namespaced_role(name, namespace, role)
            return True
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError - Error: {0}'.format(err))
            return False
        except ApiException as err:
            self.logger.exception('ApiException patch_namespaced_role - Error:{0}'.format(err))
            return False
