from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class LanguageCheckResult:
    """Result of language check."""

    def __init__(
        self,
        is_clean: bool,
        violations: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        sanitized_text: str,
    ):
        self.is_clean = is_clean
        self.violations = violations
        self.warnings = warnings
        self.sanitized_text = sanitized_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_clean": self.is_clean,
            "violations": self.violations,
            "warnings": self.warnings,
            "sanitized_text": self.sanitized_text,
        }


class ProhibitedLanguageService:
    """Service for detecting and preventing prohibited language."""

    # Prohibited patterns with severity
    PROHIBITED_PATTERNS = [
        # Guaranteed returns
        {"pattern": r"guaranteed\s+(returns?|profit|income)", "severity": "critical", "message": "Cannot guarantee returns"},
        {"pattern": r"risk[\s-]*free", "severity": "critical", "message": "Cannot claim risk-free"},
        {"pattern": r"no\s+risk", "severity": "critical", "message": "Cannot claim no risk"},
        {"pattern": r"zero\s+risk", "severity": "critical", "message": "Cannot claim zero risk"},
        {"pattern": r"certain\s+to\s+(rise|fall|increase|decrease|profit)", "severity": "critical", "message": "Cannot make certain predictions"},
        {"pattern": r"will\s+definitely", "severity": "critical", "message": "Cannot use definite predictions"},
        {"pattern": r"100%\s+(sure|guaranteed|certain)", "severity": "critical", "message": "Cannot use absolute guarantees"},
        {"pattern": r"cannot\s+(lose|fail)", "severity": "critical", "message": "Cannot claim impossibility of loss"},
        {"pattern": r"sure\s+thing", "severity": "critical", "message": "Cannot use 'sure thing'"},
        {"pattern": r"easy\s+money", "severity": "critical", "message": "Cannot promise easy money"},
        {"pattern": r"get\s+rich\s+quick", "severity": "critical", "message": "Cannot promise quick riches"},

        # Misleading claims
        {"pattern": r"always\s+(profit|win|gain)", "severity": "high", "message": "Cannot claim always winning"},
        {"pattern": r"never\s+(lose|fail|decline)", "severity": "high", "message": "Cannot claim never losing"},
        {"pattern": r"secret\s+(formula|strategy|method)", "severity": "medium", "message": "Avoid 'secret' claims"},
        {"pattern": r"insider\s+(information|tip|knowledge)", "severity": "critical", "message": "Cannot reference insider information"},
        {"pattern": r"manipulat(e|ing)\s+(the\s+)?market", "severity": "critical", "message": "Cannot reference market manipulation"},
    ]

    # Warning patterns (not violations but should be reviewed)
    WARNING_PATTERNS = [
        {"pattern": r"(buy|sell|hold)\s+now", "message": "Urgency language detected"},
        {"pattern": r"(last|final)\s+chance", "message": "Urgency language detected"},
        {"pattern": r"(limited|exclusive)\s+(time|offer)", "message": "Urgency language detected"},
        {"pattern": r"(don'?t|do\s+not)\s+miss", "message": "Urgency language detected"},
        {"pattern": r"act\s+(now|fast|quickly)", "message": "Urgency language detected"},
        {"pattern": r"(best|top|number\s+one)\s+(stock|pick|investment)", "message": "Superlative claim detected"},
    ]

    def check_text(
        self,
        text: str,
        context: Optional[str] = None,
    ) -> LanguageCheckResult:
        """Check text for prohibited language."""
        violations = []
        warnings = []
        sanitized = text

        # Check prohibited patterns
        for rule in self.PROHIBITED_PATTERNS:
            matches = re.finditer(rule["pattern"], text, re.IGNORECASE)
            for match in matches:
                violations.append({
                    "type": "prohibited",
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "matched_text": match.group(),
                    "position": match.span(),
                    "context": context,
                })

                # Sanitize by replacing with [REDACTED]
                sanitized = sanitized.replace(match.group(), "[REDACTED]")

        # Check warning patterns
        for rule in self.WARNING_PATTERNS:
            matches = re.finditer(rule["pattern"], text, re.IGNORECASE)
            for match in matches:
                warnings.append({
                    "type": "warning",
                    "message": rule["message"],
                    "matched_text": match.group(),
                    "position": match.span(),
                    "context": context,
                })

        return LanguageCheckResult(
            is_clean=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            sanitized_text=sanitized,
        )

    def check_recommendation(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check recommendation for prohibited language."""
        all_violations = []
        all_warnings = []

        # Check reasoning
        reasoning = recommendation.get("reasoning", "")
        if reasoning:
            result = self.check_text(reasoning, "reasoning")
            all_violations.extend(result.violations)
            all_warnings.extend(result.warnings)

        # Check summary
        summary = recommendation.get("summary", "")
        if summary:
            result = self.check_text(summary, "summary")
            all_violations.extend(result.violations)
            all_warnings.extend(result.warnings)

        # Check disclaimers
        disclaimers = recommendation.get("disclaimers", [])
        for disclaimer in disclaimers:
            result = self.check_text(disclaimer, "disclaimer")
            all_violations.extend(result.violations)
            all_warnings.extend(result.warnings)

        return {
            "is_compliant": len(all_violations) == 0,
            "violations": all_violations,
            "warnings": all_warnings,
            "violation_count": len(all_violations),
            "warning_count": len(all_warnings),
            "checked_at": datetime.utcnow().isoformat(),
        }

    def sanitize_text(self, text: str) -> str:
        """Sanitize text by removing prohibited language."""
        sanitized = text

        for rule in self.PROHIBITED_PATTERNS:
            sanitized = re.sub(rule["pattern"], "[REDACTED]", sanitized, flags=re.IGNORECASE)

        return sanitized

    def get_prohibited_phrases(self) -> List[Dict[str, str]]:
        """Get list of prohibited phrases."""
        return [
            {
                "pattern": rule["pattern"],
                "severity": rule["severity"],
                "message": rule["message"],
            }
            for rule in self.PROHIBITED_PATTERNS
        ]

    def get_warning_phrases(self) -> List[Dict[str, str]]:
        """Get list of warning phrases."""
        return [
            {
                "pattern": rule["pattern"],
                "message": rule["message"],
            }
            for rule in self.WARNING_PATTERNS
        ]

    def add_custom_prohibited_phrase(
        self,
        pattern: str,
        severity: str = "high",
        message: str = "",
    ) -> None:
        """Add custom prohibited phrase."""
        self.PROHIBITED_PATTERNS.append({
            "pattern": pattern,
            "severity": severity,
            "message": message or f"Custom prohibited phrase: {pattern}",
        })

    def add_custom_warning_phrase(
        self,
        pattern: str,
        message: str = "",
    ) -> None:
        """Add custom warning phrase."""
        self.WARNING_PATTERNS.append({
            "pattern": pattern,
            "message": message or f"Custom warning phrase: {pattern}",
        })


# Global service instance
prohibited_language_service = ProhibitedLanguageService()
