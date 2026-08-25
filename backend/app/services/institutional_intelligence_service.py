"""Grok-backed institutional intelligence workflows.

The service keeps live retrieval, structured reasoning, citations, and audit
metadata behind the OCI Responses boundary.  When OCI is not configured it
returns an explicit configuration state instead of fabricating live findings.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4
import json
import re

from app.core.config import settings
from app.services.oci_responses_service import oci_responses_service


PROJECT_RISK_DIMENSIONS = [
    {"id": "political", "label": "政治与政策"},
    {"id": "social", "label": "社会与社区"},
    {"id": "debt", "label": "债务与偿付"},
    {"id": "environment", "label": "环境与许可"},
    {"id": "reputation", "label": "声誉与利益相关方"},
]

GEOPOLITICAL_IMPACT_DIMENSIONS = [
    {"id": "pipeline", "label": "项目管道"},
    {"id": "cofinancing", "label": "联合融资"},
    {"id": "borrowing_appetite", "label": "成员借贷意愿"},
    {"id": "feasibility", "label": "项目可行性"},
    {"id": "risk_transfer", "label": "风险转移"},
]

SIMPLIFIED_CHINESE_OUTPUT_RULE = """
输出语言强制规则：
1. 除 JSON 键、规定的英文枚举代码、URL、日期、股票代码、模型/工具标识和引用编号外，所有面向用户的文字必须使用简体中文。
2. 人名、机构名、产品名和官方术语可保留原文，并在必要时给出中文名称；不得为了翻译而改变事实含义。
3. X 的 original_text 必须保持来源原文，不能翻译或改写；如原文不是中文，在 content_excerpt 中提供忠实的简体中文说明。
4. 不得输出英文版摘要后再附中文；结构化分析、判断、趋势、理由、事件、情景、建议、假设、未知项和来源说明直接使用简体中文。
""".strip()

TRANSLATABLE_PROSE_KEYS = {
    "executive_summary",
    "direct_assessment",
    "coverage_note",
    "label",
    "evidence",
    "rationale",
    "title",
    "content_excerpt",
    "impact",
    "trigger",
    "owner",
    "urgency",
    "driver",
    "mechanism",
    "financing_effect",
    "name",
    "probability",
    "pipeline_impact",
    "cofinancing_impact",
    "borrowing_appetite",
    "feasibility",
    "risk_transfer",
    "upside",
    "downside",
    "timing",
    "position",
    "action",
    "excerpt",
}

TRANSLATABLE_PROSE_LIST_KEYS = {
    "watch_items",
    "assumptions",
    "unknowns",
    "early_signals",
    "affected_parties",
    "warnings",
}

LOCALIZED_ENUM_VALUES = {
    "low": "低",
    "moderate": "中等",
    "high": "高",
    "critical": "严重",
    "unrated": "未评级",
    "rising": "上升",
    "stable": "稳定",
    "falling": "下降",
    "unknown": "未知",
    "unclear": "不明确",
    "now": "立即",
    "7_days": "7 天内",
    "30_days": "30 天内",
    "monitor": "持续监控",
    "quarter": "本季度",
    "baseline": "基准情景",
    "stress": "压力情景",
    "opportunity": "机会情景",
}


class InstitutionalIntelligenceService:
    """Orchestrate cited Grok analysis for project and sovereign decisions."""

    @property
    def configured(self) -> bool:
        return oci_responses_service.configured

    def capabilities(self) -> Dict[str, Any]:
        return {
            "configured": self.configured,
            "provider": "OCI Generative AI Responses API",
            "models": {
                "realtime": settings.OCI_GROK_MODEL_ID,
                "reasoning": settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
            },
            "retrieval": ["x_search", "web_search", "code_interpreter", "provider_citations"],
            "workflows": [
                {
                    "id": "realtime-research",
                    "name": "X 与公共开放信息检索",
                    "dimensions": [
                        {"id": "x", "label": "X 最新原文"},
                        {"id": "web", "label": "公共开放信息"},
                        {"id": "compute", "label": "趋势计算"},
                    ],
                },
                {
                    "id": "project-risk",
                    "name": "成员国与项目实时风险情报",
                    "dimensions": PROJECT_RISK_DIMENSIONS,
                },
                {
                    "id": "geopolitical-impact",
                    "name": "地缘政治与融资影响推演",
                    "dimensions": GEOPOLITICAL_IMPACT_DIMENSIONS,
                },
            ],
            "guardrails": [
                "实时事实必须进入来源账本",
                "无引用结论标记为未验证",
                "检索结果为尽力覆盖，不将其声明为平台全量数据",
                "X 观点不等同于事实或已验证行动",
                "输出支持人工复核，不自动批准、暂停或调整融资",
            ],
        }

    async def search_realtime_information(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve recent X originals and public open information together."""
        if not self.configured:
            return self._realtime_configuration_required(request)

        source_channels = request.get("source_channels") or ["x", "web"]
        from_date = self._as_iso_date(request.get("date_from"))
        to_date = self._as_iso_date(request.get("date_to"))
        raw = await oci_responses_service.generate_realtime_research(
            prompt=self._realtime_research_prompt(request, from_date, to_date),
            system_prompt=(
                "你是一名实时公开信息研究员。按要求保留有引用的 X 原文，将公共网页证据分开呈现，"
                "不得宣称覆盖全部信息。严格区分来源原文、事实、观点、媒体转述和模型推断；"
                "不得编造作者、时间、URL、引语或来源内容。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            source_channels=source_channels,
            from_date=from_date,
            to_date=to_date,
            use_code_interpreter=bool(request.get("use_code_interpreter", True)),
            model_id=settings.OCI_GROK_MODEL_ID,
            max_tokens=6500,
            temperature=0.1,
        )
        result = self._normalize_realtime_research(raw, request, from_date, to_date)
        return await self._ensure_simplified_chinese(result)

    async def analyze_project_risk(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured:
            return self._configuration_required(
                workflow="project-risk",
                model=settings.OCI_GROK_MODEL_ID,
                framework=PROJECT_RISK_DIMENSIONS,
                request=request,
            )

        window_days = int(request.get("window_days") or 7)
        from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).date().isoformat()
        prompt = self._project_risk_prompt(request)
        raw = await oci_responses_service.generate_realtime_research(
            prompt=prompt,
            system_prompt=(
                "你是一名机构项目风险分析师，必须直接、以证据为中心。不得淡化重大违约、政治、"
                "社会冲突、环境或声誉风险。严格区分事实、媒体转述、观点和模型推断；"
                "不得编造来源，也不得暗示任何融资决策已经获批。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.15,
            max_tokens=5000,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=settings.OCI_GROK_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="project-risk",
            raw=raw,
            request=request,
            framework=PROJECT_RISK_DIMENSIONS,
        )
        return await self._ensure_simplified_chinese(result)

    async def analyze_geopolitical_impact(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured:
            return self._configuration_required(
                workflow="geopolitical-impact",
                model=settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
                framework=GEOPOLITICAL_IMPACT_DIMENSIONS,
                request=request,
            )

        window_days = int(request.get("window_days") or 30)
        from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).date().isoformat()
        prompt = self._geopolitical_prompt(request)
        raw = await oci_responses_service.generate_realtime_research(
            prompt=prompt,
            system_prompt=(
                "你是多边开发银行高级战略分析团队。使用明确的因果链和竞争性假设，直接呈现权衡"
                "以及可能的二阶影响。将有来源的观察与模型推断分开，明确写出假设；"
                "不得编造确定性、共识或引用。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.2,
            max_tokens=6500,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="geopolitical-impact",
            raw=raw,
            request=request,
            framework=GEOPOLITICAL_IMPACT_DIMENSIONS,
        )
        return await self._ensure_simplified_chinese(result)

    @staticmethod
    def _project_risk_prompt(request: Dict[str, Any]) -> str:
        focuses = ", ".join(request.get("risk_focus") or [item["label"] for item in PROJECT_RISK_DIMENSIONS])
        return f"""
使用 X Search、公共 Web Search 和可引用证据分析当前项目级风险。

国家/成员：{request.get('country')}
项目：{request.get('project_name')}
金融产品：{request.get('product_type')}
监测窗口：最近 {request.get('window_days', 7)} 天
重点维度：{focuses}
决策问题：{request.get('monitoring_question') or '发生了什么变化、为什么重要，以及投资与风险团队现在应复核什么？'}

仅返回符合下列结构的 JSON：
{{
  "executive_summary": "简明且带引用的中文简报",
  "direct_assessment": "直接说明最重要风险，不淡化",
  "overall_risk": "low|moderate|high|critical|unrated",
  "risk_dimensions": [
    {{"dimension": "political|social|debt|environment|reputation", "label": "中文显示名称", "score": 0, "level": "low|moderate|high|critical|unrated", "trend": "rising|stable|falling|unknown", "rationale": "中文理由"}}
  ],
  "events": [
    {{"title": "中文事件标题", "observed_at": "日期或 unknown", "evidence_status": "verified_source|reported_claim|opinion|unverified", "impact": "对项目的中文影响说明", "source_refs": ["引用 URL 或来源标识"]}}
  ],
  "decision_options": [
    {{"action": "continue|adjust_terms|pause_for_review|accelerate|escalate", "urgency": "now|7_days|30_days|monitor", "owner": "中文负责人/团队", "trigger": "中文可观察触发条件", "rationale": "中文理由"}}
  ],
  "watch_items": ["下一步需观察的具体中文信号"],
  "assumptions": ["重大中文假设"]
}}

评分范围为 0-100，且必须有证据支持。证据不足时使用 "unrated" 并省略无法判断的数值。不得声称社交媒体情绪能够证明事件真实发生。

{SIMPLIFIED_CHINESE_OUTPUT_RULE}
""".strip()

    @staticmethod
    def _geopolitical_prompt(request: Dict[str, Any]) -> str:
        regions = ", ".join(request.get("regions") or [])
        actors = ", ".join(request.get("actors") or [])
        products = ", ".join(request.get("product_types") or [])
        return f"""
分析地缘政治变化如何影响多边开发融资。

议题/事件：{request.get('issue')}
地区/成员国：{regions or '不限定'}
跟踪对象：{actors or '相关政府、官员、智库、媒体和融资合作伙伴'}
金融产品：{products or '主权贷款、非主权融资、担保和联合融资'}
决策周期：{request.get('horizon')}
实时证据窗口：最近 {request.get('window_days', 30)} 天
决策问题：{request.get('decision_question') or '这将如何改变项目管道、联合融资、借贷意愿、可行性和风险转移？'}

使用 X Search 获取当前公开表态，使用 Web Search 获取官方、机构、智库和媒体证据。必须区分两类渠道，并且仅返回 JSON：
{{
  "executive_summary": "直接的中文结论",
  "direct_assessment": "决策者不应忽略的中文判断",
  "transmission_paths": [
    {{"driver": "中文变化驱动因素", "mechanism": "中文因果链", "financing_effect": "中文融资影响", "affected_parties": ["受影响方"], "evidence_status": "sourced|inference|uncertain"}}
  ],
  "scenarios": [
    {{"name": "基准情景|压力情景|机会情景", "probability": "中文定性概率区间", "early_signals": ["中文可观察信号"], "pipeline_impact": "中文影响", "cofinancing_impact": "中文影响", "borrowing_appetite": "中文影响", "feasibility": "中文影响", "risk_transfer": "中文影响"}}
  ],
  "decision_options": [
    {{"action": "中文策略选项", "timing": "立即|30天内|本季度", "upside": "中文收益", "downside": "中文成本或风险", "trigger": "中文可观察条件", "owner": "中文负责人/团队"}}
  ],
  "stakeholder_positions": [
    {{"stakeholder": "相关方名称", "position": "中文立场说明", "evidence_status": "official|reported|opinion|inferred"}}
  ],
  "assumptions": ["中文假设"],
  "unknowns": ["中文重要未知项"]
}}

避免模糊的外交措辞。不得把模型推断表述为官方立场，不得编造精确的数字概率。

{SIMPLIFIED_CHINESE_OUTPUT_RULE}
""".strip()

    @staticmethod
    def _realtime_research_prompt(
        request: Dict[str, Any],
        from_date: Optional[str],
        to_date: Optional[str],
    ) -> str:
        keywords = ", ".join(request.get("keywords") or [])
        channels = ", ".join(request.get("source_channels") or ["x", "web"])
        preserve_original = bool(request.get("preserve_x_original", True))
        return f"""
通过选定的实时信息渠道研究下列主题。

主题/问题：{request.get('query')}
关键词和别名：{keywords or '仅从主题推导必要别名'}
日期范围：{from_date or '不限定'} 至 {to_date or '当前时间'}
选定渠道：{channels}
最多返回条数：{request.get('max_results', 30)}
保留带引用的 X 原文：{'是' if preserve_original else '否'}

覆盖范围规则：这是尽力检索结果，并非 X 或公共网络的完整导出。不得声称结果是“全量”或“所有帖子”。不要重复近似转发；提供方返回来源 URL 时，每条结果都必须保留引用链接。

仅返回符合下列结构的 JSON：
{{
  "executive_summary": "用中文说明发生了什么变化以及为何重要",
  "coverage_note": "用中文直接说明检索范围与局限",
  "trends": [
    {{"label": "中文趋势名称", "direction": "rising|stable|falling|unclear", "evidence": "中文简要依据", "source_refs": ["URL"]}}
  ],
  "items": [
    {{
      "source_type": "x|public",
      "title": "中文帖子说明或公共网页标题",
      "author": "账号、发布方或 unknown",
      "published_at": "ISO 日期/时间或 unknown",
      "original_text": "可获得时逐字保留 X 原文，否则为空",
      "content_excerpt": "公共网页的中文摘要；如 X 原文非中文，则提供忠实的中文说明",
      "url": "来源 URL，无法获得时为空",
      "evidence_status": "source_available|reported_claim|opinion|unverified",
      "matched_keywords": ["匹配关键词"]
    }}
  ],
  "unknowns": ["中文说明重要缺失或未验证事项"]
}}

对于 X 内容，original_text 必须忠实保留引用帖子的原文，不能重建缺失文字；如果原文不是中文，在 content_excerpt 中另写中文说明。公共网页不得把改写内容放入 original_text。代码分析只能用于证据去重、计数或趋势计算，不得制造缺失观察。

{SIMPLIFIED_CHINESE_OUTPUT_RULE}
""".strip()

    @staticmethod
    def _looks_english(text: str) -> bool:
        """Detect English-heavy prose without flagging URLs or short identifiers."""
        value = str(text or "").strip()
        if not value or value.startswith(("http://", "https://")):
            return False
        latin_words = re.findall(r"\b[A-Za-z][A-Za-z'-]{2,}\b", value)
        if not latin_words:
            return False
        cjk_count = len(re.findall(r"[\u3400-\u9fff]", value))
        latin_count = sum(len(word) for word in latin_words)
        return len(latin_words) >= 2 or (latin_count >= 12 and cjk_count == 0) or latin_count > cjk_count * 3

    @classmethod
    def _audit_user_prose_language(
        cls,
        value: Any,
        workflow: str,
        parent_key: Optional[str] = None,
    ) -> int:
        """Localize known enums and count residual English without altering prose."""
        detected = 0
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if key == "original_text":
                    continue
                if isinstance(item, str):
                    if item in LOCALIZED_ENUM_VALUES and key in {"urgency", "timing", "name", "probability"}:
                        value[key] = LOCALIZED_ENUM_VALUES[item]
                    elif key in TRANSLATABLE_PROSE_KEYS and not (
                        workflow == "project-risk" and key == "action"
                    ) and cls._looks_english(item):
                        detected += 1
                elif isinstance(item, (dict, list)):
                    detected += cls._audit_user_prose_language(item, workflow, key)
            return detected

        if isinstance(value, list):
            for index, item in enumerate(list(value)):
                if isinstance(item, str):
                    if item in LOCALIZED_ENUM_VALUES:
                        value[index] = LOCALIZED_ENUM_VALUES[item]
                    elif parent_key in TRANSLATABLE_PROSE_LIST_KEYS and cls._looks_english(item):
                        detected += 1
                elif isinstance(item, (dict, list)):
                    detected += cls._audit_user_prose_language(item, workflow, parent_key)
        return detected

    async def _ensure_simplified_chinese(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply local language compliance checks before returning user-facing data."""
        workflow = str(result.get("workflow") or "")
        detected = 0
        for section in ("analysis", "evidence", "warnings"):
            if section in result:
                detected += self._audit_user_prose_language(result[section], workflow, section)

        audit = result.setdefault("audit", {})
        audit["language"] = "zh-CN"
        audit["language_compliant"] = detected == 0
        audit["english_fields_detected"] = detected
        return result

    def _normalize_live_result(
        self,
        workflow: str,
        raw: Dict[str, Any],
        request: Dict[str, Any],
        framework: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        output_text = raw.get("inferenceResponse", {}).get("text", "")
        analysis = self._extract_json_object(output_text)
        if not analysis:
            analysis = {
                "executive_summary": output_text or "Grok 未返回可解析的分析文本。",
                "direct_assessment": "结构化输出解析失败，必须人工复核原始响应。",
            }

        citations = self._normalize_citations(raw.get("citations") or [])
        metadata = raw.get("metadata") or {}
        degraded_tools = metadata.get("degraded_tools") or []
        warnings = [
            "X 上的公开观点、情绪和行动声明默认未验证，不得单独触发融资决策。",
            "该结果用于研究与人工复核，不自动批准、暂停、加速或修改金融产品。",
            "实时检索为尽力覆盖，不代表 X 或公共网络的全量数据。",
        ]
        if metadata.get("tool_warnings"):
            warnings.extend(metadata["tool_warnings"])
        if not citations:
            warnings.insert(0, "本次结果没有可访问引用，所有实时事实均应视为未验证。")

        return {
            "status": "partial" if degraded_tools else "live",
            "workflow": workflow,
            "evidence_quality": "cited" if citations else "unverified",
            "analysis": analysis,
            "evidence": citations,
            "analysis_framework": framework,
            "audit": {
                "provider": metadata.get("provider") or "oci-generative-ai",
                "model": metadata.get("model_id"),
                "region": metadata.get("region"),
                "request_id": metadata.get("request_id") or str(uuid4()),
                "generated_at": metadata.get("generated_at") or datetime.now(timezone.utc).isoformat(),
                "query_window_days": request.get("window_days"),
                "workspace_id": request.get("workspace_id"),
                "tools": metadata.get("used_tools") or metadata.get("tools") or [],
                "requested_tools": metadata.get("requested_tools") or [],
                "degraded_tools": degraded_tools,
                "coverage": metadata.get("coverage") or "best_effort",
            },
            "warnings": warnings,
        }

    def _normalize_realtime_research(
        self,
        raw: Dict[str, Any],
        request: Dict[str, Any],
        from_date: Optional[str],
        to_date: Optional[str],
    ) -> Dict[str, Any]:
        output_text = raw.get("inferenceResponse", {}).get("text", "")
        analysis = self._extract_json_object(output_text) or {
            "executive_summary": output_text or "Grok 未返回可解析的检索结果。",
            "coverage_note": "结构化结果解析失败，必须人工复核原始响应。",
            "items": [],
            "trends": [],
            "unknowns": ["结构化输出不可用"],
        }
        items = self._normalize_research_items(analysis.get("items") or [])
        analysis["items"] = items
        citations = self._normalize_citations(raw.get("citations") or [])
        metadata = raw.get("metadata") or {}
        degraded_tools = metadata.get("degraded_tools") or []
        warnings = [
            "检索结果为尽力覆盖，不代表 X 或公共网络的全量导出。",
            "X 原文、观点与交易声明必须结合引用独立核验。",
        ]
        if metadata.get("tool_warnings"):
            warnings.extend(metadata["tool_warnings"])
        if not citations:
            warnings.insert(0, "本次结果没有可访问引用，内容均应视为未验证。")

        counts = {
            "x": sum(1 for item in items if item.get("source_type") == "x"),
            "public": sum(1 for item in items if item.get("source_type") == "public"),
            "citations": len(citations),
        }
        return {
            "status": "partial" if degraded_tools else "live",
            "workflow": "realtime-research",
            "evidence_quality": "cited" if citations else "unverified",
            "coverage": "best_effort",
            "analysis": analysis,
            "items": items,
            "evidence": citations,
            "counts": counts,
            "audit": {
                "provider": metadata.get("provider") or "oci-generative-ai",
                "model": metadata.get("model_id"),
                "region": metadata.get("region"),
                "request_id": metadata.get("request_id") or str(uuid4()),
                "generated_at": metadata.get("generated_at") or datetime.now(timezone.utc).isoformat(),
                "date_from": from_date,
                "date_to": to_date,
                "workspace_id": request.get("workspace_id"),
                "tools": metadata.get("used_tools") or metadata.get("tools") or [],
                "requested_tools": metadata.get("requested_tools") or [],
                "degraded_tools": degraded_tools,
                "coverage": metadata.get("coverage") or "best_effort",
            },
            "warnings": warnings,
        }

    @staticmethod
    def _configuration_required(
        workflow: str,
        model: str,
        framework: List[Dict[str, str]],
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "status": "configuration_required",
            "workflow": workflow,
            "evidence_quality": "not_run",
            "analysis": {},
            "evidence": [],
            "analysis_framework": framework,
            "audit": {
                "provider": "oci-generative-ai",
                "model": model,
                "region": settings.OCI_REGION,
                "request_id": str(uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "query_window_days": request.get("window_days"),
                "workspace_id": request.get("workspace_id"),
                "tools": [],
                "requested_tools": ["web_search", "x_search", "code_interpreter"],
                "degraded_tools": [],
                "coverage": "not_run",
            },
            "configuration": {
                "message": "OCI Grok 尚未配置；当前仅展示分析框架，没有生成或伪造实时事实。",
                "required_secret": "OCI_GENAI_API_KEY",
            },
            "warnings": ["配置服务端 OCI 凭证后才能运行实时检索和推理。"],
        }

    @staticmethod
    def _realtime_configuration_required(request: Dict[str, Any]) -> Dict[str, Any]:
        source_channels = request.get("source_channels") or ["x", "web"]
        requested_tools = []
        if "web" in source_channels:
            requested_tools.append("web_search")
        if "x" in source_channels:
            requested_tools.append("x_search")
        if request.get("use_code_interpreter", True):
            requested_tools.append("code_interpreter")
        return {
            "status": "configuration_required",
            "workflow": "realtime-research",
            "evidence_quality": "not_run",
            "coverage": "not_run",
            "analysis": {"items": [], "trends": [], "unknowns": []},
            "items": [],
            "evidence": [],
            "counts": {"x": 0, "public": 0, "citations": 0},
            "audit": {
                "provider": "oci-generative-ai",
                "model": settings.OCI_GROK_MODEL_ID,
                "region": settings.OCI_REGION,
                "request_id": str(uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "date_from": InstitutionalIntelligenceService._as_iso_date(request.get("date_from")),
                "date_to": InstitutionalIntelligenceService._as_iso_date(request.get("date_to")),
                "workspace_id": request.get("workspace_id"),
                "tools": [],
                "requested_tools": requested_tools,
                "degraded_tools": [],
                "coverage": "not_run",
            },
            "configuration": {
                "message": "OCI Grok 尚未配置；当前没有查询 X 或公共网页，也没有生成模拟结果。",
                "required_secret": "OCI_GENAI_API_KEY",
            },
            "warnings": [
                "配置服务端 OCI 凭证后才能运行实时检索。",
                "检索完成后仍属于尽力覆盖，不能声明为平台全量数据。",
            ],
        }

    @staticmethod
    def _as_iso_date(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _normalize_research_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            original_text = str(item.get("original_text") or "").strip()
            excerpt = str(item.get("content_excerpt") or "").strip()
            dedupe_key = url or f"{item.get('author')}|{original_text or excerpt}"
            if not dedupe_key or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            source_type = "x" if str(item.get("source_type") or "").lower() == "x" else "public"
            normalized.append({
                "source_type": source_type,
                "title": item.get("title") or ("X 公开内容" if source_type == "x" else "公共开放来源"),
                "author": item.get("author") or "unknown",
                "published_at": item.get("published_at") or "unknown",
                "original_text": original_text if source_type == "x" else "",
                "content_excerpt": excerpt,
                "url": url,
                "evidence_status": item.get("evidence_status") or "unverified",
                "matched_keywords": item.get("matched_keywords") or [],
            })
        return normalized

    @staticmethod
    def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        candidates = [cleaned]
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first >= 0 and last > first:
            candidates.append(cleaned[first:last + 1])
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        return None

    @staticmethod
    def _normalize_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for index, citation in enumerate(citations):
            if not isinstance(citation, dict) or not citation.get("url"):
                continue
            url = str(citation["url"])
            host = urlparse(url).netloc.lower()
            normalized.append({
                "id": f"S{index + 1}",
                "title": citation.get("title") or url,
                "excerpt": citation.get("text") or "",
                "url": url,
                "source_type": "x" if host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"} else "public",
                "verification_status": "unverified_opinion" if "x.com" in host or "twitter.com" in host else "source_available",
            })
        return normalized


institutional_intelligence_service = InstitutionalIntelligenceService()
