# Cray Product Catalog

This repository contains the Docker image definition for the cray-product-catalog
image. This image provides a script that uploads the contents of a yaml file to
a product catalog entry, which serves as a kubernetes config map.

At minimum, the `catalog_update.py` script takes a `PRODUCT` and
`PRODUCT_VERSION` and applies the content of a file denoted by `YAML_CONTENT`
file as follows:

```yaml
{PRODUCT}:
  {PRODUCT_VERSION}:
    {content of yaml file (in YAML_CONTENT)}
```

The product catalog is a software inventory of sorts, and allows for system
users to view a product and its associated versions and version metadata that
have been _installed_ on the system.

The cray-product-catalog image is assumed to be running in the Shasta
Kubernetes cluster by an actor that has permissions to read and update config
maps in the namespace that is configured.

## Getting Started

The main use case for cray-product-catalog is for a product to add install-time
information and metadata to the cray-product-catalog config map located in the
services namespace via a Kubernetes job as part of a Helm chart. The image
could also be used via podman on an NCN, but this has not been tested.

## Example Usage

### Helm Chart

Two seminal examples of using cray-product-catalog are the `cray-import-config`
and `cray-import-kiwi-recipe-image` base charts. Review the values files and
Kubernetes job template to see cray-product-catalog in action.

* [cray-import-config](https://github.com/Cray-HPE/cray-product-install-charts/tree/master/charts/cray-import-config)
* [cray-import-kiwi-recipe-image](https://github.com/Cray-HPE/cray-product-install-charts/tree/master/charts/cray-import-kiwi-recipe-image)

### Podman on NCN

To create an entry in the config map for an "example" product with version
1.2.3, you can use podman on a Kubernetes worker/master node. Be sure to mount
the Kubernetes config file into the running container as well as the
`YAML_CONTENT`.

```bash
ncn-w001:~/ # podman run --rm --name example-cpc --network podman-cni-config \
    -e PRODUCT=example \
    -e PRODUCT_VERSION=1.2.3 \
    -e YAML_CONTENT=/results/example.yaml \
    -e KUBECONFIG=/.kube/admin.conf \
    -v /etc/kubernetes:/.kube:ro \
    -v ${PWD}:/results:ro \
    artifactory.algol60.net/csm-docker/stable/cray-product-catalog-update:1.2.57
Updating config_map=cray-product-catalog in namespace=services for product/version=example/1.2.3
Retrieving content from /results/example.yaml
Resting 3s before reading ConfigMap
Product=example does not exist; will update
ConfigMap update attempt=1
Resting 2s before reading ConfigMap
ConfigMap data updates exist; Exiting.
```

View the results in a nice format:

```bash
ncn-w001:~/ # kubectl get cm -n services cray-product-catalog -o json | jq .data.example | ./yq r -
1.2.3:
  this:
    is: some
    yaml: stuff
```

## Configuration

All configuration options are provided as environment variables.

### Required Environment Variables

* `PRODUCT` = (no default)

> The name of the Cray/Shasta product that is being cataloged.

* `PRODUCT_VERSION` = (no default)

> The SemVer version of the Cray/Shasta product that is being imported, e.g.
  `1.2.3`.

* `YAML_CONTENT`=  (no default)

> The filesystem location of the YAML that will be added to the config map.

### Optional Environment Variables

 * `CONFIG_MAP` = `cray-product-catalog`

 > The name of the config map to add the `YAML_CONTENT` to.

 * `CONFIG_MAP_NAMESPACE` = `services`

 > The Kubernetes namespace of the `CONFIG_MAP`.

## Build Helpers
This repo uses some build helpers from the 
[cms-meta-tools](https://github.com/Cray-HPE/cms-meta-tools) repo. See that repo for more details.

## Local Builds
If you wish to perform a local build, you will first need to clone or copy the contents of the
cms-meta-tools repo to `./cms_meta_tools` in the same directory as the `Makefile`. When building
on github, the cloneCMSMetaTools() function clones the cms-meta-tools repo into that directory.

For a local build, you will also need to manually write the .version, .docker_version (if this repo
builds a docker image), and .chart_version (if this repo builds a helm chart) files. When building
on github, this is done by the setVersionFiles() function.

## Versioning
The version of this repo is generated dynamically at build time by running the version.py script in 
cms-meta-tools. The version is included near the very beginning of the github build output. 

In order to make it easier to go from an artifact back to the source code that produced that artifact,
a text file named gitInfo.txt is added to Docker images built from this repo. For Docker images,
it can be found in the / folder. This file contains the branch from which it was built and the most
recent commits to that branch. 

For helm charts, a few annotation metadata fields are appended which contain similar information.

For RPMs, a changelog entry is added with similar information.

## New Release Branches
When making a new release branch:
    * Be sure to set the `.x` and `.y` files to the desired major and minor version number for this repo for this release. 
    * If an `update_external_versions.conf` file exists in this repo, be sure to update that as well, if needed.

## Contributing

CMS folks, make a branch. Others, make a fork.

## Built With

* Alpine Linux
* Python 3
* Python Requests
* Kubernetes Python Client
* Docker
* Good intentions

## Blamelog

* _0.1.0_ - initial release for Shasta 1.4, addition to CSM product stream - David Laine (david.laine@hpe.com)
* _0.0.1_ - initial implementation - Randy Kleinman (randy.kleinman@hpe.com)

## Copyright and License
This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.

When making any modifications to a file that has a Cray/HPE copyright header, that header
must be updated to include the current year.

When creating any new files in this repo, if they contain source code, they must have
the HPE copyright and license text in their header, unless the file is covered under
someone else's copyright/license (in which case that should be in the header). For this
purpose, source code files include Dockerfiles, Ansible files, RPM spec files, and shell
scripts. It does **not** include Jenkinsfiles, OpenAPI/Swagger specs, or READMEs.

When in doubt, provided the file is not covered under someone else's copyright or license, then
it does not hurt to add ours to the header.
