from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.services.config_persistence_service import config_persistence_service

router = APIRouter(prefix="/api/v1/user", tags=["user"])


# Request/Response Models
class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    target_return: Optional[float] = None
    investment_horizon: Optional[str] = None
    risk_tolerance: Optional[str] = None
    available_capital: Optional[float] = None
    preferred_sectors: Optional[list] = None
    excluded_sectors: Optional[list] = None


class InvestmentGoalsUpdate(BaseModel):
    target_return: float
    investment_horizon: str
    risk_tolerance: str
    available_capital: float
    max_position_size: float
    max_loss_per_trade: float
    preferred_sectors: list
    excluded_sectors: list


class RiskProfileUpdate(BaseModel):
    risk_tolerance: str
    max_drawdown: float
    volatility_tolerance: str
    loss_capacity: float
    investment_experience: str
    income_stability: str
    investment_goals: list


class PortfolioSettingsUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    target_allocation: dict
    rebalancing_frequency: str
    auto_rebalance: bool
    is_default: bool


class NotificationSettingsUpdate(BaseModel):
    enabled: bool
    channels: dict
    frequency: str
    quiet_hours: dict
    alert_types: dict


# Endpoints
@router.get("/profile")
async def get_user_profile(user_id: str = "default"):
    """Get user profile."""
    try:
        profile = await config_persistence_service.get_user_profile(user_id)
        if not profile:
            return {"user_id": user_id, "status": "not_configured"}
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
async def update_user_profile(
    updates: UserProfileUpdate,
    user_id: str = "default",
):
    """Update user profile."""
    try:
        result = await config_persistence_service.save_user_profile(
            user_id, updates.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/goals")
async def update_investment_goals(
    goals: InvestmentGoalsUpdate,
    user_id: str = "default",
):
    """Update investment goals."""
    try:
        result = await config_persistence_service.save_user_profile(
            user_id, goals.dict()
        )
        return {"status": "saved", "goals": goals.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/risk-profile")
async def update_risk_profile(
    profile: RiskProfileUpdate,
    user_id: str = "default",
):
    """Update risk profile."""
    try:
        result = await config_persistence_service.save_user_profile(
            user_id, profile.dict()
        )
        return {"status": "saved", "risk_profile": profile.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/portfolio")
async def update_portfolio_settings(
    settings: PortfolioSettingsUpdate,
    user_id: str = "default",
):
    """Update portfolio settings."""
    try:
        result = await config_persistence_service.save_portfolio(
            user_id, settings.dict()
        )
        return {"status": "saved", "portfolio": settings.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolios")
async def get_user_portfolios(user_id: str = "default"):
    """Get user portfolios."""
    try:
        portfolios = await config_persistence_service.get_user_portfolios(user_id)
        return {"portfolios": portfolios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications")
async def update_notification_settings(
    settings: NotificationSettingsUpdate,
    user_id: str = "default",
):
    """Update notification settings."""
    try:
        result = await config_persistence_service.save_user_profile(
            user_id, {"notification_settings": settings.dict()}
        )
        return {"status": "saved", "notifications": settings.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_user_config(user_id: str = "default"):
    """Export all user configuration."""
    try:
        config = await config_persistence_service.export_user_config(user_id)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_user_config(
    config: dict,
    user_id: str = "default",
):
    """Import user configuration."""
    try:
        result = await config_persistence_service.import_user_config(user_id, config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_user_config(user_id: str = "default"):
    """Reset user configuration to defaults."""
    try:
        result = await config_persistence_service.reset_user_config(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
