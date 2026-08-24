from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings
from app.services.role_permission_service import role_permission_service, Role, Permission

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Get current user from token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {"user_id": user_id, "payload": payload}


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Get current user from token, or None if not authenticated."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """Decorator to require a specific permission."""

    async def permission_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_id = current_user["user_id"]

        if not role_permission_service.has_permission(user_id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )

        return current_user

    return permission_checker


def require_role(role: Role):
    """Decorator to require a specific role."""

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_id = current_user["user_id"]
        user_role = role_permission_service.get_user_role(user_id)

        if user_role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}",
            )

        return current_user

    return role_checker


def require_any_role(*roles: Role):
    """Decorator to require any of the specified roles."""

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_id = current_user["user_id"]
        user_role = role_permission_service.get_user_role(user_id)

        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(r.value for r in roles)}",
            )

        return current_user

    return role_checker


# Permission-based dependencies
require_view_stock = require_permission(Permission.VIEW_STOCK)
require_search_stock = require_permission(Permission.SEARCH_STOCK)
require_view_recommendation = require_permission(Permission.VIEW_RECOMMENDATION)
require_generate_recommendation = require_permission(Permission.GENERATE_RECOMMENDATION)
require_manage_recommendation = require_permission(Permission.MANAGE_RECOMMENDATION)
require_view_model = require_permission(Permission.VIEW_MODEL)
require_train_model = require_permission(Permission.TRAIN_MODEL)
require_approve_model = require_permission(Permission.APPROVE_MODEL)
require_deploy_model = require_permission(Permission.DEPLOY_MODEL)
require_view_portfolio = require_permission(Permission.VIEW_PORTFOLIO)
require_manage_portfolio = require_permission(Permission.MANAGE_PORTFOLIO)
require_view_users = require_permission(Permission.VIEW_USERS)
require_manage_users = require_permission(Permission.MANAGE_USERS)
require_view_audit = require_permission(Permission.VIEW_AUDIT)
require_manage_system = require_permission(Permission.MANAGE_SYSTEM)

# Role-based dependencies
require_viewer = require_role(Role.VIEWER)
require_analyst = require_role(Role.ANALYST)
require_researcher = require_role(Role.RESEARCHER)
require_trader = require_role(Role.TRADER)
require_admin = require_role(Role.ADMIN)
