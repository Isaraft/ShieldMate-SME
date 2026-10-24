"""Bound actual request bytes and keep unexpected exceptions out of server tracebacks."""

import logging

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.errors import SECURITY_HEADERS, error_response, unexpected_error

logger = logging.getLogger("shieldmate")
MAX_BODY = 16384


class SecurityBoundary:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def secured(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = list(message.get("headers", []))
                private = (b"cache-control", b"private, no-store") in headers
                replaced = {name.lower().encode() for name in SECURITY_HEADERS}
                headers = [(k, v) for k, v in headers if k.lower() not in replaced]
                headers.extend(
                    (k.lower().encode(), v.encode()) for k, v in SECURITY_HEADERS.items()
                )
                if private:
                    headers = [(k, v) for k, v in headers if k != b"cache-control"]
                    headers.append((b"cache-control", b"private, no-store"))
                message = {**message, "headers": headers}
            await send(message)

        if scope["method"] in {"POST", "PATCH", "PUT", "DELETE"}:
            headers = dict(scope.get("headers", []))
            length = headers.get(b"content-length", b"0" if scope["method"] == "DELETE" else b"")
            if not length.isdigit() or len(length) > 8 or int(length) > MAX_BODY:
                await error_response(413, "body_too_large", "Request body must be at most 16 KiB.")(
                    scope, receive, secured
                )
                return
            body = bytearray()
            while True:
                chunk = await receive()
                if chunk["type"] == "http.disconnect":
                    return
                part = chunk.get("body", b"")
                if len(body) + len(part) > MAX_BODY:
                    await error_response(
                        413, "body_too_large", "Request body must be at most 16 KiB."
                    )(scope, receive, secured)
                    return
                body.extend(part)
                if not chunk.get("more_body", False):
                    break
            if len(body) != int(length):
                await error_response(
                    400, "invalid_request", "The request contains invalid values."
                )(scope, receive, secured)
                return
            original_receive = receive
            delivered = False

            async def buffered() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await original_receive()

            receive = buffered
        try:
            await self.app(scope, receive, secured)
        except Exception as exc:
            if started:
                logger.error("response_interrupted exception_type=%s", type(exc).__name__)
                # A committed response cannot be replaced. Suppress the original exception context.
                raise RuntimeError("Response interrupted") from None
            response = await unexpected_error(Request(scope), exc)
            await response(scope, receive, secured)
