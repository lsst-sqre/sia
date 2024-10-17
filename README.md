# SIA

SIA is an implementation of the IVOA [Simple Image Access v2](https://www.ivoa.net/documents/SIA/20150610/PR-SIA-2.0-20150610.pdf) protocol as a [FastAPI](https://fastapi.tiangolo.com/) web service, designed to be deployed as part of the Rubin Science Platform.

The default configuration uses the [dax_obscore](https://github.com/lsst-dm/dax_obscore) package and interacts with a [Butler](https://github.com/lsst/daf_butler) repository to find images matching specific criteria.


While the current release supports both remote and direct (local) Butler repositories, our primary focus has been on the Remote Butler, resulting in more mature support for this option.

Query results are streamed to the user as VOTable responses, which is currently the only supported format.

The application expects as part of the configuration a list of Butler Data Collections, each of which expects a number of attributes which define how to access the repository.

The system architecture & design considerations have been documented in https://github.com/lsst-sqre/sqr-095.

See  [CHANGELOG.md](https://github.com/lsst-sqre/sia/blob/main/CHANGELOG.md) for the change history of sia.

