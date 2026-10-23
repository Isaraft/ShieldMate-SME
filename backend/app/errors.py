import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger("shieldmate")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
        headers=SECURITY_HEADERS,
    )


async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    # Do not echo arbitrary exception details into a public response.
    messages = {404: "This endpoint does not exist.", 405: "This method is not allowed."}
    return error_response(
        exc.status_code, f"http_{exc.status_code}", messages.get(exc.status_code, "Request failed.")
    )


async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return error_response(422, "invalid_request", "The request contains invalid values.")


async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    # Avoid exception strings, URLs, request bodies and tracebacks in application logs.
    logger.error("request_failed exception_type=%s", type(exc).__name__)
    return error_response(500, "internal_error", "The service could not complete this request.")
