#####
Usage
#####


``sia`` is an image-access API complying with the IVOA SIA (v2) specification.
For documentation on the protocol and details on usage including input parameters & output see the IVOA `SIAv2`_ specification.

Parameters
=============

Example of commonly used parameters:

:POS: Central position of the region of interest (ICRS RA,Dec in degrees)
:SIZE: Size of the search region in degrees
:BAND: Energy bandpass to search
:TIME: Time interval to search

For a full list of parameters see the IVOA `SIAv2`_ specification

HTTP Methods
=============
Both POST & GET methods are implemented for the /query API in accordance to the specification

HTTP GET Example::

    https://data-dev.lsst.cloud/api/sia/dp02/query?POS=CIRCLE+55.7467+-32.2862+0.05

HTTP POST Example::

    curl -X POST "https://data-dev.lsst.cloud/api/sia/dp02/query" \
	-H "Authorization: Bearer your_token_here" \
	-d "POS=CIRCLE+55.7467+-32.2862+0.05"

Response
=============

SIAv2 responses will typically be in VOTable format, containing:

- Metadata about the service

Metadata like the fields of the response data will be included in the response assuming it did not produce an error table.
If MAXREC is set to 0, the self-description VOTable will be returned, which contains detailed information on the expected parameters, including range of possible values where appropriate and the result fields.

- Table of available image products matching the query

The results will include in the "access_url" field a link that can be used to retrieve each image.
The format (access_format) will either be a datalink (x-votable+xml;content=datalink) if the results are a datalink or the image content-type if the link is a direct download link to the image.

Example response structure::


    <VOTABLE>
      <RESOURCE type="results">
        <TABLE>
          <FIELD name="access_url" datatype="char" ucd="meta.ref.url"/>
          <FIELD name="access_format" datatype="char" ucd="meta.code.mime"/>
          <!-- Other metadata fields -->
          <DATA>
            <TABLEDATA>
              <TR>
                <TD>http://example.com/image1.fits</TD>
                <TD>image/fits</TD>
                <!-- Other metadata values -->
              </TR>
              <!-- More table rows -->
            </TABLEDATA>
          </DATA>
        </TABLE>
      </RESOURCE>
    </VOTABLE>

VOTable is the only format supported in this current version. In the future this may be extended to support other formats depending on requests and feedback from the community.

Errors
=============

SIAv2 services use standard HTTP status codes. Common errors:

:400: Bad Request (invalid parameters)
:404: Not Found (no matching data)
:500: Internal Server Error

Bad request errors (400), which in most cases will be invalid parameters provided via a query are displayed as a VOTable error.

The other two error types indicate either an invalid URL or an unexpected server-side issue which needs to be resolved so we do not format these as VOTables.

Example Error VOTable::

    <VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.3">
      <RESOURCE>
        <INFO name="QUERY_STATUS" value="ERROR">UsageFault: Unrecognized shape in POS string 'other_shape'</INFO>
      </RESOURCE>
    </VOTABLE>


Discovery
=============

The expectation is that production SIAv2 services will be registered and discoverable via VO clients, however if they are not, use of the service will require users to input the SIA service URL manually or any clients using it to hard code this value.


Query using Pyvo
===================

Querying the SIAv2 service is also possible using the `pyvo`_ package.
Here is an example of such a query::

    from pyvo.dal import SIA2Service
    service = SIA2Service(sia_url, auth)
    t1 = Time("60550.31803461111", format='mjd').to_datetime()
    t2 = Time("60550.31838182871", format='mjd').to_datetime()
    results = service.search(pos=(55.7467, -32.2862, 0.05), time=[t1, t2])
    results.to_table()

Result can then be parsed to download the images using the access_url field in
the response::

    dataLinkUrl = random.choice(results).access_url
    from pyvo.dal.adhoc import DatalinkResults
    dl_result = DatalinkResults.from_result_url(
        dataLinkUrl, session=auth
    )
    image_url = dl_result.getrecord(0).get('access_url')


.. _Butler: https://github.com/lsst/daf_butler
.. _pyvo: https://pyvo.readthedocs.io/en/latest/
.. _SIAv2: https://www.ivoa.net/documents/SIA/
