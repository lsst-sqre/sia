.. toctree::
   :maxdepth: 1
   :hidden:

   usage/index
   admin/index
   api

###########
SIA
###########

SIA is an implementation of the IVOA [Simple Image Access v2](https://www.ivoa.net/documents/SIA/20150610/PR-SIA-2.0-20150610.pdf) protocol as a [FastAPI](https://fastapi.tiangolo.com/) web service, designed to be deployed as part of the Rubin Science Platform.

The default configuration uses the [dax_obscore](https://github.com/lsst-dm/dax_obscore) package and interacts with a [Butler](https://github.com/lsst/daf_butler) repository to find images matching specific criteria.

While the current release supports both remote and direct (local) Butler repositories, our primary focus has been on the Remote Butler, resulting in more mature support for this option.

The application expects as part of the configuration a list of Butler Data Collections, each of which expects a number of attributes which define how to access the repository.

SIA is developed on `GitHub <https://github.com/lsst-sqre/sia>`__.
It is deployed via Phalanx_.

The system architecture & design considerations have been documented in https://github.com/lsst-sqre/sqr-095.

.. grid:: 1

   .. grid-item-card:: Usage
      :link: usage/index
      :link-type: doc

      Learn how to use the SIAv2 Service.

   .. grid-item-card:: Admin
      :link: admin/index
      :link-type: doc

      Learn how to setup the application.

