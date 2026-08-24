from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

from app.core.database import SessionLocal
from app.models.user_config import UserProfile, UserPortfolio, UserAlert, UserWatchlist

logger = logging.getLogger(__name__)


class ConfigPersistenceService:
    """Service for persisting and backing up user configurations."""

    async def save_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save user profile configuration."""
        db = SessionLocal()
        try:
            # Check if profile exists
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if profile:
                # Update existing profile
                for key, value in profile_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.updated_at = datetime.utcnow()
            else:
                # Create new profile
                profile = UserProfile(
                    user_id=user_id,
                    **profile_data,
                )
                db.add(profile)

            db.commit()
            db.refresh(profile)

            return {
                "user_id": user_id,
                "profile_id": profile.id,
                "saved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving user profile: {e}")
            raise
        finally:
            db.close()

    async def get_user_profile(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get user profile configuration."""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if not profile:
                return None

            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "email": profile.email,
                "target_return": profile.target_return,
                "investment_horizon": profile.investment_horizon.value if profile.investment_horizon else None,
                "risk_tolerance": profile.risk_tolerance.value if profile.risk_tolerance else None,
                "available_capital": profile.available_capital,
                "current_portfolio_value": profile.current_portfolio_value,
                "preferred_sectors": profile.preferred_sectors,
                "excluded_sectors": profile.excluded_sectors,
                "preferred_markets": profile.preferred_markets,
                "notification_enabled": profile.notification_enabled,
                "notification_channels": profile.notification_channels,
                "notification_frequency": profile.notification_frequency,
                "max_position_size": profile.max_position_size,
                "max_loss_per_trade": profile.max_loss_per_trade,
                "max_drawdown": profile.max_drawdown,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
            }

        finally:
            db.close()

    async def save_portfolio(
        self,
        user_id: str,
        portfolio_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save portfolio configuration."""
        db = SessionLocal()
        try:
            portfolio = UserPortfolio(
                user_id=user_id,
                **portfolio_data,
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)

            return {
                "portfolio_id": portfolio.id,
                "user_id": user_id,
                "name": portfolio.name,
                "saved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving portfolio: {e}")
            raise
        finally:
            db.close()

    async def get_user_portfolios(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all portfolios for a user."""
        db = SessionLocal()
        try:
            portfolios = db.query(UserPortfolio).filter(
                UserPortfolio.user_id == user_id
            ).all()

            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "is_default": p.is_default,
                    "is_active": p.is_active,
                    "target_allocation": p.target_allocation,
                    "created_at": p.created_at.isoformat(),
                }
                for p in portfolios
            ]

        finally:
            db.close()

    async def export_user_config(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Export all user configuration."""
        db = SessionLocal()
        try:
            # Get profile
            profile = await self.get_user_profile(user_id)

            # Get portfolios
            portfolios = await self.get_user_portfolios(user_id)

            # Get alerts
            alerts = db.query(UserAlert).filter(UserAlert.user_id == user_id).all()
            alerts_data = [
                {
                    "symbol": a.symbol,
                    "alert_type": a.alert_type,
                    "condition": a.condition,
                    "is_active": a.is_active,
                }
                for a in alerts
            ]

            # Get watchlists
            watchlists = db.query(UserWatchlist).filter(UserWatchlist.user_id == user_id).all()
            watchlists_data = [
                {
                    "name": w.name,
                    "description": w.description,
                    "items": [item.symbol for item in w.items],
                }
                for w in watchlists
            ]

            return {
                "user_id": user_id,
                "exported_at": datetime.utcnow().isoformat(),
                "profile": profile,
                "portfolios": portfolios,
                "alerts": alerts_data,
                "watchlists": watchlists_data,
                "version": "1.0",
            }

        finally:
            db.close()

    async def import_user_config(
        self,
        user_id: str,
        config_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Import user configuration."""
        db = SessionLocal()
        try:
            imported_items = []

            # Import profile
            if "profile" in config_data and config_data["profile"]:
                await self.save_user_profile(user_id, config_data["profile"])
                imported_items.append("profile")

            # Import portfolios
            if "portfolios" in config_data:
                for portfolio in config_data["portfolios"]:
                    await self.save_portfolio(user_id, portfolio)
                imported_items.append(f"portfolios ({len(config_data['portfolios'])})")

            # Import alerts
            if "alerts" in config_data:
                for alert_data in config_data["alerts"]:
                    alert = UserAlert(
                        user_id=user_id,
                        **alert_data,
                    )
                    db.add(alert)
                imported_items.append(f"alerts ({len(config_data['alerts'])})")

            # Import watchlists
            if "watchlists" in config_data:
                for watchlist_data in config_data["watchlists"]:
                    watchlist = UserWatchlist(
                        user_id=user_id,
                        name=watchlist_data["name"],
                        description=watchlist_data.get("description"),
                    )
                    db.add(watchlist)
                imported_items.append(f"watchlists ({len(config_data['watchlists'])})")

            db.commit()

            return {
                "user_id": user_id,
                "imported_items": imported_items,
                "imported_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error importing user config: {e}")
            raise
        finally:
            db.close()

    async def reset_user_config(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Reset user configuration to defaults."""
        db = SessionLocal()
        try:
            # Delete existing data
            db.query(UserAlert).filter(UserAlert.user_id == user_id).delete()
            db.query(UserWatchlist).filter(UserWatchlist.user_id == user_id).delete()
            db.query(UserPortfolio).filter(UserPortfolio.user_id == user_id).delete()
            db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()

            db.commit()

            return {
                "user_id": user_id,
                "reset_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting user config: {e}")
            raise
        finally:
            db.close()


# Global service instance
config_persistence_service = ConfigPersistenceService()
