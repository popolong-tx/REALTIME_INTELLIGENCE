"""Open-platform manifest for workspace-aware product clients.

The manifest exposes stable extension and deployment contracts without
pretending that production tenant isolation or enterprise identity has already
been provisioned in this local demo.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.services.role_permission_service import ROLE_PERMISSIONS


router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


ROLE_LABELS = {
    "viewer": "只读访客",
    "analyst": "分析师",
    "researcher": "量化研究员",
    "trader": "模拟组合经理",
    "admin": "平台管理员",
}


@router.get("/manifest")
async def get_platform_manifest():
    """Return workspace templates, connector contracts, and platform readiness."""
    roles = [
        {
            "id": role.value,
            "name": ROLE_LABELS.get(role.value, role.value),
            "permissions": sorted(permission.value for permission in permissions),
        }
        for role, permissions in ROLE_PERMISSIONS.items()
    ]

    return {
        "schema_version": "2026-08-25",
        "platform": {
            "name": "Grok Demo",
            "edition": "Open Platform Foundation",
            "deployment": "local",
            "execution_mode": settings.EXECUTION_MODE,
            "live_order_mutations_enabled": (
                settings.EXECUTION_MODE == "live"
                and settings.BROKER_LIVE_TRADING_ENABLED
            ),
            "tenancy_readiness": "workspace_foundation",
        },
        "workspaces": [
            {
                "id": "personal",
                "name": "我的研究空间",
                "short_name": "个人",
                "type": "personal",
                "role": "owner",
                "status": "active",
                "provisioning": "local_active",
                "description": "面向个人的研究、模拟计划和复盘空间。",
                "member_slots": ["所有者"],
                "policy_pack": "个人研究默认策略",
            },
            {
                "id": "institution",
                "name": "机构投研工作区",
                "short_name": "机构",
                "type": "institution",
                "role": "researcher",
                "status": "template",
                "provisioning": "template_preview",
                "description": "共享研究资产，使用审批、角色、数据授权与审计门禁。",
                "member_slots": ["研究负责人", "量化研究员", "风险复核人", "只读访客"],
                "policy_pack": "机构双人复核策略",
            },
            {
                "id": "custom",
                "name": "客户化交付沙箱",
                "short_name": "客户化",
                "type": "custom",
                "role": "admin",
                "status": "template",
                "provisioning": "template_preview",
                "description": "独立品牌、连接器清单和交付配置的客户化预览。",
                "member_slots": ["客户管理员", "平台运维", "合规负责人"],
                "policy_pack": "客户专属策略草案",
            },
        ],
        "roles": roles,
        "connectors": [
            {
                "id": "market-data",
                "name": "市场与基本面数据",
                "category": "provider",
                "status": "available",
                "scope": "workspace",
                "contract": "REST provider adapter",
            },
            {
                "id": "oci-grok",
                "name": "OCI Grok 决策情报",
                "category": "intelligence",
                "status": "configured" if settings.OCI_GENAI_API_KEY else "needs_configuration",
                "scope": "tenant_secret",
                "contract": "OCI Responses API + Web/X Search + Code Interpreter + cited source ledger + structured reasoning",
            },
            {
                "id": "intelligence-scheduler",
                "name": "情报定时监控",
                "category": "event",
                "status": "available",
                "scope": "workspace",
                "contract": "persistent interval monitor + execution history + automatic PDF artifact + pause/resume + run-now",
            },
            {
                "id": "intelligence-history",
                "name": "情报分析历史",
                "category": "intelligence",
                "status": "available",
                "scope": "workspace",
                "contract": "immutable input/output snapshot + workspace-scoped list/detail + exact historical PDF export without re-query",
            },
            {
                "id": "model-runtime",
                "name": "模型与策略运行时",
                "category": "model",
                "status": "available",
                "scope": "workspace",
                "contract": "versioned model package + governance gates",
            },
            {
                "id": "webhook",
                "name": "事件与 Webhook",
                "category": "event",
                "status": "available",
                "scope": "workspace_secret",
                "contract": "persistent signed inbound/outbound webhook and delivery history",
            },
            {
                "id": "broker",
                "name": "券商适配器",
                "category": "execution",
                "status": "simulation_only",
                "scope": "tenant_secret",
                "contract": "broker adapter; live order and cancellation mutations rejected by server policy",
            },
        ],
        "extension_points": [
            {
                "id": "data-provider",
                "name": "数据提供商",
                "interface": "ProviderAdapter",
                "artifact": "provider manifest + normalized schemas",
            },
            {
                "id": "strategy-package",
                "name": "策略与模型包",
                "interface": "StrategyPackage",
                "artifact": "immutable version + evidence + policy metadata",
            },
            {
                "id": "workspace-app",
                "name": "工作区应用模板",
                "interface": "WorkspaceAppManifest",
                "artifact": "navigation, widgets, roles, feature flags",
            },
            {
                "id": "event-connector",
                "name": "事件连接器",
                "interface": "EventConnector",
                "artifact": "signed events + idempotency + audit context",
            },
            {
                "id": "intelligence-workflow",
                "name": "机构情报工作流",
                "interface": "IntelligenceWorkflowManifest",
                "artifact": "input schema + prompt version + evidence policy + output schema",
            },
        ],
        "workspace_apps": [
            {
                "id": "realtime-open-research",
                "name": "X 与公共开放信息检索",
                "status": "available" if settings.OCI_GENAI_API_KEY else "needs_configuration",
                "workspaces": ["institution", "custom", "personal"],
                "model": settings.OCI_GROK_MODEL_ID,
                "requires": ["oci-grok", "web_search", "x_search", "code_interpreter", "citation_ledger", "intelligence-scheduler", "intelligence-history", "pdf-export"],
            },
            {
                "id": "project-risk-intelligence",
                "name": "项目风险情报",
                "status": "available" if settings.OCI_GENAI_API_KEY else "needs_configuration",
                "workspaces": ["institution", "custom", "personal"],
                "model": settings.OCI_GROK_MODEL_ID,
                "requires": ["oci-grok", "web_search", "x_search", "code_interpreter", "citation_ledger", "intelligence-scheduler", "intelligence-history", "pdf-export"],
            },
            {
                "id": "geopolitical-financing",
                "name": "地缘融资推演",
                "status": "available" if settings.OCI_GENAI_API_KEY else "needs_configuration",
                "workspaces": ["institution", "custom", "personal"],
                "model": settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
                "requires": ["oci-grok", "web_search", "x_search", "code_interpreter", "citation_ledger", "scenario_governance", "intelligence-history", "pdf-export"],
            },
        ],
        "deployment_profiles": [
            {
                "id": "shared",
                "name": "共享云服务",
                "status": "target",
                "isolation": "tenant_id + policy enforcement + per-tenant secrets",
            },
            {
                "id": "dedicated",
                "name": "专属私有云",
                "status": "target",
                "isolation": "dedicated database, cache, object storage and keys",
            },
            {
                "id": "on-prem",
                "name": "本地化部署",
                "status": "current_local_foundation",
                "isolation": "single customer boundary; external identity pending",
            },
        ],
        "isolation_contract": {
            "status": "design_contract",
            "required_context": ["tenant_id", "workspace_id", "actor_id", "role", "request_id"],
            "scoped_resources": [
                "profiles",
                "watchlists",
                "research snapshots",
                "project monitors",
                "realtime research monitors",
                "intelligence monitor runs",
                "intelligence analysis history",
                "institutional intelligence briefs",
                "models",
                "plans",
                "connectors",
                "audit events",
            ],
            "production_blockers": [
                "database row-level tenant enforcement",
                "tenant-aware cache keys and object storage",
                "enterprise SSO/SCIM and durable memberships",
                "per-tenant secret vault and entitlement checks",
            ],
        },
    }
