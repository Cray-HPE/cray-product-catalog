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
Contains a utility function for splitting `cray-product-catalog` data.
"""

import re

from cray_product_catalog.constants import (
    PRODUCT_CM_FIELDS
)


def split_catalog_data(data):
    """Split the passed data into data needed by main and product ConfigMaps."""
    all_unique_keys = set(data.keys())
    comm_keys_bw_cms = all_unique_keys.intersection(PRODUCT_CM_FIELDS)

    # If none of the PRODUCT_CM_FIELDS are available in all_unique_keys, then
    # return empty dict as second return value
    if not comm_keys_bw_cms:
        return {key: data[key] for key in all_unique_keys - PRODUCT_CM_FIELDS}, {}
    return {key: data[key] for key in all_unique_keys - PRODUCT_CM_FIELDS}, \
        {key: data[key] for key in comm_keys_bw_cms}


def format_product_cm_name(config_map, product):
    """Formatting PRODUCT_CONFIG_NAME based on the product name passed and the same is used as key
    under data in the ConfigMap.
    The name of a ConfigMap must be a valid DNS subdomain name. In addition, it must obey the following rules:
    - contain no more than 253 characters
    - contain only lowercase alphanumeric characters, hypens('-'), or periods('.')
    - start with an alphanumeric character
    - end with an alphanumeric character
    The product name, which is a key under the data, must obey the following rule:
    - contain only alphanumeric characters, hyphens ('-'), underscores ('_'), and periods ('.')
    Because the product name can have uppercase characters and underscores ('_'), which are
    prohibited in the ConfigMap name, we convert underscores ('_') to hyphens ('-') and uppercase
    to lowercase.
    """
    pat = re.compile('^([a-z0-9])*[a-z0-9.-]*([a-z0-9])$')
    prod_config_map = config_map + '-' + product.replace('_', '-').lower()

    if len(prod_config_map) > 253:
        return ''
    if not re.fullmatch(pat, prod_config_map):
        return ''
    return prod_config_map
