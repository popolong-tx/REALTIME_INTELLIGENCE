"""Login, session status, and logout endpoints for the product shell."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.audit_trail_service import AuditEventType, audit_trail_service
from app.services.login_service import (
    LoginConfigurationError,
    LoginRateLimitError,
    SESSION_COOKIE_NAME,
    login_service,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=512)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def _audit_safely(
    event_type: AuditEventType,
    *,
    request: Request,
    user_id: str | None,
    action: str,
    details: dict,
) -> None:
    try:
        await audit_trail_service.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="authentication",
            resource_id="local-ui-session",
            action=action,
            details=details,
            ip_address=_client_key(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.exception("Authentication audit event could not be persisted")


@router.get("/status")
async def session_status(request: Request):
    username = login_service.session_username(request.cookies.get(SESSION_COOKIE_NAME))
    return {
        "authenticated": bool(username),
        "username": username,
        "authentication_required": True,
        "configured": login_service.configured,
    }


@router.post("/login")
async def login(credentials: LoginRequest, request: Request):
    try:
        valid = login_service.authenticate(
            credentials.username,
            credentials.password,
            _client_key(request),
        )
    except LoginConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LoginRateLimitError as exc:
        await _audit_safely(
            AuditEventType.SYSTEM_EVENT,
            request=request,
            user_id=None,
            action="login_rate_limited",
            details={"retry_after_seconds": exc.retry_after_seconds},
        )
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    if not valid:
        await _audit_safely(
            AuditEventType.SYSTEM_EVENT,
            request=request,
            user_id=None,
            action="login_failed",
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = login_service.issue_session(str(settings.APP_LOGIN_USERNAME))
    response = JSONResponse(
        {
            "authenticated": True,
            "username": settings.APP_LOGIN_USERNAME,
            "expires_in_seconds": login_service.session_seconds,
        }
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=login_service.session_seconds,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    await _audit_safely(
        AuditEventType.USER_LOGIN,
        request=request,
        user_id=str(settings.APP_LOGIN_USERNAME),
        action="login_success",
        details={"session_hours": settings.AUTH_SESSION_HOURS},
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    username = login_service.session_username(request.cookies.get(SESSION_COOKIE_NAME))
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    if username:
        await _audit_safely(
            AuditEventType.USER_LOGOUT,
            request=request,
            user_id=username,
            action="logout",
            details={},
        )
    return response
