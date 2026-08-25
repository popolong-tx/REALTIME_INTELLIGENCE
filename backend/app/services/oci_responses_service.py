"""OCI Generative AI Responses API adapter for Grok research workflows.

The adapter intentionally uses OCI's Responses endpoint rather than the direct
xAI or X APIs. This keeps model inference, X Search, citations, and audit
metadata behind one provider boundary.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json
import logging

import httpx

from app.core.cache import cache
from app.core.config import settings

logger = logging.getLogger(__name__)


class OCIResponsesError(RuntimeError):
    """Provider error that keeps safe compatibility details for fallbacks."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"OCI Responses API error ({status_code}): {detail}")
        self.status_code = status_code
        self.detail = detail


class OCIResponsesService:
    """Small, provider-specific adapter around OCI's Open Responses endpoint."""

    def __init__(self) -> None:
        self.region = settings.OCI_REGION
        self.model_id = settings.OCI_GROK_MODEL_ID
        self.multi_agent_model_id = settings.OCI_GROK_MULTI_AGENT_MODEL_ID
        self.api_key = settings.OCI_GENAI_API_KEY
        self.base_url = (
            settings.OCI_GENAI_BASE_URL
            or f"https://inference.generativeai.{self.region}.oci.oraclecloud.com"
            "/20231130/actions/v1"
        )
        self.endpoint = f"{self.base_url.rstrip('/')}/responses"

    @property
    def configured(self) -> bool:
        """Return configuration state without exposing credentials."""
        return bool(self.api_key and self.model_id and self.region)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        tools: Optional[List[Dict[str, Any]]] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text with optional OCI-managed xAI tools.

        The returned object preserves the compatibility fields used by the
        existing API layer while also exposing citations and tool calls.
        """
        if not self.api_key:
            raise RuntimeError(
                "OCI Generative AI API key is not configured; set "
                "OCI_GENAI_API_KEY"
            )

        selected_model = model_id or self.model_id
        body: Dict[str, Any] = {
            "model": selected_model,
            "input": prompt,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": top_p,
        }
        if system_prompt:
            body["instructions"] = system_prompt
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        cache_material = json.dumps(
            {
                "model": selected_model,
                "prompt": prompt,
                "system": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "tools": tools,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        cache_digest = hashlib.sha256(cache_material.encode("utf-8")).hexdigest()
        cache_key = f"oci_responses:{cache_digest}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=90.0,
                )
        except httpx.TimeoutException as exc:
            raise RuntimeError("OCI Responses API timeout") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OCI Responses API network error: {exc}") from exc

        if response.status_code != 200:
            detail = self._safe_error_detail(response)
            logger.error(
                "OCI Responses API request failed: status=%s model=%s detail=%s",
                response.status_code,
                selected_model,
                detail,
            )
            raise OCIResponsesError(response.status_code, detail)

        raw = response.json()
        text = self._extract_output_text(raw)
        citations = self._extract_citations(raw)
        result = dict(raw)
        result["output_text"] = text
        result["inferenceResponse"] = {"text": text}
        result["citations"] = citations
        result["tool_calls"] = raw.get("tool_calls") or self._extract_tool_calls(raw)
        result["metadata"] = {
            "provider": "oci-generative-ai",
            "model_id": selected_model,
            "region": self.region,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "generated_at": datetime.utcnow().isoformat(),
            "request_id": response.headers.get("opc-request-id")
            or response.headers.get("x-request-id"),
            "tools": [tool.get("type") for tool in tools or []],
        }
        cache.set(cache_key, result, expire=900 if tools else 3600)
        return result

    async def generate_realtime_research(
        self,
        prompt: str,
        system_prompt: str,
        *,
        source_channels: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        use_code_interpreter: bool = True,
        model_id: Optional[str] = None,
        max_tokens: int = 5000,
        temperature: float = 0.15,
    ) -> Dict[str, Any]:
        """Run governed X/public research with a narrow compatibility fallback.

        OCI currently documents xAI-compatible X Search and Code Interpreter.
        Some Responses-compatible deployments also accept xAI Web Search.  The
        first request uses all selected tools; only an explicit tool-validation
        error can remove an unsupported tool. Authentication, quota, timeout,
        and network failures are always surfaced to the caller.
        """
        channels = list(dict.fromkeys(source_channels or ["x", "web"]))
        tools: List[Dict[str, Any]] = []
        if "web" in channels:
            tools.append({"type": "web_search"})
        if "x" in channels:
            x_tool: Dict[str, Any] = {"type": "x_search"}
            if from_date:
                x_tool["from_date"] = from_date
            if to_date:
                x_tool["to_date"] = to_date
            tools.append(x_tool)
        if use_code_interpreter:
            tools.append({"type": "code_interpreter"})

        requested_types = [tool["type"] for tool in tools]
        compatibility_warnings: List[str] = []
        attempt_tools = tools
        for _ in range(len(tools) + 1):
            try:
                result = await self.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=attempt_tools,
                    model_id=model_id,
                )
                used_types = [tool["type"] for tool in attempt_tools]
                degraded_types = [item for item in requested_types if item not in used_types]
                metadata = result.setdefault("metadata", {})
                metadata.update({
                    "requested_tools": requested_types,
                    "used_tools": used_types,
                    "degraded_tools": degraded_types,
                    "tool_warnings": compatibility_warnings,
                    "coverage": "best_effort",
                })
                return result
            except OCIResponsesError as exc:
                if not self._is_tool_compatibility_error(exc):
                    raise
                rejected_tool = self._rejected_tool(exc, attempt_tools)
                if not rejected_tool:
                    raise
                next_tools = [tool for tool in attempt_tools if tool["type"] != rejected_tool]
                if not any(tool["type"] in {"web_search", "x_search"} for tool in next_tools):
                    raise
                compatibility_warnings.append(
                    f"服务提供方不支持 {rejected_tool}；已改用其余可用工具重试。"
                )
                attempt_tools = next_tools

        raise RuntimeError("没有可用的实时研究工具组合，无法完成检索。")

    async def search_x(
        self,
        query: str,
        max_results: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        allowed_x_handles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Use OCI's built-in xAI X Search tool with citation output."""
        tool: Dict[str, Any] = {"type": "x_search"}
        if from_date:
            tool["from_date"] = from_date
        if to_date:
            tool["to_date"] = to_date
        if allowed_x_handles:
            tool["allowed_x_handles"] = allowed_x_handles

        prompt = (
            f"在 X 上检索：{query}。最多返回 {max_results} 条高度相关的公开内容。"
            "使用简体中文总结检索结果，并把可验证事实、观点和个人交易声明明确分开。"
            "保留原始来源引用；X 帖子原文不得翻译或改写。"
        )
        return await self.generate_text(
            prompt=prompt,
            system_prompt=(
                "你是一名金融研究助理。除 X 原文、URL、股票代码和专有名词外，所有回复必须使用简体中文。"
                "公开帖子只是研究证据，并非已经验证的交易或投资指令。"
            ),
            temperature=0.2,
            max_tokens=2500,
            tools=[tool],
        )

    async def generate_with_context(
        self,
        query: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        context_text = "\n\n".join(
            f"来源：{item.get('source', '未知')}\n{item.get('content', '')}"
            for item in context
        )
        return await self.generate_text(
            prompt=f"上下文：\n{context_text}\n\n问题：{query}\n\n请使用简体中文回答。",
            system_prompt=system_prompt
            or "仅依据提供的金融研究上下文回答；所有面向用户的内容必须使用简体中文。",
        )

    async def summarize_text(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        return await self.generate_text(
            prompt=f"请用不超过 {max_length} 个汉字进行摘要：\n\n{text}",
            system_prompt="提供简洁、准确的简体中文摘要，不增加原文没有的事实。",
            max_tokens=max_length * 2,
        )

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        result = await self.generate_text(
            prompt=(
                "将情绪分类为正面、中性或负面，给出 0-1 置信度和支持判断的原文片段。"
                f"使用简体中文回答。文本：\n{text}"
            ),
            system_prompt="返回简洁的简体中文金融情绪分析。",
            temperature=0.2,
        )
        return {
            "text": text,
            "analysis": result["inferenceResponse"]["text"],
            "model_id": result["metadata"]["model_id"],
        }

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        result = await self.generate_text(
            prompt=(
                "从下列文本提取公司名称、股票代码、金融指标、日期和金额；"
                f"字段说明使用简体中文：\n{text}"
            ),
            system_prompt="返回结构化的金融实体清单，说明文字使用简体中文。",
            temperature=0.1,
        )
        return {
            "text": text,
            "entities": result["inferenceResponse"]["text"],
            "model_id": result["metadata"]["model_id"],
        }

    @staticmethod
    def _safe_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
            return str(payload.get("detail") or payload.get("message") or payload.get("error") or payload)[:500]
        except Exception:
            return response.text[:500] or "unknown provider error"

    @staticmethod
    def _is_tool_compatibility_error(error: OCIResponsesError) -> bool:
        if error.status_code not in {400, 422}:
            return False
        detail = error.detail.lower()
        tool_markers = {
            "tool",
            "web_search",
            "x_search",
            "code_interpreter",
            "unsupported",
            "not supported",
            "invalid type",
        }
        return any(marker in detail for marker in tool_markers)

    @staticmethod
    def _rejected_tool(
        error: OCIResponsesError,
        tools: List[Dict[str, Any]],
    ) -> Optional[str]:
        detail = error.detail.lower()
        active = [tool.get("type") for tool in tools]
        for tool_type in ["web_search", "code_interpreter", "x_search"]:
            if tool_type in active and tool_type in detail:
                return tool_type
        # OCI explicitly documents X Search and Code Interpreter for xAI
        # models. For a generic tool-validation error, probe compatibility by
        # removing Web Search first and keep the decision in the audit record.
        if "web_search" in active:
            return "web_search"
        return None

    @staticmethod
    def _extract_output_text(payload: Dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        chunks: List[str] = []
        for output in payload.get("output") or []:
            if not isinstance(output, dict):
                continue
            for content in output.get("content") or []:
                if not isinstance(content, dict):
                    continue
                text = content.get("text") or content.get("output_text")
                if isinstance(text, str):
                    chunks.append(text)
        return "\n".join(chunks).strip()

    @classmethod
    def _extract_citations(cls, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        found: List[Dict[str, Any]] = []
        raw_citations = payload.get("citations") or []
        for citation in raw_citations:
            normalized = cls._normalize_citation(citation)
            if normalized:
                found.append(normalized)

        for output in payload.get("output") or []:
            if not isinstance(output, dict):
                continue
            for content in output.get("content") or []:
                if not isinstance(content, dict):
                    continue
                for annotation in content.get("annotations") or []:
                    normalized = cls._normalize_citation(annotation)
                    if normalized:
                        found.append(normalized)

        unique: List[Dict[str, Any]] = []
        seen = set()
        for item in found:
            key = item.get("url") or json.dumps(item, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @staticmethod
    def _normalize_citation(citation: Any) -> Optional[Dict[str, Any]]:
        if isinstance(citation, str):
            return {"url": citation, "title": citation, "text": ""}
        if not isinstance(citation, dict):
            return None
        nested = citation.get("url_citation") or citation.get("citation") or citation
        if not isinstance(nested, dict):
            return None
        url = nested.get("url") or nested.get("uri")
        if not url:
            return None
        return {
            "url": url,
            "title": nested.get("title") or nested.get("name") or url,
            "text": nested.get("text") or nested.get("excerpt") or "",
        }

    @staticmethod
    def _extract_tool_calls(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            output
            for output in payload.get("output") or []
            if isinstance(output, dict) and "call" in str(output.get("type", ""))
        ]


oci_responses_service = OCIResponsesService()
