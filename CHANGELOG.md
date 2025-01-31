# Change log

vo-siav2 is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/vo-siav2/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.1.6'></a>
## 0.1.6  (2025-01-31)

### New features

- Now reads bands information from obscore config
- Fix some of the self-descirption documentation (calibs and remove specify statements)
- Enable Sentry telemetry

<a id='changelog-0.1.5'></a>
## 0.1.5  (2024-12-21)

### Bug fixes

- Update dependencies

<a id='changelog-0.1.4'></a>
## 0.1.4  (2024-12-12)

### Bug fixes

- Fixed missing attribute (type) in VOTable Error resource element

<a id='changelog-0.1.3'></a>
## 0.1.3  (2024-10-29)

### Other changes

- Remove default_instrument from ButlerDataCollection, no longer needed

<a id='changelog-0.1.2'></a>
## 0.1.2  (2024-10-28)

### New features

- Added documentation for the SIA application (/docs)

<a id='changelog-0.1.1'></a>
## 0.1.1  (2024-10-22)

### Other changes

- Change query to be synchronous (Needs to be because dax_obscore siav2_query is sync)
- Update requirements

<a id='changelog-0.1.0'></a>
## 0.1.0 (2024-10-21)

### New features

- Initial release
