#
# MIT License
#
# (C) Copyright 2021-2024 Hewlett Packard Enterprise Development LP
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

# If you wish to perform a local build, you will need to clone or copy the contents of the
# cms-meta-tools repo to ./cms_meta_tools

NAME ?= cray-product-catalog
APP_NAME ?= $(NAME)-update
CHART_PATH ?= charts

DOCKER_VERSION ?= $(shell head -1 .docker_version)
CHART_VERSION ?= $(shell head -1 .chart_version)

HELM_UNITTEST_IMAGE ?= quintush/helm-unittest:3.3.0-0.2.5

all: runbuildprep lint image chart pymod
chart: chart_setup chart_package chart_test

runbuildprep:
		./cms_meta_tools/scripts/runBuildPrep.sh

lint:
		./cms_meta_tools/scripts/runLint.sh

image:
		docker build --pull ${DOCKER_ARGS} --tag '${APP_NAME}:${DOCKER_VERSION}' .

chart_setup:
		mkdir -p ${CHART_PATH}/.packaged
		printf "\nglobal:\n  appVersion: ${DOCKER_VERSION}" >> ${CHART_PATH}/${NAME}/values.yaml

chart_package:
		helm dep up ${CHART_PATH}/${NAME}
		helm package ${CHART_PATH}/${NAME} -d ${CHART_PATH}/.packaged --app-version ${DOCKER_VERSION} --version ${CHART_VERSION}

chart_test:
		helm lint "${CHART_PATH}/${NAME}"
		docker run --rm -v ${PWD}/${CHART_PATH}:/apps ${HELM_UNITTEST_IMAGE} -3 ${NAME}
