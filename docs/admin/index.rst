##############
Administration
##############


Helm configuration
==================

The SIAv2 service is deployed via Phalanx, which requires a ``values-{env}.yaml`` configuration file to be provided. Most of the configuration is fairly standard and common with other applications in Phalanx and has defaults in the ``values.yaml``.

The main configuration that needs to be provided is the list of Butler Repositories (``butlerDataCollections``), and all the relevant attributes for each repository which are listed below:

butlerDataCollections
---------------------

**config** (required)
    A path (HTTP or File Path) to the Obscore configuration.

    Example: ``"https://raw.githubusercontent.com/lsst-dm/dax_obscore/refs/heads/main/configs/dp02.yaml"``

**label** (required)
    The label for the Butler repository.

    Example: ``"dp02"``

**name** (required)
    Name of the Butler repository. This is used by the app to configure the path to the SIAv2 service for this repository.
    For example ``"dp02"`` will result in ``"https://data-dev.lsst.cloud/api/sia/dp02"``

**butler_type** (required)
    The type of Butler repository.
    Only ``REMOTE`` is supported.

    Example: ``"REMOTE"``

**repository** (required)
    A path (HTTP or File Path) to the Butler repository.

    Example: ``"https://data-dev.lsst.cloud/api/butler/configs/dp02.yaml"``

**datalink_url** (optional)
    An HTTP path to overwrite the Datalink endpoint in the obscore repository with.

    Example: ``"https://data-dev.lsst.cloud/api/datalink/links?ID=butler%3A//dp02/{id}"``.

Ingresses
==================

**Anonymous Paths**

By default SIA sets up an anonymous ingress for these paths:

- path: "/openapi.json"

- path: "/{collection}/capabilities"

- path: "/{collection}/availability"

**Authenticated Paths**

All other paths of the app, including /query are authenticated:

- path: /



Vault secrets
=============

The SIA applications by default does not require any secrets to be setup by an administrator, as the secrets that it does expect are copied over from other Phalanx applications.
An administrator can however define an environment specific :file:`secrets.yaml` file and overwrite these if they wish.

These secrets are listed below:

**sentry-dsn**:
  DSN for Sentry reporting, required if ``config.sentry.enabled`` is set to true.

**slack-webhook**:
  Copied from mobu if ``config.slackAlerts`` is set to true.


Deployment Information
======================

SIA will deploy one pod by default, which is the SIA FastAPI application.
This will be the main FastAPI web-service running the SIA application.
Any relevant logs during operations will be in the logs of this pod.


Use with a Remote Butler
==========================

To connect the SIA app with a Remote Butler repository, the values in the configuration need to be specified as described, ensuring their ``butler_type`` is set to **REMOTE**. Then when a user wishes to run a query they need to provide a Bearer token as with several other apps in Phalanx (see TAP for example). This is possible with most python clients (pyvo/astropy) and is handled automatically for the user when accessing via a browser having previously logged in.
If a token is not provided the app will reject the request with an authorization error.


Service Self-Description
========================

SIA v2 Services are expected to return a self-description VOTable document with metadata describing the input & output of the service, including where appropriate ranges or enumeration of possible values.
This SIA app is configured to generate that response via a combination of information gathered from the specific Butler Repository of the service being queried, and the repository attributes defined in the configuration values for the environment. In the future we may end-up generating everything from the Butler repository to ensure we avoid any unexpected behavior.
