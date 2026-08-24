from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

from app.services.citation_tracker import Citation, citation_tracker

logger = logging.getLogger(__name__)


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    DISPUTED = "disputed"


class VerificationResult:
    """Result of verification check."""

    def __init__(
        self,
        status: VerificationStatus,
        citations: List[Citation],
        confidence: float,
        reasoning: str,
        checked_at: Optional[datetime] = None,
    ):
        self.status = status
        self.citations = citations
        self.confidence = confidence
        self.reasoning = reasoning
        self.checked_at = checked_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "checked_at": self.checked_at.isoformat(),
        }


class VerificationService:
    """Service for verifying information and marking unverified content."""

    # Thresholds for verification
    MIN_CITATIONS_FOR_VERIFIED = 2
    MIN_CONFIDENCE_FOR_VERIFIED = 0.7
    MIN_CITATIONS_FOR_PARTIAL = 1

    async def verify_claim(
        self,
        claim: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify a claim against available citations."""
        # Find relevant citations
        relevant_citations = citation_tracker.get_citations_for_content(claim)

        if not relevant_citations:
            return VerificationResult(
                status=VerificationStatus.UNVERIFIED,
                citations=[],
                confidence=0.0,
                reasoning="No citations found to verify this claim",
            )

        # Calculate verification score
        verification_score = self._calculate_verification_score(
            claim, relevant_citations
        )

        # Determine status
        if len(relevant_citations) >= self.MIN_CITATIONS_FOR_VERIFIED:
            if verification_score >= self.MIN_CONFIDENCE_FOR_VERIFIED:
                status = VerificationStatus.VERIFIED
            else:
                status = VerificationStatus.PARTIALLY_VERIFIED
        elif len(relevant_citations) >= self.MIN_CITATIONS_FOR_PARTIAL:
            status = VerificationStatus.PARTIALLY_VERIFIED
        else:
            status = VerificationStatus.UNVERIFIED

        return VerificationResult(
            status=status,
            citations=relevant_citations,
            confidence=verification_score,
            reasoning=self._generate_reasoning(status, relevant_citations, verification_score),
        )

    async def verify_stock_data(
        self,
        stock_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify stock data against citations."""
        verified_fields = {}
        unverified_fields = []

        for field, value in stock_data.items():
            if field in ["source", "fetched_at", "data_source"]:
                continue

            if value is not None:
                claim = f"{field}: {value}"
                result = await self.verify_claim(claim)

                if result.status == VerificationStatus.VERIFIED:
                    verified_fields[field] = {
                        "value": value,
                        "status": "verified",
                        "citations": len(result.citations),
                        "confidence": result.confidence,
                    }
                elif result.status == VerificationStatus.PARTIALLY_VERIFIED:
                    verified_fields[field] = {
                        "value": value,
                        "status": "partially_verified",
                        "citations": len(result.citations),
                        "confidence": result.confidence,
                    }
                else:
                    unverified_fields.append({
                        "field": field,
                        "value": value,
                        "status": "unverified",
                        "reason": result.reasoning,
                    })

        return {
            "verified_fields": verified_fields,
            "unverified_fields": unverified_fields,
            "verification_summary": {
                "total_fields": len(stock_data),
                "verified_count": len([f for f in verified_fields.values() if f["status"] == "verified"]),
                "partially_verified_count": len([f for f in verified_fields.values() if f["status"] == "partially_verified"]),
                "unverified_count": len(unverified_fields),
            },
        }

    async def verify_news_article(
        self,
        article: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify a news article."""
        # Check if article has source attribution
        has_source = bool(article.get("source"))
        has_url = bool(article.get("url"))
        has_author = bool(article.get("author"))
        has_published_at = bool(article.get("published_at"))

        # Calculate source credibility
        source_credibility = self._assess_source_credibility(article.get("source", ""))

        # Determine verification status
        if has_source and has_url and has_published_at:
            if source_credibility >= 0.8:
                status = VerificationStatus.VERIFIED
            else:
                status = VerificationStatus.PARTIALLY_VERIFIED
        elif has_source:
            status = VerificationStatus.PARTIALLY_VERIFIED
        else:
            status = VerificationStatus.UNVERIFIED

        return {
            "article_id": article.get("id"),
            "verification_status": status.value,
            "source_credibility": source_credibility,
            "has_source": has_source,
            "has_url": has_url,
            "has_author": has_author,
            "has_published_at": has_published_at,
            "verified_at": datetime.utcnow().isoformat(),
        }

    async def mark_as_unverified(
        self,
        content: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Explicitly mark content as unverified."""
        return {
            "content": content,
            "status": VerificationStatus.UNVERIFIED.value,
            "reason": reason,
            "marked_at": datetime.utcnow().isoformat(),
            "disclaimer": "This information has not been verified and should not be relied upon for investment decisions.",
        }

    def _calculate_verification_score(
        self,
        claim: str,
        citations: List[Citation],
    ) -> float:
        """Calculate verification score based on citations."""
        if not citations:
            return 0.0

        # Base score from number of citations
        citation_score = min(len(citations) / self.MIN_CITATIONS_FOR_VERIFIED, 1.0)

        # Average confidence of citations
        avg_confidence = sum(c.confidence for c in citations) / len(citations)

        # Source diversity bonus
        unique_sources = len(set(c.source for c in citations))
        diversity_bonus = min(unique_sources / 3, 0.3)

        # Calculate final score
        final_score = (citation_score * 0.4) + (avg_confidence * 0.4) + diversity_bonus

        return min(final_score, 1.0)

    def _assess_source_credibility(self, source: str) -> float:
        """Assess credibility of a source."""
        # High credibility sources
        high_credibility = [
            "reuters", "bloomberg", "wsj", "ft", "nyt",
            "yahoo_finance", "alpha_vantage", "sec", "edgar",
        ]

        # Medium credibility sources
        medium_credibility = [
            "seeking_alpha", "marketwatch", "cnbc", "bbc",
            "associated_press", "ap",
        ]

        source_lower = source.lower()

        if any(s in source_lower for s in high_credibility):
            return 0.9
        elif any(s in source_lower for s in medium_credibility):
            return 0.7
        else:
            return 0.5

    def _generate_reasoning(
        self,
        status: VerificationStatus,
        citations: List[Citation],
        confidence: float,
    ) -> str:
        """Generate reasoning for verification status."""
        if status == VerificationStatus.VERIFIED:
            return f"Verified by {len(citations)} sources with {confidence:.0%} confidence"
        elif status == VerificationStatus.PARTIALLY_VERIFIED:
            return f"Partially verified by {len(citations)} source(s) with {confidence:.0%} confidence"
        else:
            return "No reliable sources found to verify this information"


# Global service instance
verification_service = VerificationService()
