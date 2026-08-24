"""Backward-compatible facade for the canonical OCI Responses adapter."""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.oci_responses_service import oci_responses_service


class OCIGenerativeAIClient:
    """Preserve older call sites while keeping all traffic inside OCI."""

    def __init__(self) -> None:
        self.region = settings.OCI_REGION
        self.model_id = settings.OCI_GROK_MODEL_ID

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        return await oci_responses_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_id=self.model_id,
        )

    async def search_x_posts(
        self,
        query: str,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        return await oci_responses_service.search_x(
            query=query,
            max_results=max_results,
        )


oci_client = OCIGenerativeAIClient()
