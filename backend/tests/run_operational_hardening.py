"""Dependency-free regression runner for operational hardening checks."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from app.core.database import init_db
from app.main_ui import app
from app.services.audit_trail_service import AuditEventType, AuditTrailService
from app.services.model_fine_tuning_service import model_fine_tuning_service
from app.services.model_training_service import model_training_service
from app.services.trading_plan_service import TradingPlanService
from app.services.training_data_service import training_data_service
from app.services.webhook_service import WebhookEventType, WebhookService


def synthetic_training_data():
    return {
        "symbol": "TEST",
        "features": ["feature_a", "feature_b"],
        "prepared_at": "2026-08-24T00:00:00Z",
        "data": {
            "X_train": [[1.0, 2.0], [2.0, 3.0], [3.0, 5.0], [4.0, 7.0]],
            "X_val": [[5.0, 8.0], [6.0, 9.0]],
            "X_test": [[7.0, 11.0], [8.0, 12.0]],
            "y_train": [0.01, 0.02, 0.03, 0.04],
            "y_val": [0.05, 0.06],
            "y_test": [0.07, 0.08],
        },
    }


class OperationalHardeningTests(unittest.TestCase):
    def test_simulation_policy_blocks_live_order(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/broker/order",
                json={
                    "symbol": "AAPL",
                    "side": "Buy",
                    "order_type": "Market",
                    "quantity": 1,
                },
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["detail"]["code"], "simulation_only")
            broker = client.get("/api/v1/broker/brokers").json()
            self.assertFalse(broker["order_mutations_enabled"])

    def test_emergency_shutdown_blocks_and_recovers(self):
        with TestClient(app) as client:
            initiated = client.post(
                "/api/v1/governance/shutdown/initiate",
                json={
                    "reason": "manual_test",
                    "description": "Regression test",
                    "affected_systems": ["recommendations", "models"],
                },
            )
            self.assertEqual(initiated.status_code, 200)
            blocked_plan = client.post(
                "/api/v1/recommendations/generate-plan",
                json={"symbol": "AAPL", "user_profile": {}},
            )
            self.assertEqual(blocked_plan.status_code, 503)
            blocked_model = client.post(
                "/api/v1/models/",
                json={"name": "blocked", "model_type": "linear_regression"},
            )
            self.assertEqual(blocked_model.status_code, 503)
            recovered = client.post("/api/v1/governance/shutdown/recover")
            self.assertEqual(recovered.status_code, 200)
            self.assertEqual(recovered.json()["status"], "active")

    def test_durable_audit_webhook_and_plan(self):
        init_db()
        event = asyncio.run(
            AuditTrailService().log_event(
                AuditEventType.SYSTEM_EVENT,
                user_id="test_user",
                action="persistence_probe",
            )
        )
        queried = asyncio.run(AuditTrailService().get_audit_events(user_id="test_user"))
        self.assertTrue(any(item["id"] == event["id"] for item in queried["events"]))

        webhook = WebhookService().create_webhook(
            name="persistent hook",
            url="https://example.invalid/hook",
            events=[WebhookEventType.SYSTEM_EVENT],
        )
        self.assertEqual(WebhookService().get_webhook(webhook.id).name, "persistent hook")

        plan = TradingPlanService().create_plan(
            workspace_id="test-workspace",
            symbol="AAPL",
            evidence_status="checked",
            user_plan={"symbol": "AAPL", "thesis": "test"},
            generated_plan={"phases": []},
        )
        restored = TradingPlanService().list_plans("test-workspace")
        self.assertTrue(any(item["id"] == plan["id"] for item in restored))

    def test_model_evaluation_and_fine_tuning_are_real(self):
        async def fake_prepare_training_data(*args, **kwargs):
            return synthetic_training_data()

        with tempfile.TemporaryDirectory(prefix="quant-model-test-") as directory:
            with patch.object(
                training_data_service,
                "prepare_training_data",
                side_effect=fake_prepare_training_data,
            ), patch.object(model_training_service, "models_dir", directory), patch.object(
                model_fine_tuning_service, "models_dir", directory
            ):
                with TestClient(app) as client:
                    created = client.post(
                        "/api/v1/models/",
                        json={"name": "real execution probe", "model_type": "linear_regression"},
                    )
                    self.assertEqual(created.status_code, 200)
                    model_id = created.json()["id"]
                    trained = client.post(
                        f"/api/v1/models/{model_id}/train",
                        json={"symbol": "TEST", "prediction_horizon": 1},
                    )
                    self.assertEqual(trained.status_code, 200, trained.text)
                    evaluated = client.post(
                        f"/api/v1/models/{model_id}/evaluate",
                        json={"symbol": "TEST", "prediction_horizon": 1},
                    )
                    self.assertEqual(evaluated.status_code, 200, evaluated.text)
                    self.assertEqual(evaluated.json()["status"], "evaluated")
                    tuned = client.post(
                        f"/api/v1/models/{model_id}/fine-tune",
                        json={
                            "symbol": "TEST",
                            "prediction_horizon": 1,
                            "param_grid": {"fit_intercept": [True, False]},
                            "cv": 2,
                        },
                    )
                    self.assertEqual(tuned.status_code, 200, tuned.text)
                    self.assertEqual(tuned.json()["status"], "fine_tuned")

    def test_status_reports_module_maturity(self):
        with TestClient(app) as client:
            response = client.get("/api/v1/status")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["features"]["audit_trail"]["status"], "operational")
            self.assertEqual(payload["features"]["saved_plans"]["persistence"], "database")
            self.assertEqual(payload["features"]["broker_execution"]["status"], "simulation_only")
            self.assertTrue(payload["integrations"]["longport"]["server_policy_enforced"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
