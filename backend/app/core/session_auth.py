"""Request middleware that protects the UI shell and business APIs."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.login_service import SESSION_COOKIE_NAME, login_service


PUBLIC_PATHS = {
    "/login",
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/status",
}
PUBLIC_PREFIXES = ("/assets/",)


class SessionAuthenticationMiddleware(BaseHTTPMiddleware):
    """Require a valid signed session for the product and its business APIs."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (
            request.method == "OPTIONS"
            or path in PUBLIC_PATHS
            or path.startswith(PUBLIC_PREFIXES)
        ):
            return await call_next(request)

        username = login_service.session_username(request.cookies.get(SESSION_COOKIE_NAME))
        if username:
            request.state.authenticated_username = username
            return await call_next(request)

        if path.startswith("/api/") or path == "/openapi.json":
            return JSONResponse(
                {"detail": "请先登录后再访问系统"},
                status_code=401,
                headers={"Cache-Control": "no-store"},
            )

        next_path = path if path.startswith("/") and not path.startswith("//") else "/"
        return RedirectResponse(
            url=f"/login?next={quote(next_path, safe='/')}",
            status_code=303,
            headers={"Cache-Control": "no-store"},
        )
