.. toctree::
   :maxdepth: 1
   :hidden:

   usage/index
   admin/index
   api

###########
SIA
###########
SIA is an implementation of the IVOA `Simple Image Access v2`_ protocol as a `FastAPI`_ web service, designed to be deployed as part of the Rubin Science Platform through `Phalanx`_.

The default configuration uses the `dax_obscore`_ package and interacts with a `Butler`_ repository to find images matching specific criteria.

While the current release supports both remote and direct (local) Butler repositories, our primary focus has been on the Remote Butler use-case, resulting in more mature support for this option.

The application expects as part of the configuration a list of Butler Data Collections, each of which expects a number of attributes which define how to access the repository.

SIA is developed on `SIA`_. It is deployed via Phalanx.

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

.. _Simple Image Access v2: https://www.ivoa.net/documents/SIA/
.. _FastAPI: https://fastapi.tiangolo.com/
.. _Phalanx: https://github.com/lsst-sqre/phalanx
.. _dax_obscore: https://github.com/lsst-dm/dax_obscore
.. _Butler: https://github.com/lsst/daf_butler
.. _SIA: https://github.com/lsst-sqre/sia>
