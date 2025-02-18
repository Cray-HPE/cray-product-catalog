#
# MIT License
#
# (C) Copyright 2020-2025 Hewlett Packard Enterprise Development LP
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
FROM artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.18 AS base
WORKDIR /src/
COPY requirements.txt constraints.txt README.md ./

RUN --mount=type=secret,id=netrc,target=/root/.netrc \
       apk add --upgrade --no-cache apk-tools \
    && apk update \
    && apk add --update --no-cache \
        gcc \
        libc-dev \
        py3-pip \
        python3 \
        python3-dev \
    && apk -U upgrade --no-cache \
    && pip3 install --no-cache-dir --upgrade pip wheel -c constraints.txt \
    && pip3 install --ignore-installed --no-cache-dir -r requirements.txt \
    && pip3 list --format freeze \
    && ln -s /usr/bin/catalog_update /catalog_update.py 
#      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Must make catalog_update available as /catalog_update.py
# because it is currently specified this way in the cray-import-config helm
# chart. This is not easy to do with setuptools directly, so just link it
# here.
# https://github.com/Cray-HPE/cray-product-install-charts/blob/master/charts/cray-import-config/templates/job.yaml#L50

WORKDIR /
USER nobody:nobody

ENTRYPOINT [ "/usr/bin/catalog_update" ]
