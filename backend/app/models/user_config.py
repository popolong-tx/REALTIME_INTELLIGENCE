from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentHorizon(str, Enum):
    SHORT = "short"  # 1-4 weeks
    MEDIUM = "medium"  # 1-3 months
    LONG = "long"  # 3-12 months


class UserProfile(Base):
    """User profile and configuration."""

    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False)

    # Basic info
    display_name = Column(String)
    email = Column(String)

    # Investment goals
    target_return = Column(Float)  # Annual target return percentage
    investment_horizon = Column(SQLEnum(InvestmentHorizon), default=InvestmentHorizon.MEDIUM)
    risk_tolerance = Column(SQLEnum(RiskTolerance), default=RiskTolerance.MODERATE)

    # Financial info
    available_capital = Column(Float)
    current_portfolio_value = Column(Float)

    # Preferences
    preferred_sectors = Column(JSON)  # List of preferred sectors
    excluded_sectors = Column(JSON)  # List of excluded sectors
    preferred_markets = Column(JSON)  # List of preferred markets

    # Notification settings
    notification_enabled = Column(Boolean, default=True)
    notification_channels = Column(JSON)  # email, sms, push
    notification_frequency = Column(String, default="daily")  # immediate, daily, weekly

    # Risk parameters
    max_position_size = Column(Float)  # Max position size as percentage
    max_loss_per_trade = Column(Float)  # Max loss per trade as percentage
    max_drawdown = Column(Float)  # Max acceptable drawdown

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolios = relationship("UserPortfolio", back_populates="user")
    recommendations = relationship("UserRecommendation", back_populates="user")


class UserPortfolio(Base):
    """User portfolio configuration."""

    __tablename__ = "user_portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)

    # Portfolio info
    name = Column(String, nullable=False)
    description = Column(String)

    # Portfolio settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Allocation targets
    target_allocation = Column(JSON)  # {"stocks": 0.6, "bonds": 0.3, "cash": 0.1}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserProfile", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio")


class PortfolioHolding(Base):
    """Individual holdings in a portfolio."""

    __tablename__ = "portfolio_holdings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("user_portfolios.id"), nullable=False)

    # Holding info
    symbol = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    average_cost = Column(Float, nullable=False)

    # Current value
    current_price = Column(Float)
    current_value = Column(Float)
    unrealized_pnl = Column(Float)
    unrealized_pnl_pct = Column(Float)

    # Timestamps
    purchased_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("UserPortfolio", back_populates="holdings")


class UserRecommendation(Base):
    """User's saved recommendations."""

    __tablename__ = "user_recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)

    # Recommendation info
    symbol = Column(String, nullable=False)
    recommendation_type = Column(String, nullable=False)  # buy, sell, hold
    confidence = Column(Float)
    risk_level = Column(String)

    # Price targets
    entry_price = Column(Float)
    target_price = Column(Float)
    stop_loss = Column(Float)

    # Status
    status = Column(String, default="active")  # active, expired, triggered
    is_favorite = Column(Boolean, default=False)

    # Notes
    user_notes = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    triggered_at = Column(DateTime)

    # Relationships
    user = relationship("UserProfile", back_populates="recommendations")


class UserAlert(Base):
    """User price and condition alerts."""

    __tablename__ = "user_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)

    # Alert info
    symbol = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # price_above, price_below, percent_change
    condition = Column(JSON)  # {"price": 150, "direction": "above"}

    # Status
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime)

    # Notification
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserWatchlist(Base):
    """User watchlists."""

    __tablename__ = "user_watchlists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user_profiles.user_id"), nullable=False)

    # Watchlist info
    name = Column(String, nullable=False)
    description = Column(String)

    # Settings
    is_default = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("WatchlistItem", back_populates="watchlist")


class WatchlistItem(Base):
    """Items in a watchlist."""

    __tablename__ = "watchlist_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    watchlist_id = Column(String, ForeignKey("user_watchlists.id"), nullable=False)

    # Item info
    symbol = Column(String, nullable=False)
    notes = Column(String)

    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    watchlist = relationship("UserWatchlist", back_populates="items")
