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
Mock data for catalog_update unit tests
"""

from kubernetes.client.rest import ApiException
import os
from unittest import mock
from tests.mocks import COS_VERSIONS, Name

# Mocking environment variables before import so that:
# 1. import (create_config_map, update_config_map and main) is successful
# 2. Additionally they will be used in testcase to verify the tests.
mock.patch.dict(
    os.environ, {
        'PRODUCT': 'sat',
        'PRODUCT_VERSION': '1.0.0',
        'YAML_CONTENT_STRING': 'Test data',
        'CONFIG_MAP_NAMESPACE': 'myNamespace'
    }
).start()

UPDATE_DATA = {
    '2.0.0': {
        'component_versions': {
            'docker': [
                {'name': 'cray/cray-cos', 'version': '1.0.0'},
                {'name': 'cray/cos-cfs-install', 'version': '1.4.0'}
            ]
        }
    }
}

ERR_NOT_FOUND = 404


class Response:
    """
    Class to generate response for k8s api call api_instance.read_namespaced_config_map(name, namespace)
    """
    def __init__(self):
        self.data = COS_VERSIONS
        self.metadata = Name()


class ApiException(ApiException):
    """
    Custom Exception to define status
    """
    def __init__(self):
        self.status = ERR_NOT_FOUND


class ApiInstance():
    """
    Class to raise custom exception and ignore function calls
    """
    def __init__(self, raise_exception=False):
        self.raise_exception = raise_exception
        self.count = 0

    def create_namespaced_config_map(self, namespace='a', body='b'):
        """
        Dummy Function to raise exception, if needed
        """
        if self.raise_exception:
            raise ApiException()
        else:
            pass

    def read_namespaced_config_map(self, name, namespace):
        """
        Dummy Function to :
        1. Raise exception
        2. generate and return proper response with data and metadata
        """
        # if this is called for first time return exception, so that product cm is created.
        if self.count == 0:
            self.count += 1
            raise ApiException()
        else:
            return Response()

    def patch_namespaced_config_map(self, name, namespace, body='xxx'):
        """
        Dummy function to handle the call in code, does nothing
        """
        pass
