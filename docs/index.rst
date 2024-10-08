.. toctree::
   :maxdepth: 1
   :hidden:

###########
SIA
###########


SIA is an implementation of the IVOA [Simple Image Access v2](https://www.ivoa.net/documents/SIA/20150610/PR-SIA-2.0-20150610.pdf) protocol as a [FastAPI](https://fastapi.tiangolo.com/) web service, designed to be deployed as part of the Rubin Science Platform.

The default configuration is designed to use the [dax_obscore](https://github.com/lsst-dm/dax_obscore) package and interact with a [Butler](https://github.com/lsst/daf_butler) repository to find images that match a certain criteria.
While the application has been designed with consideration to potential future use with other middleware packages & query engines, the current release is targeted to the specific Butler-backed use case for the RSP.
Queries results are streamed as VOTable responses to the user, and in the current release this is the only format supported.
The application expects as configuration the definition of what query_engine to use, and the associated data collections configuration. In the default case of using Remote Butler as the query engine, the application expects at least one data collection (with default=True).


The system architecture & design considerations have been documented in https://github.com/lsst-sqre/sqr-095.

See  [CHANGELOG.md](https://github.com/lsst-sqre/sia/blob/main/CHANGELOG.md) for the change history of sia.


