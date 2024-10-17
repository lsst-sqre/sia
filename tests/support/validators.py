"""Validators for testing the responses of the API."""

from defusedxml import ElementTree as DefusedET
from httpx import Response


def validate_response(
    response: Response, status_code: int, content_type: str
) -> None:
    """Validate that the response is an error with the expected status code
    and content_type.

    Parameters
    ----------
    response
        The response to validate.
    status_code
        The expected status code.
    content_type
        The expected error message.

    Raises
    ------
    AssertionError
        If the response is not an expected error
    """
    assert response.status_code == status_code
    assert content_type in response.headers["Content-Type"]


def validate_votable_error(
    response: Response,
    expected_message: str | None,
) -> None:
    """Validate that the response is a VOTable error with the expected message.

    Parameters
    ----------
    response
        The response to validate.
    expected_message
        The expected error message.

    Raises
    ------
    AssertionError
        If the response is not a VOTable error with the expected message.
    """
    root = DefusedET.fromstring(response.text)
    assert root.tag == "{http://www.ivoa.net/xml/VOTable/v1.3}VOTABLE"
    assert root.attrib["version"] == "1.3"
    resource = root.find("{http://www.ivoa.net/xml/VOTable/v1.3}RESOURCE")
    assert resource is not None
    info = resource.find("{http://www.ivoa.net/xml/VOTable/v1.3}INFO")
    assert info is not None
    assert info.attrib["name"] == "QUERY_STATUS"
    assert info.attrib["value"] == "ERROR"
    if expected_message and info.text:
        assert info.text.startswith(expected_message)


def valid_votable(xml_string: str) -> bool:
    """Check if the VOTable structure is valid and has at least one Table row.

    Parameters
    ----------
    xml_string
        The VOTable XML string to validate.

    Returns
    -------
    bool
        True if the XML string is a valid VOTable with some data,
        False otherwise.
    """
    try:
        root = DefusedET.fromstring(xml_string)
        resource = root.find("{http://www.ivoa.net/xml/VOTable/v1.3}RESOURCE")
        if resource is None:
            return False

        info = resource.find("{http://www.ivoa.net/xml/VOTable/v1.3}INFO")
        if info is not None:
            if (
                info is None
                or info.get("name") != "QUERY_STATUS"
                or info.get("value") != "OK"
            ):
                return False

        table = resource.find("{http://www.ivoa.net/xml/VOTable/v1.3}TABLE")

        if table is None:
            return False

        data = table.find("{http://www.ivoa.net/xml/VOTable/v1.3}DATA")
        if data is None:
            return False

        tabledata = data.find(
            "{http://www.ivoa.net/xml/VOTable/v1.3}TABLEDATA"
        )

        if tabledata is None:
            return False

        return (
            tabledata.find("{http://www.ivoa.net/xml/VOTable/v1.3}TR")
            is not None
        )

    except DefusedET.ParseError:
        return False
