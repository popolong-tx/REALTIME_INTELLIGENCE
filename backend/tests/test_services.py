import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.stock_validator import StockValidator
from app.services.risk_management_service import RiskManagementService
from app.services.prohibited_language_service import ProhibitedLanguageService
from app.services.investor_suitability_service import InvestorSuitabilityService


class TestStockValidator:
    """Test stock validator service."""

    def setup_method(self):
        self.validator = StockValidator()

    def test_validate_format_us_stock(self):
        """Test US stock format validation."""
        assert self.validator.validate_format("AAPL") is True
        assert self.validator.validate_format("MSFT") is True
        assert self.validator.validate_format("GOOGL") is True
        assert self.validator.validate_format("INVALID123") is False
        assert self.validator.validate_format("") is False

    def test_validate_format_china_stock(self):
        """Test China stock format validation."""
        assert self.validator.validate_format("600519.SH") is True
        assert self.validator.validate_format("000858.SZ") is True
        assert self.validator.validate_format("12345.SH") is False  # Wrong length

    def test_validate_format_hk_stock(self):
        """Test HK stock format validation."""
        assert self.validator.validate_format("0700.HK") is True
        assert self.validator.validate_format("9988.HK") is True

    def test_get_market(self):
        """Test market detection."""
        assert self.validator.get_market("AAPL") == "US"
        assert self.validator.get_market("600519.SH") == "SH"
        assert self.validator.get_market("000858.SZ") == "SZ"
        assert self.validator.get_market("0700.HK") == "HK"
        assert self.validator.get_market("INVALID") is None

    def test_suggest_similar(self):
        """Test stock suggestions."""
        suggestions = self.validator.suggest_similar("AA", 5)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5


class TestRiskManagementService:
    """Test risk management service."""

    def setup_method(self):
        self.service = RiskManagementService()

    def test_calculate_position_size(self):
        """Test position size calculation."""
        result = self.service.calculate_position_size(
            account_balance=100000,
            risk_per_trade=0.02,
            entry_price=100,
            stop_loss_price=95,
            risk_tolerance="moderate",
        )

        assert "position_size" in result
        assert "position_value" in result
        assert "risk_amount" in result
        assert result["position_size"] > 0
        assert result["risk_amount"] == 2000  # 100000 * 0.02

    def test_calculate_stop_loss_percentage(self):
        """Test percentage stop-loss calculation."""
        result = self.service.calculate_stop_loss(
            entry_price=100,
            stop_loss_type="percentage",
            percentage=0.05,
        )

        assert result["stop_loss_price"] == 95.0
        assert result["distance_percentage"] == 5.0

    def test_calculate_take_profit(self):
        """Test take-profit calculation."""
        result = self.service.calculate_take_profit(
            entry_price=100,
            stop_loss_price=95,
            risk_reward_ratio=2.0,
        )

        assert result["take_profit_price"] == 110.0  # 100 + (5 * 2)
        assert result["risk_reward_ratio"] == 2.0

    def test_assess_portfolio_risk(self):
        """Test portfolio risk assessment."""
        positions = [
            {"symbol": "AAPL", "value": 50000, "risk": 1000, "sector": "Technology"},
            {"symbol": "MSFT", "value": 30000, "risk": 600, "sector": "Technology"},
            {"symbol": "JPM", "value": 20000, "risk": 400, "sector": "Finance"},
        ]

        result = self.service.assess_portfolio_risk(positions, 100000)

        assert "total_position_value" in result
        assert "risk_level" in result
        assert result["total_position_value"] == 100000


class TestProhibitedLanguageService:
    """Test prohibited language service."""

    def setup_method(self):
        self.service = ProhibitedLanguageService()

    def test_check_clean_text(self):
        """Test checking clean text."""
        result = self.service.check_text("This stock shows strong fundamentals.")
        assert result.is_clean is True
        assert len(result.violations) == 0

    def test_check_prohibited_guaranteed(self):
        """Test detecting guaranteed returns language."""
        result = self.service.check_text("This stock will provide guaranteed returns.")
        assert result.is_clean is False
        assert len(result.violations) > 0

    def test_check_prohibited_risk_free(self):
        """Test detecting risk-free language."""
        result = self.service.check_text("This is a risk-free investment.")
        assert result.is_clean is False
        assert len(result.violations) > 0

    def test_check_warning_language(self):
        """Test detecting warning language."""
        result = self.service.check_text("Buy now before it's too late!")
        assert len(result.warnings) > 0

    def test_sanitize_text(self):
        """Test text sanitization."""
        sanitized = self.service.sanitize_text(
            "This stock offers guaranteed returns with no risk."
        )
        assert "[REDACTED]" in sanitized
        assert "guaranteed returns" not in sanitized.lower()


class TestInvestorSuitabilityService:
    """Test investor suitability service."""

    def setup_method(self):
        self.service = InvestorSuitabilityService()

    def test_check_suitable_recommendation(self):
        """Test suitable recommendation check."""
        user_profile = {
            "risk_tolerance": "moderate",
            "investment_horizon": "medium",
            "available_capital": 100000,
        }

        recommendation = {
            "symbol": "AAPL",
            "risk_level": "medium",
            "time_horizon": "medium",
            "entry_price": 150,
        }

        result = self.service.check_recommendation_suitability(
            user_profile, recommendation
        )

        assert result["suitable"] is True
        assert result["level"] == "suitable"

    def test_check_high_risk_for_conservative(self):
        """Test high risk recommendation for conservative investor."""
        user_profile = {
            "risk_tolerance": "conservative",
            "investment_horizon": "short",
            "available_capital": 100000,
        }

        recommendation = {
            "symbol": "TSLA",
            "risk_level": "very_high",
            "time_horizon": "long",
            "entry_price": 200,
        }

        result = self.service.check_recommendation_suitability(
            user_profile, recommendation
        )

        assert result["suitable"] is False
        assert result["level"] == "not_suitable"
        assert len(result["issues"]) > 0

    def test_get_suitability_summary(self):
        """Test suitability summary."""
        user_profile = {
            "risk_tolerance": "moderate",
            "investment_horizon": "medium",
            "available_capital": 100000,
        }

        recommendations = [
            {"symbol": "AAPL", "risk_level": "low", "time_horizon": "short"},
            {"symbol": "TSLA", "risk_level": "very_high", "time_horizon": "long"},
        ]

        result = self.service.get_suitability_summary(
            user_profile, recommendations
        )

        assert result["total"] == 2
        assert "suitable" in result
        assert "not_suitable" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
