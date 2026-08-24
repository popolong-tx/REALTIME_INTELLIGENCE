import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestStockAPI:
    """Integration tests for stock API endpoints."""

    def test_validate_stock(self):
        """Test stock validation endpoint."""
        response = client.post(
            "/api/v1/stocks/validate",
            json=["AAPL", "INVALID"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] == 2

    def test_autocomplete(self):
        """Test autocomplete endpoint."""
        response = client.get(
            "/api/v1/stocks/autocomplete",
            params={"q": "AA", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    @patch("app.services.stock_info_service.stock_info_service.get_stock_overview")
    def test_get_stock_info(self, mock_get_info):
        """Test get stock info endpoint."""
        mock_get_info.return_value = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": 150.0,
            "market_cap": 2000000000000,
        }

        response = client.get("/api/v1/stocks/AAPL/info")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 150.0


class TestRecommendationAPI:
    """Integration tests for recommendation API endpoints."""

    @patch("app.services.single_stock_recommendation.single_stock_recommendation_service.get_quick_recommendation")
    def test_get_quick_recommendation(self, mock_get_recommendation):
        """Test quick recommendation endpoint."""
        mock_get_recommendation.return_value = {
            "symbol": "AAPL",
            "recommendation": "buy",
            "confidence": 0.85,
            "risk_level": "medium",
        }

        response = client.get("/api/v1/recommendations/quick/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["recommendation"] == "buy"

    @patch("app.services.recommendation_history_service.recommendation_history_service.get_recommendation_history")
    def test_get_recommendation_history(self, mock_get_history):
        """Test recommendation history endpoint."""
        mock_get_history.return_value = {
            "recommendations": [],
            "total": 0,
        }

        response = client.get("/api/v1/recommendations/history")

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data


class TestModelAPI:
    """Integration tests for model API endpoints."""

    def test_list_models(self):
        """Test list models endpoint."""
        response = client.get("/api/v1/models/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("app.models.training.Model")
    def test_create_model(self, mock_model):
        """Test create model endpoint."""
        response = client.post(
            "/api/v1/models/",
            json={
                "name": "Test Model",
                "model_type": "random_forest",
                "hyperparameters": {"n_estimators": 100},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Model"


class TestUserAPI:
    """Integration tests for user API endpoints."""

    def test_get_user_profile(self):
        """Test get user profile endpoint."""
        response = client.get("/api/v1/user/profile")

        assert response.status_code == 200

    def test_update_investment_goals(self):
        """Test update investment goals endpoint."""
        response = client.put(
            "/api/v1/user/goals",
            json={
                "target_return": 15,
                "investment_horizon": "medium",
                "risk_tolerance": "moderate",
                "available_capital": 100000,
                "max_position_size": 20,
                "max_loss_per_trade": 3,
                "preferred_sectors": ["Technology"],
                "excluded_sectors": [],
            },
        )

        assert response.status_code == 200

    def test_export_import_config(self):
        """Test export and import config endpoints."""
        # Export
        export_response = client.get("/api/v1/user/export")
        assert export_response.status_code == 200
        config = export_response.json()

        # Import
        import_response = client.post(
            "/api/v1/user/import",
            json=config,
        )
        assert import_response.status_code == 200


class TestGovernanceAPI:
    """Integration tests for governance API endpoints."""

    def test_get_governance_stats(self):
        """Test get governance stats endpoint."""
        response = client.get("/api/v1/governance/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_models" in data

    def test_get_pending_approvals(self):
        """Test get pending approvals endpoint."""
        response = client.get("/api/v1/governance/pending")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_get_model_aliases(self):
        """Test get model aliases endpoint."""
        response = client.get("/api/v1/governance/aliases")

        assert response.status_code == 200
        data = response.json()
        assert "aliases" in data


class TestSearchAPI:
    """Integration tests for search API endpoints."""

    @patch("app.services.news_service.news_service.search_news")
    def test_search_news(self, mock_search):
        """Test search news endpoint."""
        mock_search.return_value = {
            "news": [],
            "total": 0,
        }

        response = client.get(
            "/api/v1/search/news",
            params={"q": "AAPL", "days": 7},
        )

        assert response.status_code == 200

    @patch("app.services.data_sources.data_aggregator.data_aggregator.get_stock_info")
    def test_search_market_data(self, mock_get_info):
        """Test search market data endpoint."""
        mock_get_info.return_value = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
        }

        response = client.get(
            "/api/v1/search/market",
            params={"symbols": "AAPL"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
