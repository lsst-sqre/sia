##############
Administration
##############

Helm configuration
==================

The SIAv2 service is deployed via Phalanx, which requires a :file:`values-{env}.yaml` configuration file to be provided.
Most of the configuration is fairly standard and common with other applications in Phalanx and has defaults in the :file:`values.yaml`.

The two main settings that need to be configured for a given environment are:

**config.datasets** (required)
    A list of Repertoire dataset names (``dp1``, ``dp2``, etc.) that this instance of SIA should serve.
    Each of these datasets must have a Butler configuration in service discovery and must have an entry in **obscoreConfig** (see below).

**config.obscoreConfig** (required)
    A mapping of dataset names to the corresponding ObsCore exporter configuration.
    For example, ``dp02`` might map to ``https://raw.githubusercontent.com/lsst-dm/dax_obscore/refs/heads/main/configs/dp02.yaml``.


Ingresses
=========

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


Authentication
==============

When a user wishes to run a query, they need to provide a Bearer token as with several other apps in Phalanx (see TAP for example).
This is possible with most Python clients (pyVO and astropy, for example) and is handled automatically for the user when accessing via a browser having previously logged in.

If a token is not provided the app will reject the request with an authorization error.


Service Self-Description
========================

SIA v2 Services are expected to return a self-description VOTable document with metadata describing the input & output of the service, including where appropriate ranges or enumeration of possible values.
This SIA app is configured to generate that response via a combination of information gathered from the specific Butler Repository of the service being queried, and the repository attributes defined in the configuration values for the environment. In the future we may end-up generating everything from the Butler repository to ensure we avoid any unexpected behavior.
