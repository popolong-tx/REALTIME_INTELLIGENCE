from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re
import logging

from app.services.verification_service import verification_service, VerificationStatus
from app.services.citation_tracker import citation_tracker

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class ValidationResult:
    """Result of LLM output validation."""

    def __init__(
        self,
        is_valid: bool,
        issues: List[Dict[str, Any]],
        warnings: List[str],
        sanitized_output: str,
        validation_level: ValidationLevel,
    ):
        self.is_valid = is_valid
        self.issues = issues
        self.warnings = warnings
        self.sanitized_output = sanitized_output
        self.validation_level = validation_level

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "issues": self.issues,
            "warnings": self.warnings,
            "sanitized_output": self.sanitized_output,
            "validation_level": self.validation_level.value,
        }


class LLMOutputValidator:
    """Validator for LLM outputs to ensure quality and compliance."""

    # Prohibited phrases
    PROHIBITED_PHRASES = [
        "guaranteed returns",
        "guaranteed profit",
        "risk-free",
        "no risk",
        "certain to rise",
        "certain to fall",
        "will definitely",
        "100% sure",
        "cannot lose",
        "sure thing",
        "easy money",
        "get rich quick",
    ]

    # Financial advice disclaimers
    DISCLAIMER_REQUIRED_PATTERNS = [
        r"(buy|sell|hold|invest|trade)\s+(stock|shares?|securities?)",
        r"(recommend|suggest|advise)\s+(buying|selling|holding|investing)",
        r"(target|expected)\s+(price|return|profit)",
    ]

    def __init__(self):
        self.validation_level = ValidationLevel.MODERATE

    async def validate_output(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        validation_level: Optional[ValidationLevel] = None,
    ) -> ValidationResult:
        """Validate LLM output."""
        level = validation_level or self.validation_level
        issues = []
        warnings = []
        sanitized = output

        # Check for prohibited phrases
        prohibited_issues = self._check_prohibited_phrases(output)
        issues.extend(prohibited_issues)

        # Check for unsubstantiated claims
        claim_issues = await self._check_unsubstantiated_claims(output)
        issues.extend(claim_issues)

        # Check for missing disclaimers
        disclaimer_issues = self._check_disclaimer_requirement(output)
        issues.extend(disclaimer_issues)

        # Check for hallucination indicators
        hallucination_warnings = self._check_hallucination_indicators(output)
        warnings.extend(hallucination_warnings)

        # Sanitize output if needed
        if issues:
            sanitized = self._sanitize_output(output, issues)

        # Determine if valid
        is_valid = len(issues) == 0 or (
            level == ValidationLevel.LENIENT and
            not any(i["severity"] == "critical" for i in issues)
        )

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            sanitized_output=sanitized,
            validation_level=level,
        )

    def _check_prohibited_phrases(self, output: str) -> List[Dict[str, Any]]:
        """Check for prohibited phrases."""
        issues = []
        output_lower = output.lower()

        for phrase in self.PROHIBITED_PHRASES:
            if phrase in output_lower:
                issues.append({
                    "type": "prohibited_phrase",
                    "severity": "critical",
                    "phrase": phrase,
                    "message": f"Prohibited phrase detected: '{phrase}'",
                    "suggestion": "Remove or rephrase to avoid making guarantees",
                })

        return issues

    async def _check_unsubstantiated_claims(self, output: str) -> List[Dict[str, Any]]:
        """Check for unsubstantiated claims."""
        issues = []

        # Extract potential claims
        claims = self._extract_claims(output)

        for claim in claims:
            # Verify claim against citations
            verification = await verification_service.verify_claim(claim)

            if verification.status == VerificationStatus.UNVERIFIED:
                issues.append({
                    "type": "unsubstantiated_claim",
                    "severity": "warning",
                    "claim": claim,
                    "message": "Claim may be unsubstantiated",
                    "suggestion": "Add citation or mark as unverified",
                })

        return issues

    def _check_disclaimer_requirement(self, output: str) -> List[Dict[str, Any]]:
        """Check if disclaimer is required."""
        issues = []

        # Check if output contains financial advice patterns
        contains_advice = any(
            re.search(pattern, output, re.IGNORECASE)
            for pattern in self.DISCLAIMER_REQUIRED_PATTERNS
        )

        if contains_advice:
            # Check if disclaimer is present
            disclaimer_present = any(
                phrase in output.lower()
                for phrase in [
                    "not financial advice",
                    "not investment advice",
                    "for informational purposes",
                    "consult a professional",
                    "do your own research",
                ]
            )

            if not disclaimer_present:
                issues.append({
                    "type": "missing_disclaimer",
                    "severity": "critical",
                    "message": "Financial advice detected without disclaimer",
                    "suggestion": "Add disclaimer: 'This is not financial advice. Consult a professional before making investment decisions.'",
                })

        return issues

    def _check_hallucination_indicators(self, output: str) -> List[str]:
        """Check for indicators of hallucination."""
        warnings = []

        # Check for very specific numbers without sources
        specific_numbers = re.findall(r'\$[\d,]+\.?\d*|\d+\.?\d*%', output)
        if specific_numbers and "source" not in output.lower():
            warnings.append("Specific numbers detected without source attribution")

        # Check for future predictions
        future_patterns = [
            r"will\s+(rise|fall|increase|decrease|reach|hit)",
            r"is\s+expected\s+to",
            r"is\s+likely\s+to",
            r"predicted\s+to",
        ]
        for pattern in future_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                warnings.append("Future prediction detected - ensure proper hedging language")
                break

        # Check for absolute statements
        absolute_patterns = [
            r"always\s+(rise|fall|increase|decrease)",
            r"never\s+(rise|fall|increase|decrease)",
            r"definitely\s+(will|won't)",
        ]
        for pattern in absolute_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                warnings.append("Absolute statement detected - consider using hedging language")
                break

        return warnings

    def _extract_claims(self, text: str) -> List[str]:
        """Extract potential claims from text."""
        claims = []

        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filter out very short fragments
                # Check if it looks like a factual claim
                if any(keyword in sentence.lower() for keyword in [
                    "is", "are", "was", "were", "has", "have", "had",
                    "shows", "indicates", "suggests", "reports",
                ]):
                    claims.append(sentence)

        return claims[:10]  # Limit to 10 claims

    def _sanitize_output(self, output: str, issues: List[Dict[str, Any]]) -> str:
        """Sanitize output by addressing issues."""
        sanitized = output

        # Add disclaimer if missing
        has_disclaimer_issue = any(
            i["type"] == "missing_disclaimer" for i in issues
        )
        if has_disclaimer_issue:
            disclaimer = "\n\n---\n**Disclaimer:** This is not financial advice. Consult a professional before making investment decisions.\n"
            sanitized += disclaimer

        # Mark unverified claims
        unverified_claims = [
            i for i in issues if i["type"] == "unsubstantiated_claim"
        ]
        for claim_issue in unverified_claims:
            claim = claim_issue.get("claim", "")
            if claim in sanitized:
                sanitized = sanitized.replace(
                    claim,
                    f"{claim} [unverified]"
                )

        return sanitized

    def set_validation_level(self, level: ValidationLevel) -> None:
        """Set validation level."""
        self.validation_level = level

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules."""
        return {
            "validation_level": self.validation_level.value,
            "prohibited_phrases": self.PROHIBITED_PHRASES,
            "disclaimer_required_patterns": self.DISCLAIMER_REQUIRED_PATTERNS,
        }


# Global validator instance
llm_output_validator = LLMOutputValidator()
