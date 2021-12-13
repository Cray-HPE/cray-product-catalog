# Overview

This chart creates an empty config map which product installers can use to
list the versions and various metadata about the installation. Examples of
metadata would be configuration repository information and images and/or recipes
that have been imported.

This chart also installs a cray-product-catalog service account, role, and role
binding for allowing charts/jobs from product helm charts to update the config
map during installation.

## Example ConfigMap Entries

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  creationTimestamp: "2020-07-28T03:26:00Z"
  name: cray-product-catalog
  namespace: services
data:
  cos:
    versions:
      1.4.0:
        configuration:
          clone_url: https://vcs.shasta.io/vcs/cray/cos-config-management.git
          import_branch: cray/cos/1.4.0
          ssh_url: git@vcs.shasta.io:cray/cos-config-management.git
        images:
          cray-cos-sles15sp1-x86_64-compute-1.4.0:
            id: a76f334d-f41d-41d7-a8a8-36af96139027
          cray-cos-sles15sp2-x86_64-compute-1.4.0:
            id: 1ddd0cbd-b976-4721-9626-722d19cf7ada
        recipes:
          cray-cos-sles15sp1-x86_64-compute-1.4.0:
            id: f90a16ed-313a-422d-b5c9-b72648b50519
          cray-cos-sles15sp2-x86_64-compute-1.4.0:
            id: a2cbb305-8a01-4e68-8c4e-0f0911aa10fe
  uan:
    versions:
      2.0.0:
        configuration:
          clone_url: https://vcs.shasta.io/vcs/cray/uan-config-management.git
          import_branch: cray/cos/1.4.0
          ssh_url: git@vcs.shasta.io:cray/uan-config-management.git
        images:
          cray-uan-sles15sp1-x86_64-compute-kernel-2.0.0:
            id: abad11d2-fed3-440e-bf25-0f03a7f1fe8c
        recipes:
          cray-uan-sles15sp1-x86_64-compute-kernel-2.0.0:
            id: 540ce136-1aea-4ef8-8e89-29bf33b574fc
          cray-uan-sles15sp1-x86_64-base-kernel-2.0.0:
            id: 86ad74fa-841a-4bc5-b088-9dff91f1094e      ## example of only a recipe provided, no corresponding image
```
