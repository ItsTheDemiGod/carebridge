"""One error format: {"error": {"code", "message"}}. Messages come from the English templates (error.<code>); the UI can fetch the same ids in
ta/hi from /api/v1/strings. Messages never echo user content and responses never carry stack traces."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services import templates as T

log = logging.getLogger("carebridge")


class ApiError(Exception):
    def __init__(self, status: int, code: str, headers: dict | None = None):
        super().__init__(code)
        self.status, self.code, self.headers = status, code, headers or {}


def message(code: str) -> str:
    try:
        return T.render(f"error.{code}", "en")
    except KeyError:
        return T.render("error.internal_error", "en")


def body(code: str, msg: str | None = None) -> dict:
    return {"error": {"code": code, "message": msg or message(code)}}


def error_response(status: int, code: str, headers: dict | None = None, msg: str | None = None) -> JSONResponse:
    return JSONResponse(body(code, msg), status_code=status, headers=headers)


STATUS_CODES = {404: "not_found", 405: "invalid_request", 413: "upload_too_large", 401: "no_session", 403: "request_blocked"}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return error_response(e.status, e.code, e.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        return error_response(422, "invalid_request")  # never echo the invalid input

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        return error_response(e.status_code, STATUS_CODES.get(e.status_code, "invalid_request"))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, e: Exception):
        log.error("unhandled error type=%s", type(e).__name__)  # type only: the message may contain user content
        return error_response(500, "internal_error")
