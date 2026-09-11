"""Intelligence-focused capability status reporting."""

from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import settings
from app.core.database import check_cache_connection, check_db_connection
from app.services.emergency_shutdown_service import emergency_shutdown_service
from app.services.login_service import login_service


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
    """Build a module-level report for intelligence-only deployment."""
    database_ok = check_db_connection()
    cache_ok = check_cache_connection()
    control = await emergency_shutdown_service.get_current_status()
    mutations_blocked = not control["is_operational"]
    grok_configured = bool(
        settings.OCI_GENAI_API_KEY and settings.OCI_GENAI_BASE_URL
    )
    pdf_export_available = True  # reportlab is a core dependency

    modules = {
        "authentication": capability(
            "operational" if login_service.configured else "configuration_required",
            persistence="signed_http_only_cookie_and_database_audit",
            reason="登录账号由服务端环境变量配置，会话使用签名 HttpOnly Cookie。"
            if login_service.configured
            else "需要配置 APP_LOGIN_USERNAME、APP_LOGIN_PASSWORD 和 AUTH_SESSION_SECRET。",
            dependencies=["environment_configuration", "signed_session", "audit_trail"],
        ),
        "grok_intelligence": capability(
            "operational" if grok_configured else "configuration_required",
            persistence="database_analysis_and_monitor_history",
            reason="OCI Responses 密钥和服务地址已配置。"
            if grok_configured
            else "实时 X/Web 检索需要配置 OCI_GENAI_API_KEY 和 OCI_GENAI_BASE_URL。",
            dependencies=["oci_responses", "x_search", "web_search", "code_interpreter"],
        ),
        "intelligence_history": capability(
            "operational" if database_ok else "unavailable",
            persistence="workspace_scoped_immutable_database_snapshots",
            reason="情报分析结果保存完整输入与输出；可恢复并导出，不重新调用 Grok。"
            if database_ok
            else "数据库连接失败，分析历史无法保存或读取。",
            dependencies=["sqlite", "audit_trail", "reportlab"],
        ),
        "intelligence_scheduler": capability(
            "operational",
            persistence="database",
            reason="定时监控、执行历史和 PDF 报告已持久化。",
            dependencies=["sqlite", "single_process_scheduler", "reportlab"],
        ),
        "intelligence_pdf_export": capability(
            "operational" if pdf_export_available else "unavailable",
            persistence="database_metadata_and_filesystem",
            reason="情报结果可导出 PDF；监控成功运行自动保存报告。"
            if pdf_export_available
            else "PDF 生成依赖 ReportLab 未安装。",
            dependencies=["reportlab", "cjk_font", "audit_trail", "artifact_store"],
        ),
        "audit_trail": capability(
            "operational" if database_ok else "unavailable",
            persistence="database",
            reason="审计事件已写入 audit_events 数据表。"
            if database_ok
            else "数据库连接失败。",
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
                "available_models": [
                    m.strip()
                    for m in settings.AVAILABLE_LLM_MODELS.split(",")
                    if m.strip()
                ],
                "region": settings.OCI_REGION,
                "tools": ["web_search", "x_search", "code_interpreter"],
            },
        },
    }
