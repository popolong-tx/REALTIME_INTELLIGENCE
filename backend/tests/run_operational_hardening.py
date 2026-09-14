"""Dependency-free regression runner for operational hardening checks."""

import asyncio
from contextlib import contextmanager
from io import BytesIO
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.core.database import SessionLocal, init_db
from app.core.config import settings
from app.main_ui import app
from app.models.intelligence_monitoring import IntelligenceAnalysisRecord
from app.services.audit_trail_service import AuditEventType, AuditTrailService
from app.services.model_fine_tuning_service import model_fine_tuning_service
from app.services.model_training_service import model_training_service
from app.services.trading_plan_service import TradingPlanService
from app.services.training_data_service import training_data_service
from app.services.webhook_service import WebhookEventType, WebhookService
from app.services.intelligence_pdf_service import intelligence_pdf_service
from app.services.intelligence_report_artifact_service import (
    intelligence_report_artifact_service,
)
from app.services.institutional_intelligence_service import institutional_intelligence_service
from app.services.intelligence_monitoring_service import IntelligenceMonitoringService
from app.services.data_sources.twelve_data import twelve_data_service


@contextmanager
def authenticated_client():
    """Create a client with the same server-side configured test account as the UI."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.APP_LOGIN_USERNAME,
                "password": settings.APP_LOGIN_PASSWORD,
            },
        )
        if response.status_code != 200:
            raise AssertionError(f"Test login failed: {response.status_code} {response.text}")
        yield client


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


def intelligence_pdf_sample(workflow):
    analyses = {
        "realtime-research": {
            "executive_summary": "公开信息显示项目关注度上升，但仍需核验来源与时间窗口。",
            "coverage_note": "按关键词与日期尽力覆盖，不代表平台全量数据。",
            "trends": [{"label": "政策关注", "direction": "rising", "evidence": "两条公开来源提及", "source_refs": ["S1"]}],
            "items": [{"source_type": "public", "title": "公开政策更新", "author": "示例机构", "published_at": "2026-08-24", "content_excerpt": "政策进入公开征求意见阶段。", "url": "https://example.com/policy", "evidence_status": "source_available"}],
            "unknowns": ["正式实施时间尚未确认"],
        },
        "project-risk": {
            "executive_summary": "项目总体风险中等，社会沟通与许可节奏需要专项复核。",
            "direct_assessment": "不能忽视社区沟通延迟对项目进度和声誉的叠加影响。",
            "overall_risk": "moderate",
            "risk_dimensions": [{"dimension": "social", "label": "社会与社区", "score": 58, "level": "moderate", "trend": "rising", "rationale": "新增公开关注"}],
            "events": [{"title": "社区公开会议", "observed_at": "2026-08-24", "evidence_status": "verified_source", "impact": "需要补充沟通计划", "source_refs": ["S1"]}],
            "decision_options": [{"action": "pause_for_review", "urgency": "7_days", "owner": "风险团队", "trigger": "许可延迟超过七天", "rationale": "控制进度和声誉风险"}],
            "watch_items": ["许可更新时间"],
            "assumptions": ["公开会议记录完整"],
        },
        "geopolitical-impact": {
            "executive_summary": "区域融资竞争可能改变联合融资伙伴结构和项目排序。",
            "direct_assessment": "最容易被低估的是合作伙伴退出后的风险转移。",
            "transmission_paths": [{"driver": "政策调整", "mechanism": "资本成本变化", "financing_effect": "联合融资比例下降", "affected_parties": ["国家/地区", "融资伙伴"], "evidence_status": "sourced"}],
            "scenarios": [{"name": "baseline", "probability": "medium", "pipeline_impact": "保持审慎推进", "cofinancing_impact": "伙伴结构调整", "borrowing_appetite": "基本稳定", "feasibility": "需复核", "risk_transfer": "部分转移至担保方", "early_signals": ["伙伴公开表态"]}],
            "decision_options": [{"action": "调整联合融资组合", "upside": "降低单一伙伴依赖", "downside": "谈判周期延长", "owner": "战略团队", "timing": "本季度", "trigger": "伙伴条款发生变化"}],
            "assumptions": ["现有政策延续"],
            "unknowns": ["国家/地区正式借贷意愿"],
        },
    }
    return {
        "status": "live",
        "workflow": workflow,
        "evidence_quality": "cited",
        "coverage": "best_effort",
        "analysis": analyses[workflow],
        "items": analyses[workflow].get("items", []),
        "counts": {"x": 0, "public": 1, "citations": 1},
        "evidence": [{"id": "S1", "title": "公开来源", "excerpt": "用于验证 PDF 来源账本。", "url": "https://example.com/source", "source_type": "public", "verification_status": "source_available"}],
        "audit": {"provider": "test-provider", "model": "xai.grok-test", "region": "test-region", "request_id": f"pdf-{workflow}", "generated_at": "2026-08-24T08:00:00Z", "workspace_id": "test-workspace", "tools": ["web_search"], "requested_tools": ["web_search", "x_search"], "degraded_tools": ["x_search"], "coverage": "best_effort"},
        "warnings": ["测试报告仅用于验证导出功能。"],
    }


class OperationalHardeningTests(unittest.TestCase):
    def test_overseas_securities_provider_is_real_and_truthful(self):
        async def fake_twelve_request(endpoint, params):
            if endpoint == "/symbol_search":
                return {
                    "data": [{
                        "symbol": "QATEST",
                        "instrument_name": "QA Global Equity",
                        "exchange": "NASDAQ",
                        "mic_code": "XNAS",
                        "country": "United States",
                        "currency": "USD",
                        "instrument_type": "Common Stock",
                        "access": {"global": "Basic"},
                    }]
                }
            if endpoint == "/quote":
                return {
                    "symbol": "QATEST",
                    "name": "QA Global Equity",
                    "exchange": "NASDAQ",
                    "mic_code": "XNAS",
                    "country": "United States",
                    "currency": "USD",
                    "datetime": "2026-08-25",
                    "open": "100.0",
                    "high": "103.0",
                    "low": "99.5",
                    "close": "102.0",
                    "previous_close": "100.0",
                    "change": "2.0",
                    "percent_change": "2.0",
                    "volume": "123456",
                    "is_market_open": False,
                }
            if endpoint == "/time_series":
                return {
                    "meta": {
                        "symbol": "QATEST",
                        "exchange": "NASDAQ",
                        "mic_code": "XNAS",
                        "currency": "USD",
                        "exchange_timezone": "America/New_York",
                    },
                    "values": [
                        {"datetime": "2026-08-22", "open": "99", "high": "101", "low": "98", "close": "100", "volume": "1000"},
                        {"datetime": "2026-08-25", "open": "100", "high": "103", "low": "99.5", "close": "102", "volume": "123456"},
                    ],
                }
            raise AssertionError(f"Unexpected Twelve Data endpoint: {endpoint}")

        with authenticated_client() as client:
            with patch.object(twelve_data_service, "api_key", None):
                providers = client.get("/api/v1/overseas-securities/providers")
                self.assertEqual(providers.status_code, 200)
                self.assertFalse(providers.json()["providers"][0]["configured"])
                unconfigured = client.get("/api/v1/overseas-securities/QATEST/quote")
                self.assertEqual(unconfigured.status_code, 503)
                self.assertIn("TWELVE_DATA_API_KEY", unconfigured.text)

            with patch.object(twelve_data_service, "api_key", "qa-provider-secret"), patch.object(
                twelve_data_service, "_request", side_effect=fake_twelve_request
            ):
                found = client.get("/api/v1/overseas-securities/search?q=QA")
                self.assertEqual(found.status_code, 200, found.text)
                self.assertEqual(found.json()["results"][0]["mic_code"], "XNAS")

                quote = client.get("/api/v1/overseas-securities/QATEST/quote")
                self.assertEqual(quote.status_code, 200, quote.text)
                self.assertEqual(quote.json()["source"], "twelve_data")
                self.assertEqual(quote.json()["current_price"], 102.0)

                history = client.get(
                    "/api/v1/overseas-securities/QATEST/historical?period=1mo&interval=1d"
                )
                self.assertEqual(history.status_code, 200, history.text)
                self.assertEqual(history.json()["data"][-1]["close"], 102.0)
                self.assertNotIn("qa-provider-secret", found.text + quote.text + history.text)

    def test_environment_login_protects_ui_and_business_api(self):
        self.assertTrue(settings.APP_LOGIN_USERNAME)
        self.assertTrue(settings.APP_LOGIN_PASSWORD)
        self.assertTrue(settings.AUTH_SESSION_SECRET)
        with TestClient(app) as client:
            root = client.get("/", follow_redirects=False)
            self.assertEqual(root.status_code, 303)
            self.assertTrue(root.headers["location"].startswith("/login?next="))
            self.assertEqual(client.get("/api/v1/status").status_code, 401)
            login_page = client.get("/login")
            self.assertEqual(login_page.status_code, 200)
            self.assertIn("登录系统", login_page.text)
            self.assertNotIn(str(settings.APP_LOGIN_PASSWORD), login_page.text)

            rejected = client.post(
                "/api/v1/auth/login",
                json={"username": settings.APP_LOGIN_USERNAME, "password": "incorrect"},
            )
            self.assertEqual(rejected.status_code, 401)
            self.assertNotIn(str(settings.APP_LOGIN_PASSWORD), rejected.text)

            accepted = client.post(
                "/api/v1/auth/login",
                json={
                    "username": settings.APP_LOGIN_USERNAME,
                    "password": settings.APP_LOGIN_PASSWORD,
                },
            )
            self.assertEqual(accepted.status_code, 200, accepted.text)
            cookie = accepted.headers.get("set-cookie", "").lower()
            self.assertIn("httponly", cookie)
            self.assertIn("samesite=lax", cookie)
            self.assertNotIn(str(settings.APP_LOGIN_PASSWORD).lower(), cookie)
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/api/v1/auth/status").json()["username"], settings.APP_LOGIN_USERNAME)

            logged_out = client.post("/api/v1/auth/logout")
            self.assertEqual(logged_out.status_code, 200)
            self.assertEqual(client.get("/", follow_redirects=False).status_code, 303)

    def test_intelligence_outputs_require_chinese_and_preserve_x_original(self):
        realtime_prompt = institutional_intelligence_service._realtime_research_prompt(
            {
                "query": "区域项目风险",
                "keywords": ["项目"],
                "source_channels": ["x", "web"],
                "preserve_x_original": True,
                "max_results": 10,
            },
            "2026-08-24",
            "2026-08-25",
        )
        project_prompt = institutional_intelligence_service._project_risk_prompt({
            "country": "示例国家/地区",
            "project_name": "清洁能源项目",
            "product_type": "主权贷款",
            "window_days": 7,
        })
        geopolitical_prompt = institutional_intelligence_service._geopolitical_prompt({
            "issue": "区域融资政策变化",
            "regions": ["东南亚"],
            "actors": [],
            "product_types": [],
            "horizon": "一年",
            "window_days": 30,
        })
        for prompt in (realtime_prompt, project_prompt, geopolitical_prompt):
            self.assertIn("所有面向用户的文字必须使用简体中文", prompt)

        original_x_text = "Markets remain cautious after the policy announcement."
        result = {
            "status": "live",
            "workflow": "realtime-research",
            "analysis": {
                "executive_summary": "Markets remain cautious and financing conditions are tightening.",
                "items": [{
                    "source_type": "x",
                    "title": "Market update from an official account",
                    "original_text": original_x_text,
                    "content_excerpt": "The post says financing conditions may tighten.",
                }],
            },
            "evidence": [{
                "source_type": "public",
                "title": "Official policy announcement",
                "excerpt": "The policy will enter into force next month.",
                "url": "https://example.com/policy",
            }],
            "audit": {},
            "warnings": ["Provider returned an incomplete public-web result."],
        }
        checked = asyncio.run(institutional_intelligence_service._ensure_simplified_chinese(result))
        self.assertEqual(checked["analysis"]["items"][0]["original_text"], original_x_text)
        self.assertEqual(checked["analysis"]["items"][0]["title"], "Market update from an official account")
        self.assertEqual(
            checked["analysis"]["items"][0]["content_excerpt"],
            "The post says financing conditions may tighten.",
        )
        self.assertEqual(
            checked["analysis"]["executive_summary"],
            "Markets remain cautious and financing conditions are tightening.",
        )
        self.assertEqual(checked["audit"]["language"], "zh-CN")
        self.assertFalse(checked["audit"]["language_compliant"])
        self.assertGreater(checked["audit"]["english_fields_detected"], 0)
        self.assertEqual(checked["status"], "live")
        self.assertNotIn("请重新运行", str(checked))
        self.assertNotIn("blocked_english_fields", checked["audit"])

    def test_intelligence_pdf_export_is_real_and_governed(self):
        contexts = {
            "realtime-research": {"query": "区域项目政策", "keywords": ["项目", "政策"], "workspace_id": "test-workspace"},
            "project-risk": {"country": "示例国家/地区", "project_name": "清洁能源项目", "window_days": 7, "workspace_id": "test-workspace"},
            "geopolitical-impact": {"issue": "区域融资政策变化", "regions": ["东南亚"], "horizon": "one_year", "workspace_id": "test-workspace"},
        }
        for workflow, context in contexts.items():
            report = intelligence_pdf_service.generate(workflow, intelligence_pdf_sample(workflow), context)
            self.assertTrue(report.content.startswith(b"%PDF-"))
            self.assertGreater(len(report.content), 1000)
            reader = PdfReader(BytesIO(report.content))
            self.assertGreaterEqual(len(reader.pages), 2)
            self.assertIn("GROK DEMO", "".join(page.extract_text() or "" for page in reader.pages))

        with authenticated_client() as client:
            response = client.post(
                "/api/v1/intelligence/export/pdf",
                json={
                    "workflow": "project-risk",
                    "result": intelligence_pdf_sample("project-risk"),
                    "query_context": contexts["project-risk"],
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["content-type"], "application/pdf")
            self.assertIn("filename*=UTF-8", response.headers["content-disposition"])
            self.assertTrue(response.content.startswith(b"%PDF-"))

            rejected = intelligence_pdf_sample("project-risk")
            rejected["status"] = "configuration_required"
            invalid = client.post(
                "/api/v1/intelligence/export/pdf",
                json={"workflow": "project-risk", "result": rejected, "query_context": {}},
            )
            self.assertEqual(invalid.status_code, 422)

    def test_scheduled_monitor_generates_persistent_pdf_report(self):
        init_db()
        workspace_id = f"scheduled-pdf-{uuid4()}"
        service = IntelligenceMonitoringService()
        monitor_ids = []
        with tempfile.TemporaryDirectory(prefix="intelligence-reports-") as directory, patch.object(
            intelligence_report_artifact_service,
            "reports_dir",
            Path(directory),
        ):
            try:
                with SessionLocal() as db:
                    monitor = service.create_monitor(
                        db,
                        workspace_id=workspace_id,
                        monitor_type="realtime_research",
                        name="定时报告回归验证",
                        schedule_minutes=30,
                        request_payload={
                            "query": "区域项目政策",
                            "keywords": ["项目", "政策"],
                            "source_channels": ["web"],
                            "use_code_interpreter": True,
                            "preserve_x_original": True,
                            "max_results": 10,
                            "workspace_id": workspace_id,
                        },
                    )
                    monitor_ids.append(monitor.id)

                live_result = intelligence_pdf_sample("realtime-research")
                live_result["audit"] = {
                    **live_result["audit"],
                    "request_id": f"scheduled-{uuid4()}",
                    "workspace_id": workspace_id,
                }
                with patch.object(
                    institutional_intelligence_service,
                    "search_realtime_information",
                    return_value=live_result,
                ):
                    execution = asyncio.run(service.execute_monitor(monitor.id, trigger="schedule"))

                self.assertEqual(execution["run"]["trigger"], "schedule")
                self.assertEqual(execution["report_generation"]["status"], "generated")
                self.assertEqual(execution["history_save"]["status"], "saved")
                self.assertEqual(execution["history_record"]["trigger"], "schedule")
                report = execution["run"]["report"]
                self.assertIsNotNone(report)
                self.assertEqual(execution["monitor"]["latest_report"]["id"], report["id"])

                with authenticated_client() as client:
                    listed = client.get(
                        "/api/v1/intelligence/reports",
                        params={"workspace_id": workspace_id, "monitor_id": monitor.id},
                    )
                    self.assertEqual(listed.status_code, 200, listed.text)
                    self.assertEqual(len(listed.json()["items"]), 1)
                    history = client.get(
                        "/api/v1/intelligence/history",
                        params={"workspace_id": workspace_id, "workflow": "realtime-research"},
                    )
                    self.assertEqual(history.status_code, 200, history.text)
                    self.assertEqual(len(history.json()["items"]), 1)
                    self.assertEqual(history.json()["items"][0]["run_id"], execution["run"]["id"])
                    downloaded = client.get(
                        f"/api/v1/intelligence/reports/{report['id']}/download",
                        params={"workspace_id": workspace_id},
                    )
                    self.assertEqual(downloaded.status_code, 200, downloaded.text)
                    self.assertEqual(downloaded.headers["content-type"], "application/pdf")
                    self.assertEqual(downloaded.headers["x-report-sha256"], report["sha256"])
                    self.assertTrue(downloaded.content.startswith(b"%PDF-"))
                    cross_workspace = client.get(
                        f"/api/v1/intelligence/reports/{report['id']}/download",
                        params={"workspace_id": "another-workspace"},
                    )
                    self.assertEqual(cross_workspace.status_code, 404)

                with SessionLocal() as db:
                    unconfigured = service.create_monitor(
                        db,
                        workspace_id=workspace_id,
                        monitor_type="realtime_research",
                        name="未配置不生成报告",
                        schedule_minutes=30,
                        request_payload={
                            "query": "不应生成假报告",
                            "keywords": [],
                            "source_channels": ["web"],
                            "use_code_interpreter": False,
                            "preserve_x_original": True,
                            "max_results": 10,
                            "workspace_id": workspace_id,
                        },
                    )
                    monitor_ids.append(unconfigured.id)
                missing_result = {
                    "status": "configuration_required",
                    "workflow": "realtime-research",
                    "analysis": {},
                    "evidence": [],
                    "audit": {"workspace_id": workspace_id},
                }
                with patch.object(
                    institutional_intelligence_service,
                    "search_realtime_information",
                    return_value=missing_result,
                ):
                    skipped = asyncio.run(
                        service.execute_monitor(unconfigured.id, trigger="schedule")
                    )
                self.assertEqual(skipped["report_generation"]["status"], "skipped")
                self.assertEqual(skipped["history_save"]["status"], "skipped")
                self.assertIsNone(skipped["run"]["report"])
            finally:
                with SessionLocal() as db:
                    for monitor_id in monitor_ids:
                        try:
                            service.delete_monitor(db, monitor_id)
                        except Exception:
                            db.rollback()
                    db.query(IntelligenceAnalysisRecord).filter(
                        IntelligenceAnalysisRecord.workspace_id == workspace_id
                    ).delete(synchronize_session=False)
                    db.commit()
                self.assertFalse(list(Path(directory).rglob("*.pdf")))

    def test_three_intelligence_workflows_persist_restore_and_export_history(self):
        init_db()
        workspace_id = f"analysis-history-{uuid4()}"
        cases = [
            (
                "realtime-research",
                "/api/v1/intelligence/realtime/search",
                "search_realtime_information",
                {
                    "query": "区域项目政策变化",
                    "keywords": ["项目", "政策"],
                    "source_channels": ["x", "web"],
                    "use_code_interpreter": True,
                    "preserve_x_original": True,
                    "max_results": 10,
                    "workspace_id": workspace_id,
                },
            ),
            (
                "project-risk",
                "/api/v1/intelligence/project-risk/analyze",
                "analyze_project_risk",
                {
                    "country": "示例国家/地区",
                    "project_name": "清洁能源项目",
                    "product_type": "sovereign_loan",
                    "risk_focus": ["political", "social"],
                    "window_days": 7,
                    "workspace_id": workspace_id,
                },
            ),
            (
                "geopolitical-impact",
                "/api/v1/intelligence/geopolitical-impact/analyze",
                "analyze_geopolitical_impact",
                {
                    "issue": "区域基础设施融资政策变化",
                    "regions": ["东南亚"],
                    "actors": ["金融机构"],
                    "product_types": ["联合融资"],
                    "horizon": "one_year",
                    "window_days": 30,
                    "workspace_id": workspace_id,
                },
            ),
        ]
        record_ids = {}
        try:
            with authenticated_client() as client:
                for workflow, endpoint, method_name, payload in cases:
                    live_result = intelligence_pdf_sample(workflow)
                    live_result["audit"] = {
                        **live_result["audit"],
                        "request_id": f"history-{workflow}-{uuid4()}",
                        "workspace_id": workspace_id,
                    }
                    with patch.object(
                        institutional_intelligence_service,
                        method_name,
                        return_value=live_result,
                    ):
                        created = client.post(endpoint, json=payload)
                    self.assertEqual(created.status_code, 200, created.text)
                    history_record = created.json().get("history_record")
                    self.assertIsNotNone(history_record)
                    self.assertEqual(history_record["workflow"], workflow)
                    record_ids[workflow] = history_record["id"]

                    listed = client.get(
                        "/api/v1/intelligence/history",
                        params={"workspace_id": workspace_id, "workflow": workflow},
                    )
                    self.assertEqual(listed.status_code, 200, listed.text)
                    self.assertEqual(len(listed.json()["items"]), 1)
                    self.assertNotIn("result", listed.json()["items"][0])

                    detail = client.get(
                        f"/api/v1/intelligence/history/{history_record['id']}",
                        params={"workspace_id": workspace_id},
                    )
                    self.assertEqual(detail.status_code, 200, detail.text)
                    self.assertEqual(detail.json()["query_context"]["workspace_id"], workspace_id)
                    self.assertEqual(
                        detail.json()["result"]["analysis"]["executive_summary"],
                        live_result["analysis"]["executive_summary"],
                    )

                    exported = client.get(
                        f"/api/v1/intelligence/history/{history_record['id']}/pdf",
                        params={"workspace_id": workspace_id},
                    )
                    self.assertEqual(exported.status_code, 200, exported.text)
                    self.assertEqual(exported.headers["content-type"], "application/pdf")
                    self.assertEqual(
                        exported.headers["x-intelligence-history-id"],
                        history_record["id"],
                    )
                    self.assertTrue(exported.content.startswith(b"%PDF-"))

                blocked = client.get(
                    f"/api/v1/intelligence/history/{record_ids['project-risk']}",
                    params={"workspace_id": "another-workspace"},
                )
                self.assertEqual(blocked.status_code, 404)
                blocked_pdf = client.get(
                    f"/api/v1/intelligence/history/{record_ids['project-risk']}/pdf",
                    params={"workspace_id": "another-workspace"},
                )
                self.assertEqual(blocked_pdf.status_code, 404)
        finally:
            with SessionLocal() as db:
                db.query(IntelligenceAnalysisRecord).filter(
                    IntelligenceAnalysisRecord.workspace_id == workspace_id
                ).delete(synchronize_session=False)
                db.commit()

    def test_simulation_policy_blocks_live_order(self):
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
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["detail"]["code"], "simulation_only")
            broker = client.get("/api/v1/broker/brokers").json()
            self.assertFalse(broker["order_mutations_enabled"])

    def test_emergency_shutdown_blocks_and_recovers(self):
        with authenticated_client() as client:
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
                with authenticated_client() as client:
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
        with authenticated_client() as client:
            response = client.get("/api/v1/status")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["features"]["audit_trail"]["status"], "operational")
            self.assertEqual(payload["features"]["authentication"]["status"], "operational")
            self.assertEqual(payload["features"]["intelligence_pdf_export"]["status"], "operational")
            self.assertEqual(payload["features"]["intelligence_history"]["status"], "operational")
            self.assertIn(
                payload["features"]["overseas_market_data"]["status"],
                {"operational", "configuration_required"},
            )
            self.assertEqual(
                payload["integrations"]["overseas_securities"]["provider"],
                "twelve_data",
            )
            self.assertEqual(
                payload["features"]["intelligence_history"]["persistence"],
                "workspace_scoped_immutable_database_snapshots",
            )
            self.assertEqual(
                payload["features"]["intelligence_pdf_export"]["persistence"],
                "database_metadata_and_filesystem",
            )
            self.assertIn(
                "reportlab",
                payload["features"]["intelligence_scheduler"]["dependencies"],
            )
            self.assertEqual(payload["features"]["saved_plans"]["persistence"], "database")
            self.assertEqual(payload["features"]["broker_execution"]["status"], "simulation_only")
            self.assertTrue(payload["integrations"]["longport"]["server_policy_enforced"])

        project_root = BACKEND_ROOT.parent
        page = (project_root / "frontend/public/index.html").read_text(encoding="utf-8")
        script = (project_root / "frontend/public/assets/app.js").read_text(encoding="utf-8")
        login_page = (project_root / "frontend/public/login.html").read_text(encoding="utf-8")
        app_styles = (project_root / "frontend/public/assets/app.css").read_text(encoding="utf-8")
        self.assertIn("每次真实检索成功后自动保存 PDF 报告", page)
        self.assertIn("每次真实风险扫描成功后自动保存 PDF 报告", page)
        self.assertIn("download-report", script)
        self.assertIn("/api/v1/intelligence/reports/", script)
        self.assertIn("/api/v1/intelligence/history", script)
        self.assertIn("导出当时记录", script)
        self.assertIn("检索实时公开信息", script)
        self.assertIn("登录系统", login_page)
        self.assertNotIn(str(settings.APP_LOGIN_PASSWORD), login_page)
        self.assertIn("@media (max-width: 920px)", app_styles)
        self.assertIn("@media (max-width: 480px)", app_styles)


if __name__ == "__main__":
    unittest.main(verbosity=2)
