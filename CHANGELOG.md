# Change log

vo-siav2 is versioned with [semver](https://semver.org/).
Dependencies are updated to the latest available version during each release, and aren't noted here.

Find changes for the upcoming release in the project's [changelog.d directory](https://github.com/lsst-sqre/vo-siav2/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-0.6.0'></a>

##  0.6.0 (2025-06-05)

### New features

- Add support for dpsubtype parameters

### Other changes

- Upgrade requirements

<a id='changelog-0.5.0'></a>

## 0.5.0 (2025-05-29)

### Changed

- Upgraded dependencies (Includes dax_obscore band bugfix)
- Upgraded Python to 3.13.3

<a id='changelog-0.4.0'></a>

## 0.4.0 (2025-05-02)

### Changed

- Upgraded dependencies
- Upgraded Python to 3.13
- Fixed test to match upgraded dependecies

<a id='changelog-0.3.0'></a>

## 0.3.0 (2025-03-21)

### Changed

- Make query route and handler asynchronous, to allow publishing events in Sentry which is async


<a id='changelog-0.2.1'></a>

## 0.2.1 (2025-03-20)

### New features

- Record username for Sentry events

<a id='changelog-0.2.0'></a>
## 0.2.0  (2025-03-19)

### Changed

- Enable Sentry metrics (events)

<a id='changelog-0.1.7'></a>
## 0.1.7  (2025-03-18)

### Changed

- Capture sia query in sentry tracing
- Update Python and pre-commit dependencies


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
