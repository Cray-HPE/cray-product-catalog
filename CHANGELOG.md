# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Build helm chart, python module with GH actions (CASMCMS-7698)
- Change default behavior to stop setting "active" key unless `SET_ACTIVE_VERSION`
  variable is given.
- Fix build timestamp used by Docker image tag
- Build docker image with GH actions (CASMCMS-7698)

## [1.4.2] - 2021-12-01

### Changed

- Updated README to reflect versioning change in v1.4.1.

## [1.4.1] - 2021-12-01

### Changed

- Changed GitVersion.yml to ignore previous CSM release branches

## [1.4.0] - 2021-11-29

### Added

- Build docker image with CSM-provided build-scan-sign GH action
- Add GitVersion.yml for automatic git versioning using Gitflow
- Pull python requirements from PyPI, not arti.dev.cray.com to enable GH actions builds

## [1.3.1] - 2021-11-19

### Added

- Added pull request template
- Added Chart lint, test, scan action

### Changed

- Conformed chart to CASM-2670 specifications (CASMCMS-7619)

## [1.2.71] - 2017-11-15

### Added

- Included cray-product-catalog python module
- Introduce new catalog entry delete functionality

### Changed

- Updated repo to Gitflow branching strategy; develop branch now base branch
- Change default reviewers to CMS-core-product-support
