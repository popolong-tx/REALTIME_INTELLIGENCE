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

SANCTIONS_NEWS_DIMENSIONS = [
    {"id": "sanctions_lists", "label": "制裁名单"},
    {"id": "adverse_media", "label": "负面媒体"},
    {"id": "regulatory_actions", "label": "监管行动"},
    {"id": "litigation", "label": "诉讼与仲裁"},
    {"id": "beneficial_ownership", "label": "受益所有权"},
]

MARKET_FUNDING_DIMENSIONS = [
    {"id": "interest_rates", "label": "利率环境"},
    {"id": "exchange_rates", "label": "汇率走势"},
    {"id": "credit_spreads", "label": "信用利差"},
    {"id": "commodity_prices", "label": "大宗商品"},
    {"id": "funding_conditions", "label": "融资条件"},
]

RESEARCH_AGENT_DIMENSIONS = [
    {"id": "data_collection", "label": "数据采集"},
    {"id": "computation", "label": "计算与分析"},
    {"id": "verification", "label": "事实校验"},
    {"id": "output", "label": "结构化输出"},
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
            "available_models": [
                m.strip()
                for m in settings.AVAILABLE_LLM_MODELS.split(",")
                if m.strip()
            ],
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
                    "name": "国家/地区与项目实时风险情报",
                    "dimensions": PROJECT_RISK_DIMENSIONS,
                },
                {
                    "id": "geopolitical-impact",
                    "name": "地缘政治与融资影响推演",
                    "dimensions": GEOPOLITICAL_IMPACT_DIMENSIONS,
                },
                {
                    "id": "sanctions-news",
                    "name": "制裁与负面新闻补充",
                    "dimensions": SANCTIONS_NEWS_DIMENSIONS,
                },
                {
                    "id": "market-funding",
                    "name": "市场与资金环境研究",
                    "dimensions": MARKET_FUNDING_DIMENSIONS,
                },
                {
                    "id": "research-agent",
                    "name": "研究与数据 Agent",
                    "dimensions": RESEARCH_AGENT_DIMENSIONS,
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
            model_id=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
            max_tokens=6500,
            temperature=0.1,
        )
        result = self._normalize_realtime_research(raw, request, from_date, to_date)
        return await self._ensure_simplified_chinese(result)

    async def analyze_materials(
        self,
        *,
        question: str,
        text_inputs: List[Dict[str, Any]],
        image_inputs: List[Dict[str, Any]],
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Jointly analyze only materials from the current isolated session."""
        if not self.configured:
            return {
                "status": "configuration_required",
                "workflow": "material-analysis",
                "analysis": {},
                "evidence": [],
                "warnings": ["OCI Grok 尚未配置；没有读取外部资料并生成模拟分析。"],
            }
        context = "\n\n".join(f"资料：{item['filename']}\n{item['text']}" for item in text_inputs)
        prompt = (
            "你是一名机构研究分析师。只能依据本次任务提供的资料回答，不得调用或假设其他任务的资料。\n"
            f"研究问题：{question}\n\n文本资料：\n{context[:300000]}\n\n"
            "请返回 JSON，包含 executive_summary、key_findings、contradictions、unknowns、"
            "decision_implications 和 citations。明确区分原文事实、资料间冲突和模型推断；"
            "截图中的表格、图表、日期、金额和主体必须说明所在文件，无法辨认时标记为待核实。"
        )
        if image_inputs:
            raw = await oci_responses_service.generate_multimodal(
                prompt=prompt,
                images=image_inputs,
                system_prompt=SIMPLIFIED_CHINESE_OUTPUT_RULE,
                model_id=model_id or settings.OCI_GROK_MODEL_ID,
            )
        else:
            raw = await oci_responses_service.generate_text(
                prompt=prompt,
                system_prompt=SIMPLIFIED_CHINESE_OUTPUT_RULE,
                model_id=model_id or settings.OCI_GROK_MODEL_ID,
                max_tokens=6000,
                temperature=0.1,
            )
        raw_text = raw.get("inferenceResponse", {}).get("text", "")
        analysis = self._extract_json_object(raw_text) or {
            "executive_summary": raw_text,
            "unknowns": ["结构化输出解析失败，需人工复核原始回复"],
        }
        return {
            "status": "live",
            "workflow": "material-analysis",
            "analysis": analysis,
            "evidence": [{"material_id": item["material_id"], "filename": item["filename"]} for item in text_inputs + image_inputs],
            "warnings": ["本次联合分析仅使用当前研究会话上传的资料。", "截图中的不可辨认内容不应被视为事实。"],
            "audit": {**(raw.get("metadata") or {}), "source_scope": "session_materials_only"},
        }

    async def analyze_project_risk(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured:
            return self._configuration_required(
                workflow="project-risk",
                model=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
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
            model_id=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
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
                model=request.get("model_id") or settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
                framework=GEOPOLITICAL_IMPACT_DIMENSIONS,
                request=request,
            )

        window_days = int(request.get("window_days") or 30)
        from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).date().isoformat()
        prompt = self._geopolitical_prompt(request)
        raw = await oci_responses_service.generate_realtime_research(
            prompt=prompt,
            system_prompt=(
                "你是金融机构高级战略分析团队。使用明确的因果链和竞争性假设，直接呈现权衡"
                "以及可能的二阶影响。将有来源的观察与模型推断分开，明确写出假设；"
                "不得编造确定性、共识或引用。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.2,
            max_tokens=6500,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=request.get("model_id") or settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="geopolitical-impact",
            raw=raw,
            request=request,
            framework=GEOPOLITICAL_IMPACT_DIMENSIONS,
        )
        return await self._ensure_simplified_chinese(result)

    # ── 场景 03：制裁与负面新闻 ────────────────────────────────────

    async def analyze_sanctions_news(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """制裁与负面新闻补充 — 为 KYC/CDD 与合作方审查提供公共信息线索。"""
        if not self.configured:
            return self._configuration_required(
                workflow="sanctions-news",
                model=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
                framework=SANCTIONS_NEWS_DIMENSIONS,
                request=request,
            )

        window_days = int(request.get("window_days") or 30)
        from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).date().isoformat()
        prompt = self._sanctions_news_prompt(request)
        raw = await oci_responses_service.generate_realtime_research(
            prompt=prompt,
            system_prompt=(
                "你是金融机构合规与尽职调查分析师。必须以事实为依据，严格区分已确认制裁、"
                "媒体报道、监管行动和未经证实的线索。不得编造制裁名单条目或法律结论；"
                '不确定的信息必须明确标注为"待核实"。\n\n'
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.1,
            max_tokens=5000,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=False,
            model_id=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="sanctions-news",
            raw=raw,
            request=request,
            framework=SANCTIONS_NEWS_DIMENSIONS,
        )
        return await self._ensure_simplified_chinese(result)

    # ── 场景 04：市场与资金环境 ────────────────────────────────────

    async def analyze_market_funding(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """市场与资金环境 — 利率、汇率、商品价格和融资条件研究。"""
        if not self.configured:
            return self._configuration_required(
                workflow="market-funding",
                model=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
                framework=MARKET_FUNDING_DIMENSIONS,
                request=request,
            )

        window_days = int(request.get("window_days") or 30)
        from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).date().isoformat()
        prompt = self._market_funding_prompt(request)
        raw = await oci_responses_service.generate_realtime_research(
            prompt=prompt,
            system_prompt=(
                "你是金融机构市场与融资环境分析师。基于公开数据和可靠来源，分析利率、汇率、"
                "商品价格、信用利差和融资条件的最新变化及其对基础设施融资的影响。"
                "严格区分市场数据事实、分析师观点和模型推断；不得编造具体数值。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.15,
            max_tokens=5000,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="market-funding",
            raw=raw,
            request=request,
            framework=MARKET_FUNDING_DIMENSIONS,
        )
        return await self._ensure_simplified_chinese(result)

    # ── 场景 05：研究与数据 Agent ────────────────────────────────────

    async def run_research_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """研究与数据 Agent — 连接白名单 SQL、知识库与计算工具生成可核验分析。"""
        if not self.configured:
            return self._configuration_required(
                workflow="research-agent",
                model=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
                framework=RESEARCH_AGENT_DIMENSIONS,
                request=request,
            )

        prompt = self._research_agent_prompt(request)
        # Build tools list from data_sources
        data_sources = request.get("data_sources") or ["web_search", "code_interpreter"]
        tools: list[dict] = []
        if "web_search" in data_sources:
            tools.append({"type": "web_search"})
        if "x_search" in data_sources:
            tools.append({"type": "x_search"})
        if "code_interpreter" in data_sources or request.get("calculation_required", True):
            tools.append({"type": "code_interpreter"})
        raw = await oci_responses_service.generate_text(
            prompt=prompt,
            system_prompt=(
                "你是一名金融机构研究与数据分析师。使用代码解释器进行计算、数据处理和可视化，"
                "确保所有数值结果可复现。严格区分公开数据事实、模型计算结果和分析推断；"
                "所有计算步骤必须透明可验证。\n\n"
                + SIMPLIFIED_CHINESE_OUTPUT_RULE
            ),
            temperature=0.1,
            max_tokens=6000,
            tools=tools or None,
            model_id=request.get("model_id") or settings.OCI_GROK_MODEL_ID,
        )
        result = self._normalize_live_result(
            workflow="research-agent",
            raw=raw,
            request=request,
            framework=RESEARCH_AGENT_DIMENSIONS,
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
地区/国家/地区：{regions or '不限定'}
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
    def _sanctions_news_prompt(request: Dict[str, Any]) -> str:
        focuses = ", ".join(request.get("risk_focus") or ["sanctions", " adverse_media", "litigation"])
        jurisdictions = ", ".join(request.get("jurisdictions") or [])
        return f"""
基于公开信息审查下列实体的制裁、负面新闻与合规风险。

审查对象：{request.get('entity_name')}
对象类型：{request.get('entity_type')}
相关司法管辖区：{jurisdictions or '全球'}
风险维度：{focuses}
审查窗口：最近 {request.get('window_days', 30)} 天
补充背景：{request.get('additional_context') or '无'}

使用 X Search 和 Web Search 检索以下信息：
1. 制裁名单匹配（OFAC SDN、EU、UN、本地制裁）
2. 负面媒体报道（腐败、欺诈、环境违规、人权问题）
3. 监管行动（罚款、禁令、调查）
4. 诉讼与仲裁（公开案件记录）
5. 受益所有权线索（如有公开信息）

仅返回符合下列结构的 JSON：
{{
  "executive_summary": "中文合规风险简报",
  "overall_risk_level": "low|moderate|high|critical|unrated",
  "findings": [
    {{
      "category": "sanctions|adverse_media|regulatory|litigation|beneficial_ownership",
      "label": "中文分类名称",
      "severity": "low|moderate|high|critical",
      "finding": "中文发现描述",
      "evidence_status": "verified|reported|unverified",
      "source_refs": ["来源 URL 或标识"],
      "recommended_action": "中文建议后续动作"
    }}
  ],
  "sanctions_lists_checked": ["已检查的制裁名单"],
  "coverage_note": "说明检索覆盖范围和局限性",
  "unknowns": ["待核实事项"],
  "warnings": ["重要风险提示"]
}}

不确定的信息必须标注为"待核实"。不得编造制裁名单条目或法律结论。

{SIMPLIFIED_CHINESE_OUTPUT_RULE}
""".strip()

    @staticmethod
    def _market_funding_prompt(request: Dict[str, Any]) -> str:
        regions = ", ".join(request.get("regions") or [])
        indicators = ", ".join(request.get("indicators") or [])
        return f"""
基于公开数据和可靠来源分析以下市场与融资环境主题。

研究主题：{request.get('topic')}
关注地区：{regions or '全球'}
关键指标：{indicators}
时间窗口：最近 {request.get('window_days', 30)} 天
分析周期：{request.get('horizon', 'one_month')}
决策背景：{request.get('decision_context') or '无特定决策背景'}

使用 X Search、Web Search 和 Code Interpreter 分析：
1. 利率环境（政策利率、国债收益率、贷款利率趋势）
2. 汇率走势（主要货币对、新兴市场货币、汇率波动性）
3. 信用利差（投资级 vs 高收益、主权债利差）
4. 大宗商品价格（能源、金属、农产品价格趋势）
5. 融资条件（银团贷款市场、债券发行、DFI 融资窗口）

仅返回符合下列结构的 JSON：
{{
  "executive_summary": "中文市场环境简报",
  "key_findings": [
    {{
      "indicator": "interest_rate|exchange_rate|credit_spread|commodity|funding_condition",
      "label": "中文指标名称",
      "current_assessment": "中文当前状况",
      "trend": "rising|stable|falling|volatile|unknown",
      "impact_on_aiib": "对融资活动的中文影响分析",
      "evidence_refs": ["来源 URL"],
      "data_points": ["关键数据点"]
    }}
  ],
  "market_outlook": "中文市场展望",
  "risks_to_watch": ["需关注的风险因素"],
  "recommendations": ["对融资决策的中文建议"],
  "coverage_note": "数据来源说明",
  "unknowns": ["数据缺口或不确定事项"]
}}

{SIMPLIFIED_CHINESE_OUTPUT_RULE}
""".strip()

    @staticmethod
    def _research_agent_prompt(request: Dict[str, Any]) -> str:
        data_sources = ", ".join(request.get("data_sources") or ["web_search", "code_interpreter"])
        return f"""
执行以下研究与数据分析任务，确保所有结果可核验。

研究问题：{request.get('query')}
可用工具：{data_sources}
是否需要计算：{'是' if request.get('calculation_required', True) else '否'}
校验深度：{request.get('verification_level', 'detailed')}
最大返回条数：{request.get('max_results', 30)}

执行步骤：
1. 数据采集：通过指定工具获取相关公开数据
2. 计算分析：使用代码解释器进行数据处理、统计分析或趋势计算
3. 事实校验：交叉验证关键数据点，标注数据来源
4. 结构化输出：将分析结果组织为可审计的格式

仅返回符合下列结构的 JSON：
{{
  "executive_summary": "中文研究结论简报",
  "methodology": "分析方法说明",
  "data_collection": [
    {{
      "source": "数据来源名称",
      "tool_used": "使用的工具",
      "data_points": ["获取的关键数据"],
      "coverage": "来源覆盖说明"
    }}
  ],
  "computation_results": [
    {{
      "description": "计算内容描述",
      "method": "计算方法",
      "result": "计算结果",
      "reproducible": true,
      "code_snippet": "可复现的代码片段（如有）"
    }}
  ],
  "verification": {{
    "cross_references": ["交叉验证来源"],
    "confidence_level": "high|moderate|low",
    "data_quality_notes": ["数据质量说明"]
  }},
  "findings": [
    {{
      "finding": "中文研究发现",
      "evidence_status": "data_backed|model_inferred|unverified",
      "source_refs": ["来源引用"]
    }}
  ],
  "assumptions": ["分析假设"],
  "unknowns": ["数据缺口或待深入研究事项"],
  "limitations": ["分析局限性说明"]
}}

所有计算步骤必须透明可验证。不得编造数据或统计结果。

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
            "forecast_governance": self._forecast_governance(analysis),
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
            "forecast_governance": self._forecast_governance(analysis),
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
    def _forecast_governance(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make the boundary between scenario reasoning and calibrated forecasts explicit."""
        scenario_keys = {"scenarios", "forecast", "forecasts", "outlook", "trends"}
        has_scenario_language = bool(scenario_keys.intersection(analysis.keys()))
        return {
            "contains_scenario_reasoning": has_scenario_language,
            "calibration_status": "not_calibrated",
            "probability_semantics": "qualitative_only",
            "historical_backtest": "not_available",
            "decision_use": "research_and_human_review_only",
            "required_before_automated_use": [
                "明确预测事件与截止时间",
                "保存预测生成时点和信息集",
                "使用历史样本进行概率校准与分层回测",
                "记录命中率、Brier 分数和失效条件",
            ],
        }

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
