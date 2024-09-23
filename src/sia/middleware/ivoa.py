"""Middleware for IVOA services."""

import json
from copy import copy
from typing import Any
from urllib.parse import parse_qsl, urlencode

from starlette.types import ASGIApp, Receive, Scope, Send

__all__ = ["CaseInsensitiveQueryAndBodyMiddleware"]


class CaseInsensitiveQueryAndBodyMiddleware:
    """Make query parameter keys and POST body keys all lowercase.

    This middleware attempts to work around case-sensitivity issues by
    lowercasing the query parameter keys and POST body keys before the
    request is processed. This allows normal FastAPI parsing to work without
    regard for case, permitting FastAPI to perform input validation on both
    GET and POST parameters.

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

        if scope.get("query_string"):
            params = [
                (k.lower(), v) for k, v in parse_qsl(scope["query_string"])
            ]
            scope["query_string"] = urlencode(params).encode()

        if scope["method"] == "POST":
            body = await self.get_body(receive)
            modified_body = await self.process_body(body)
            receive = self.wrapped_receive(modified_body)

        await self._app(scope, receive, send)

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

    async def process_body(self, body: bytes) -> bytes:
        """Process the body, lowercasing keys if it's JSON.

        Parameters
        ----------
        body
            The request body.

        Returns
        -------
        bytes
            The processed request body.
        """
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                data = self.lowercase_keys_recursive(data)
            return json.dumps(data).encode()
        except json.JSONDecodeError:
            return body

    def lowercase_keys_recursive(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively lowercase all dictionary keys.

        Parameters
        ----------
        data
            The dictionary to process.

        Returns
        -------
        Dict[str, Any]
            The dictionary with all keys lowercased.
        """
        return {
            k.lower(): (
                self.lowercase_keys_recursive(v) if isinstance(v, dict) else v
            )
            for k, v in data.items()
        }

    @staticmethod
    def wrapped_receive(body: bytes) -> Receive:
        """Wrap the receive function to return our modified body.

        Parameters
        ----------
        body
            The modified request body.

        Returns
        -------
        Receive
            The wrapped receive function.
        """

        async def receive_wrapper() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        return receive_wrapper
