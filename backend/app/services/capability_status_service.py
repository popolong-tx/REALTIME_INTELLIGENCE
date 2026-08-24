"""Truthful module maturity and readiness reporting."""

from datetime import datetime, timezone
import importlib.util
from typing import Any, Dict

from app.core.config import settings
from app.core.database import check_cache_connection, check_db_connection
from app.services.broker.longport_service import longport_service
from app.services.emergency_shutdown_service import emergency_shutdown_service


def capability(
    status: str,
    *,
    persistence: str,
    reason: str,
    dependencies: list[str] | None = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "persistence": persistence,
        "reason": reason,
        "dependencies": dependencies or [],
    }


async def build_readiness_report() -> Dict[str, Any]:
    """Build a module-level report without masking optional configuration gaps."""
    database_ok = check_db_connection()
    cache_ok = check_cache_connection()
    control = await emergency_shutdown_service.get_current_status()
    mutations_blocked = not control["is_operational"]
    grok_configured = bool(
        settings.OCI_GENAI_API_KEY and settings.OCI_GENAI_BASE_URL
    )
    live_broker_enabled = (
        settings.EXECUTION_MODE == "live"
        and settings.BROKER_LIVE_TRADING_ENABLED
    )
    xgboost_available = importlib.util.find_spec("xgboost") is not None

    modules = {
        "market_research": capability(
            "operational" if settings.YAHOO_FINANCE_ENABLED else "configuration_required",
            persistence="provider_cache",
            reason="Yahoo Finance 行情、历史价格、技术指标和财务数据适配器已启用。"
            if settings.YAHOO_FINANCE_ENABLED
            else "当前没有启用市场数据适配器。",
            dependencies=["yahoo_finance"],
        ),
        "grok_intelligence": capability(
            "operational" if grok_configured else "configuration_required",
            persistence="database_monitor_history",
            reason="OCI Responses 密钥和服务地址已配置。"
            if grok_configured
            else "实时 X/Web 检索需要配置 OCI_GENAI_API_KEY 和 OCI_GENAI_BASE_URL。",
            dependencies=["oci_responses", "x_search", "web_search", "code_interpreter"],
        ),
        "intelligence_scheduler": capability(
            "operational",
            persistence="database",
            reason="定时监控和执行历史已持久化；当前仍是单进程调度，未启用多实例租约。",
            dependencies=["sqlite", "single_process_scheduler"],
        ),
        "recommendations": capability(
            "blocked" if mutations_blocked else "operational",
            persistence="database_history",
            reason="当前被紧急停用策略阻断。"
            if mutations_blocked
            else "推荐和分阶段计划计算在服务端真实执行。",
        ),
        "saved_plans": capability(
            "blocked" if mutations_blocked else "operational",
            persistence="database",
            reason="计划版本和冻结状态已保存到服务端数据库。"
            if not mutations_blocked
            else "仍可读取计划，但变更操作已被紧急停用策略阻断。",
        ),
        "model_training": capability(
            "blocked" if mutations_blocked else "operational",
            persistence="database_and_artifact",
            reason="训练、微调和评估会使用准备后的市场数据集真实执行。"
            if not mutations_blocked
            else "模型操作已被紧急停用策略阻断。",
            dependencies=["scikit_learn", "model_artifact_store"],
        ),
        "model_xgboost": capability(
            "operational" if xgboost_available else "configuration_required",
            persistence="optional_runtime_dependency",
            reason="XGBoost 可选运行依赖已安装。"
            if xgboost_available
            else "线性回归和随机森林可用；使用 XGBoost 模板前需安装可选依赖。",
            dependencies=["xgboost"],
        ),
        "audit_trail": capability(
            "operational" if database_ok else "unavailable",
            persistence="database",
            reason="审计事件已写入 audit_events 数据表。"
            if database_ok
            else "数据库连接失败。",
        ),
        "webhooks": capability(
            "operational" if database_ok else "unavailable",
            persistence="database",
            reason="Webhook 配置和投递记录已持久化。"
            if database_ok
            else "数据库连接失败。",
        ),
        "broker_execution": capability(
            "operational" if live_broker_enabled else "simulation_only",
            persistence="external_broker",
            reason="服务端已显式启用实盘订单变更。"
            if live_broker_enabled
            else "服务端策略会拒绝真实下单和撤单请求。",
            dependencies=["longport"] if live_broker_enabled else [],
        ),
        "workspace_customization": capability(
            "local_only",
            persistence="browser_and_manifest",
            reason="工作区、成员关系和租户隔离仍处于模板预览阶段。",
        ),
    }

    core_healthy = database_ok and cache_ok
    overall_status = (
        "degraded"
        if not core_healthy
        else "blocked"
        if mutations_blocked
        else "healthy"
    )
    return {
        "status": overall_status,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checks": {
            "database": database_ok,
            "cache": cache_ok,
            "emergency_gate": control,
        },
        "modules": modules,
        "integrations": {
            "oci_grok": {
                "status": "operational" if grok_configured else "configuration_required",
                "configured": grok_configured,
                "model": settings.OCI_GROK_MODEL_ID,
                "multi_agent_model": settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
                "region": settings.OCI_REGION,
                "tools": ["web_search", "x_search", "code_interpreter"],
            },
            "longport": {
                "status": "configured" if longport_service.access_token else "configuration_required",
                "configured": bool(longport_service.access_token),
                "execution_mode": settings.EXECUTION_MODE,
                "order_mutations_enabled": live_broker_enabled,
                "server_policy_enforced": True,
            },
        },
    }
