"""Regression tests for the functionality gaps found in the runtime audit."""

import asyncio
from contextlib import contextmanager

import numpy as np
from fastapi.testclient import TestClient

from app.core.database import init_db
from app.core.config import settings
from app.main_ui import app
from app.services.audit_trail_service import (
    AuditEventType,
    AuditTrailService,
)
from app.services.model_fine_tuning_service import model_fine_tuning_service
from app.services.model_training_service import model_training_service
from app.services.trading_plan_service import TradingPlanService
from app.services.webhook_service import (
    WebhookEventType,
    WebhookService,
)


@contextmanager
def authenticated_client():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.APP_LOGIN_USERNAME,
                "password": settings.APP_LOGIN_PASSWORD,
            },
        )
        assert response.status_code == 200, response.text
        yield client


def synthetic_training_data():
    X_train = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 5.0], [4.0, 7.0]])
    X_val = np.array([[5.0, 8.0], [6.0, 9.0]])
    X_test = np.array([[7.0, 11.0], [8.0, 12.0]])
    y_train = np.array([0.01, 0.02, 0.03, 0.04])
    y_val = np.array([0.05, 0.06])
    y_test = np.array([0.07, 0.08])
    return {
        "symbol": "TEST",
        "features": ["feature_a", "feature_b"],
        "prepared_at": "2026-08-24T00:00:00Z",
        "data": {
            "X_train": X_train.tolist(),
            "X_val": X_val.tolist(),
            "X_test": X_test.tolist(),
            "y_train": y_train.tolist(),
            "y_val": y_val.tolist(),
            "y_test": y_test.tolist(),
        },
    }


def test_simulation_policy_blocks_live_order_and_is_reported():
    with authenticated_client() as client:
        response = client.post(
            "/api/v1/broker/order",
            json={
                "symbol": "AAPL",
                "side": "Buy",
                "order_type": "Market",
                "quantity": 1,
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "simulation_only"

        broker = client.get("/api/v1/broker/brokers").json()
        assert broker["execution_mode"] == "simulation_only"
        assert broker["order_mutations_enabled"] is False


def test_emergency_shutdown_blocks_mutations_and_recovery_restores_gate():
    with authenticated_client() as client:
        initiated = client.post(
            "/api/v1/governance/shutdown/initiate",
            json={
                "reason": "manual_test",
                "description": "Regression test",
                "affected_systems": ["recommendations", "models"],
            },
        )
        assert initiated.status_code == 200

        blocked_plan = client.post(
            "/api/v1/recommendations/generate-plan",
            json={"symbol": "AAPL", "user_profile": {}},
        )
        assert blocked_plan.status_code == 503
        assert blocked_plan.json()["detail"]["code"] == "emergency_shutdown"

        blocked_model = client.post(
            "/api/v1/models/",
            json={"name": "blocked", "model_type": "linear_regression"},
        )
        assert blocked_model.status_code == 503

        recovered = client.post("/api/v1/governance/shutdown/recover")
        assert recovered.status_code == 200
        assert recovered.json()["status"] == "active"


def test_audit_webhook_and_plan_records_survive_service_reinstantiation():
    init_db()
    audit = AuditTrailService()
    event = asyncio.run(
        audit.log_event(
            AuditEventType.SYSTEM_EVENT,
            user_id="test_user",
            action="persistence_probe",
        )
    )
    queried = asyncio.run(AuditTrailService().get_audit_events(user_id="test_user"))
    assert any(item["id"] == event["id"] for item in queried["events"])

    webhook = WebhookService().create_webhook(
        name="persistent hook",
        url="https://example.invalid/hook",
        events=[WebhookEventType.SYSTEM_EVENT],
    )
    restored_webhook = WebhookService().get_webhook(webhook.id)
    assert restored_webhook is not None
    assert restored_webhook.name == "persistent hook"

    created_plan = TradingPlanService().create_plan(
        workspace_id="test-workspace",
        symbol="AAPL",
        evidence_status="checked",
        user_plan={"symbol": "AAPL", "thesis": "test"},
        generated_plan={"phases": []},
    )
    restored_plans = TradingPlanService().list_plans("test-workspace")
    assert any(plan["id"] == created_plan["id"] for plan in restored_plans)


def test_model_evaluation_and_fine_tuning_execute_real_services(monkeypatch, tmp_path):
    async def fake_prepare_training_data(*args, **kwargs):
        return synthetic_training_data()

    from app.services.training_data_service import training_data_service

    monkeypatch.setattr(
        training_data_service,
        "prepare_training_data",
        fake_prepare_training_data,
    )
    monkeypatch.setattr(model_training_service, "models_dir", str(tmp_path))
    monkeypatch.setattr(model_fine_tuning_service, "models_dir", str(tmp_path))

    with authenticated_client() as client:
        created = client.post(
            "/api/v1/models/",
            json={"name": "real execution probe", "model_type": "linear_regression"},
        )
        assert created.status_code == 200
        model_id = created.json()["id"]

        trained = client.post(
            f"/api/v1/models/{model_id}/train",
            json={"symbol": "TEST", "prediction_horizon": 1},
        )
        assert trained.status_code == 200
        assert trained.json()["status"] == "trained"

        evaluated = client.post(
            f"/api/v1/models/{model_id}/evaluate",
            json={"symbol": "TEST", "prediction_horizon": 1},
        )
        assert evaluated.status_code == 200
        assert evaluated.json()["status"] == "evaluated"
        assert evaluated.json()["sample_count"] == 2

        tuned = client.post(
            f"/api/v1/models/{model_id}/fine-tune",
            json={
                "symbol": "TEST",
                "prediction_horizon": 1,
                "param_grid": {"fit_intercept": [True, False]},
                "cv": 2,
            },
        )
        assert tuned.status_code == 200
        assert tuned.json()["status"] == "fine_tuned"
        assert "best_params" in tuned.json()


def test_status_exposes_module_maturity_instead_of_boolean_flags():
    with authenticated_client() as client:
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["features"]["authentication"]["status"] == "operational"
        assert payload["features"]["audit_trail"]["status"] == "operational"
        assert payload["features"]["saved_plans"]["persistence"] == "database"
        assert payload["features"]["broker_execution"]["status"] == "simulation_only"
        assert payload["integrations"]["longport"]["server_policy_enforced"] is True
