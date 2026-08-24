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
                "You are a real-time open-source intelligence researcher. Preserve cited X post "
                "text when requested, keep public-web evidence separate, and never claim exhaustive "
                "coverage. Distinguish source text, facts, opinions, reported claims, and inference. "
                "Do not invent authors, timestamps, URLs, quotations, or source content."
            ),
            source_channels=source_channels,
            from_date=from_date,
            to_date=to_date,
            use_code_interpreter=bool(request.get("use_code_interpreter", True)),
            model_id=settings.OCI_GROK_MODEL_ID,
            max_tokens=6500,
            temperature=0.1,
        )
        return self._normalize_realtime_research(raw, request, from_date, to_date)

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
                "You are an institutional project-risk analyst. Be direct and evidence-led. "
                "Do not soften material default, political, social-conflict, environmental, "
                "or reputation risks. Distinguish facts, reported claims, opinions, and inference. "
                "Never invent a source or imply that a financing decision has been approved."
            ),
            temperature=0.15,
            max_tokens=5000,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=settings.OCI_GROK_MODEL_ID,
        )
        return self._normalize_live_result(
            workflow="project-risk",
            raw=raw,
            request=request,
            framework=PROJECT_RISK_DIMENSIONS,
        )

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
                "You are a senior multilateral-development-bank strategy team. Use explicit "
                "causal chains and competing hypotheses. Present trade-offs and likely second-order "
                "effects directly. Separate sourced observations from inference, state assumptions, "
                "and never manufacture certainty, consensus, or citations."
            ),
            temperature=0.2,
            max_tokens=6500,
            source_channels=["x", "web"],
            from_date=from_date,
            use_code_interpreter=True,
            model_id=settings.OCI_GROK_MULTI_AGENT_MODEL_ID,
        )
        return self._normalize_live_result(
            workflow="geopolitical-impact",
            raw=raw,
            request=request,
            framework=GEOPOLITICAL_IMPACT_DIMENSIONS,
        )

    @staticmethod
    def _project_risk_prompt(request: Dict[str, Any]) -> str:
        focuses = ", ".join(request.get("risk_focus") or [item["label"] for item in PROJECT_RISK_DIMENSIONS])
        return f"""
Analyze current project-level risk using X Search, public Web Search, and cited evidence.

Country/member: {request.get('country')}
Project: {request.get('project_name')}
Financial product: {request.get('product_type')}
Monitoring window: last {request.get('window_days', 7)} days
Priority dimensions: {focuses}
Decision question: {request.get('monitoring_question') or 'What changed, why does it matter, and what should the investment and risk teams review now?'}

Return JSON only with this shape:
{{
  "executive_summary": "concise cited briefing",
  "direct_assessment": "plain, unsoftened assessment of the most material risk",
  "overall_risk": "low|moderate|high|critical|unrated",
  "risk_dimensions": [
    {{"dimension": "political|social|debt|environment|reputation", "label": "display label", "score": 0, "level": "low|moderate|high|critical|unrated", "trend": "rising|stable|falling|unknown", "rationale": "reason"}}
  ],
  "events": [
    {{"title": "event", "observed_at": "date or unknown", "evidence_status": "verified_source|reported_claim|opinion|unverified", "impact": "project impact", "source_refs": ["citation URL or source label"]}}
  ],
  "decision_options": [
    {{"action": "continue|adjust_terms|pause_for_review|accelerate|escalate", "urgency": "now|7_days|30_days|monitor", "owner": "team", "trigger": "observable trigger", "rationale": "why"}}
  ],
  "watch_items": ["specific next signal"],
  "assumptions": ["material assumption"]
}}

Scores are 0-100 and must be evidence-based. Use "unrated" and null-like omission when evidence is insufficient. Do not claim that social-media sentiment proves an event.
""".strip()

    @staticmethod
    def _geopolitical_prompt(request: Dict[str, Any]) -> str:
        regions = ", ".join(request.get("regions") or [])
        actors = ", ".join(request.get("actors") or [])
        products = ", ".join(request.get("product_types") or [])
        return f"""
Analyze how a geopolitical development may affect multilateral development financing.

Issue/event: {request.get('issue')}
Regions/member countries: {regions or 'not constrained'}
Actors to track: {actors or 'relevant governments, officials, think tanks, media, and financing partners'}
Financial products: {products or 'sovereign loans, non-sovereign finance, guarantees, and co-financing'}
Decision horizon: {request.get('horizon')}
Realtime evidence window: last {request.get('window_days', 30)} days
Decision question: {request.get('decision_question') or 'How could this change pipeline, co-financing, borrowing appetite, feasibility, and risk transfer?'}

Use X Search for current public statements and Web Search for official, institutional, think-tank, and media evidence. Keep the channels distinguishable and return JSON only:
{{
  "executive_summary": "direct conclusion",
  "direct_assessment": "what decision-makers should not ignore",
  "transmission_paths": [
    {{"driver": "change", "mechanism": "causal link", "financing_effect": "effect", "affected_parties": ["party"], "evidence_status": "sourced|inference|uncertain"}}
  ],
  "scenarios": [
    {{"name": "baseline|stress|opportunity", "probability": "qualitative range", "early_signals": ["observable signal"], "pipeline_impact": "impact", "cofinancing_impact": "impact", "borrowing_appetite": "impact", "feasibility": "impact", "risk_transfer": "impact"}}
  ],
  "decision_options": [
    {{"action": "option", "timing": "now|30_days|quarter", "upside": "benefit", "downside": "cost/risk", "trigger": "observable condition", "owner": "team"}}
  ],
  "stakeholder_positions": [
    {{"stakeholder": "actor", "position": "stated position", "evidence_status": "official|reported|opinion|inferred"}}
  ],
  "assumptions": ["assumption"],
  "unknowns": ["important unknown"]
}}

Avoid vague diplomatic wording. Do not present inference as an official position. Do not assign false numeric probabilities.
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
Research the topic across the selected real-time source channels.

Topic/question: {request.get('query')}
Keywords and aliases: {keywords or 'derive only necessary aliases from the topic'}
Date range: {from_date or 'not constrained'} through {to_date or 'now'}
Selected channels: {channels}
Maximum requested items: {request.get('max_results', 30)}
Preserve cited X original text: {'yes' if preserve_original else 'no'}

Important coverage rule: this is a best-effort search result, not a complete export of X or the public web. Never describe it as exhaustive or "all posts". Do not repeat near-duplicate reposts. Keep a cited source URL on every item when the provider supplies one.

Return JSON only with this shape:
{{
  "executive_summary": "what changed and why it matters",
  "coverage_note": "plain statement of query scope and limitations",
  "trends": [
    {{"label": "trend", "direction": "rising|stable|falling|unclear", "evidence": "short basis", "source_refs": ["URL"]}}
  ],
  "items": [
    {{
      "source_type": "x|public",
      "title": "post descriptor or public page headline",
      "author": "account or publisher, or unknown",
      "published_at": "ISO date/time or unknown",
      "original_text": "verbatim X post text when available, otherwise empty",
      "content_excerpt": "concise public-page excerpt or X context",
      "url": "source URL or empty if unavailable",
      "evidence_status": "source_available|reported_claim|opinion|unverified",
      "matched_keywords": ["keyword"]
    }}
  ],
  "unknowns": ["important missing or unverified point"]
}}

For X, keep original_text faithful to the cited post and do not reconstruct missing text. For public pages, do not place paraphrases in original_text. Use code interpretation only to deduplicate, count, or calculate trends from retrieved evidence; do not manufacture missing observations.
""".strip()

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
