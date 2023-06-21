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
# Contains a utility functions for parsing catalog data.

import re

from cray_product_catalog.constants import (
    PRODUCT_CM_FIELDS
)

def split_catalog_data(data):
    """Split the passed data into data needed by main and product config map"""
    all_unique_keys = set(data.keys())
    comm_keys_bw_cms = all_unique_keys.intersection(PRODUCT_CM_FIELDS)
    
    #If fields in PRODUCT_CM_FIELDS is not available in all unique keys return empty dict as second return value
    if not comm_keys_bw_cms:
        return {key:data[key] for key in all_unique_keys - PRODUCT_CM_FIELDS}, {}
    else:
        return {key:data[key] for key in all_unique_keys - PRODUCT_CM_FIELDS}, \
        {key:data[key] for key in comm_keys_bw_cms}   
        

def format_product_cm_name(config_map, product):
    """Formatting PRODUCT_CONFIG_NAME based on the product name passed and the same is used as key under data in cm.
    Below are the rules for configmap name. The name of a ConfigMap must be a valid DNS subdomain name.
    - contain no more than 253 characters
    - contain only lowercase alphanumeric characters, '-' or '.'
    - start with an alphanumeric character
    - end with an alphanumeric character
    Rules for Product name which is a key under the data
    - must be alphanumeric characters, -, _ or .
    Since product name can have upper case and '_' which are prohibited in config name,
    we are converting '_' to '-' and upper case to lower case
    """
    pat = re.compile('^([a-z0-9])*[a-z0-9.-]*([a-z0-9])$')
    prod_config_map = config_map + '-' + product.replace('_', '-').lower()

    if len(prod_config_map) > 253:
        return ''
    elif not re.fullmatch(pat, prod_config_map):
        return ''
    else:
        return prod_config_map
