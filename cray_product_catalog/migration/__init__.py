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
File defines few constants
"""

import os
from cray_product_catalog.constants import PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR
from re import compile

# ConfigMap name for temporary many config map
CONFIG_MAP_TEMP = "cray-product-catalog-temp"

# namespace for ConfigMaps
PRODUCT_CATALOG_CONFIG_MAP_NAME = os.environ.get("CONFIG_MAP_NAME", "cray-product-catalog").strip()
PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE = os.environ.get("CONFIG_MAP_NAMESPACE", "services").strip()

# config map names
CRAY_DATA_CATALOG_LABEL = PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR

# product ConfigMap pattern
PRODUCT_CONFIG_MAP_PATTERN = compile('^(cray-product-catalog)-([a-z0-9.-]+)$')
RESOURCE_VERSION = 'resource_version'

retry_count = 10
role_name = 'cray-product-catalog'
action = 'update'
