"""Cross-site request protection and response headers.

State-changing requests (POST/PUT/PATCH/DELETE) must carry `X-CareBridge-Request: 1` (a custom header cannot be sent cross-site without a CORS
pre-flight, which only ALLOWED_ORIGINS pass) and, when the browser sends an Origin, it must be allowed. A request without Origin is accepted only
because the header is present (non-browser clients). The cookie is SameSite=Lax HttpOnly as a second layer."""
from fastapi import FastAPI, Request

from app.api.errors import error_response

HEADER = "x-carebridge-request"
SAFE = {"GET", "HEAD", "OPTIONS"}
CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def install(app: FastAPI, origins: list[str]) -> None:
    allowed = set(origins)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.method not in SAFE:
            origin = request.headers.get("origin")
            if request.headers.get(HEADER) != "1":
                return _harden(error_response(403, "request_blocked", msg="Missing X-CareBridge-Request header."))
            if origin is not None and origin not in allowed:
                return _harden(error_response(403, "request_blocked", msg="Origin not allowed."))
        return _harden(await call_next(request))


def _harden(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = CSP
    return resp
