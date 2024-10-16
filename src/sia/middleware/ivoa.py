"""Middleware for IVOA services."""

from copy import copy
from urllib.parse import parse_qsl, urlencode

from starlette.types import ASGIApp, Receive, Scope, Send

__all__ = ["CaseInsensitiveFormMiddleware"]


class CaseInsensitiveFormMiddleware:
    """Make POST parameter keys all lowercase.

    This middleware attempts to work around case-sensitivity issues by
    lowercasing POST parameter keys before the request is processed. This
    allows normal FastAPI parsing to work without regard for case, permitting
    FastAPI to perform input validation on the POST parameters.
    """

    def __init__(self, *, app: ASGIApp) -> None:
        """Initialize the middleware with the ASGI application.

        Parameters
        ----------
        app
            The ASGI application to wrap.
        """
        self._app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Process request set query parameters and POST body keys to
        lowercase.
        """
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        scope = copy(scope)

        if scope["method"] == "POST" and self.is_form_data(scope):
            receive = self.wrapped_receive(receive)

        await self._app(scope, receive, send)

    @staticmethod
    def is_form_data(scope: Scope) -> bool:
        """Check if the request contains form data.

        Parameters
        ----------
        scope
            The request scope.

        Returns
        -------
        bool
            True if the request contains form data, False otherwise.
        """
        headers = {
            k.decode("latin-1"): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        content_type = headers.get("content-type", "")
        return content_type.startswith("application/x-www-form-urlencoded")

    @staticmethod
    async def get_body(receive: Receive) -> bytes:
        """Read the entire request body.

        Parameters
        ----------
        receive
            The receive function to read messages from.

        Returns
        -------
        bytes
            The entire request body.
        """
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        return body

    @staticmethod
    async def process_form_data(body: bytes) -> bytes:
        """Process the body, lowercasing keys of form data.

        Parameters
        ----------
        body
            The request body.

        Returns
        -------
        bytes
            The processed request body with lowercased keys.
        """
        body_str = body.decode("utf-8")
        parsed = parse_qsl(body_str)
        lowercased = [(key.lower(), value) for key, value in parsed]
        processed = urlencode(lowercased)
        return processed.encode("utf-8")

    def wrapped_receive(self, receive: Receive) -> Receive:
        """Wrap the receive function to process form data.

        Parameters
        ----------
        receive
            The receive function to wrap.

        Returns
        -------
        Receive
            The wrapped receive function.
        """

        async def inner() -> dict:
            """Process the form data and return the request."""
            body = await self.get_body(receive)
            processed_body = await self.process_form_data(body)
            return {
                "type": "http.request",
                "body": processed_body,
                "more_body": False,
            }

        return inner
