"""Environment-backed login and signed browser sessions for the local UI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from threading import Lock
from time import monotonic
from typing import Dict, List, Optional
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


SESSION_COOKIE_NAME = "grok_demo_session"
SESSION_ISSUER = "grok-demo-local-auth"


class LoginConfigurationError(RuntimeError):
    pass


class LoginRateLimitError(RuntimeError):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("登录尝试过多，请稍后重试")
        self.retry_after_seconds = max(1, retry_after_seconds)


class LoginService:
    """Verify one configured test account without exposing its password."""

    def __init__(self) -> None:
        self._attempts: Dict[str, List[float]] = {}
        self._lock = Lock()

    @property
    def configured(self) -> bool:
        return bool(
            settings.APP_LOGIN_USERNAME
            and settings.APP_LOGIN_PASSWORD
            and settings.AUTH_SESSION_SECRET
        )

    @staticmethod
    def _digest(value: str) -> bytes:
        return sha256(value.encode("utf-8")).digest()

    @property
    def session_seconds(self) -> int:
        return max(1, settings.AUTH_SESSION_HOURS) * 60 * 60

    def _window_seconds(self) -> int:
        return max(1, settings.AUTH_LOCKOUT_MINUTES) * 60

    def authenticate(self, username: str, password: str, client_key: str) -> bool:
        if not self.configured:
            raise LoginConfigurationError("登录账号尚未在服务端环境变量中配置")

        now = monotonic()
        window = self._window_seconds()
        with self._lock:
            recent = [stamp for stamp in self._attempts.get(client_key, []) if now - stamp < window]
            self._attempts[client_key] = recent
            if len(recent) >= max(1, settings.AUTH_MAX_ATTEMPTS):
                retry_after = int(window - (now - recent[0])) + 1
                raise LoginRateLimitError(retry_after)

        username_matches = hmac.compare_digest(
            self._digest(username),
            self._digest(str(settings.APP_LOGIN_USERNAME)),
        )
        password_matches = hmac.compare_digest(
            self._digest(password),
            self._digest(str(settings.APP_LOGIN_PASSWORD)),
        )
        authenticated = username_matches & password_matches
        with self._lock:
            if authenticated:
                self._attempts.pop(client_key, None)
            else:
                self._attempts.setdefault(client_key, []).append(now)
        return bool(authenticated)

    def issue_session(self, username: str) -> str:
        if not self.configured:
            raise LoginConfigurationError("登录账号尚未在服务端环境变量中配置")
        now = datetime.now(timezone.utc)
        payload = {
            "sub": username,
            "scope": "ui_session",
            "iss": SESSION_ISSUER,
            "iat": now,
            "exp": now + timedelta(seconds=self.session_seconds),
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, settings.AUTH_SESSION_SECRET, algorithm=settings.ALGORITHM)

    def session_username(self, token: Optional[str]) -> Optional[str]:
        if not token or not self.configured:
            return None
        try:
            payload = jwt.decode(
                token,
                settings.AUTH_SESSION_SECRET,
                algorithms=[settings.ALGORITHM],
                issuer=SESSION_ISSUER,
            )
        except JWTError:
            return None
        username = payload.get("sub")
        if payload.get("scope") != "ui_session" or username != settings.APP_LOGIN_USERNAME:
            return None
        return str(username)


login_service = LoginService()
