from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ComplianceStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING_REVIEW = "pending_review"


class ComplianceGateService:
    """Service for compliance gate checks."""

    # Prohibited phrases that cannot appear in recommendations
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
        "zero risk",
        "guaranteed income",
    ]

    # Required disclaimers
    REQUIRED_DISCLAIMERS = [
        "not financial advice",
        "not investment advice",
        "for informational purposes",
        "consult a professional",
        "do your own research",
    ]

    async def check_recommendation_compliance(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if recommendation meets compliance requirements."""
        issues = []
        warnings = []

        # Check for prohibited phrases
        prohibited_check = self._check_prohibited_phrases(recommendation)
        if not prohibited_check["passed"]:
            issues.extend(prohibited_check["issues"])

        # Check for required disclaimers
        disclaimer_check = self._check_disclaimers(recommendation)
        if not disclaimer_check["passed"]:
            issues.extend(disclaimer_check["issues"])

        # Check for proper risk warnings
        risk_check = self._check_risk_warnings(recommendation)
        if not risk_check["passed"]:
            warnings.extend(risk_check["warnings"])

        # Check for source attribution
        source_check = self._check_source_attribution(recommendation)
        if not source_check["passed"]:
            warnings.extend(source_check["warnings"])

        # Determine overall status
        if issues:
            status = ComplianceStatus.FAILED
        elif warnings:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.PASSED

        return {
            "status": status.value,
            "passed": status == ComplianceStatus.PASSED,
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def check_model_compliance(
        self,
        model: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if model meets compliance requirements."""
        issues = []
        warnings = []

        # Check model documentation
        if not model.get("description"):
            warnings.append("Model missing description")

        # Check validation metrics
        if not model.get("validation_metrics"):
            issues.append("Model missing validation metrics")

        # Check backtest results
        if not model.get("backtest_results"):
            warnings.append("Model missing backtest results")

        # Check approval status
        if model.get("status") not in ["approved", "deployed"]:
            issues.append("Model not approved for use")

        # Determine overall status
        if issues:
            status = ComplianceStatus.FAILED
        elif warnings:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.PASSED

        return {
            "status": status.value,
            "passed": status == ComplianceStatus.PASSED,
            "issues": issues,
            "warnings": warnings,
            "model_id": model.get("id"),
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def check_data_compliance(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if data usage meets compliance requirements."""
        issues = []
        warnings = []

        # Check data source attribution
        if not data.get("source"):
            issues.append("Data missing source attribution")

        # Check data freshness
        fetched_at = data.get("fetched_at")
        if fetched_at:
            try:
                fetch_time = datetime.fromisoformat(fetched_at)
                age_hours = (datetime.utcnow() - fetch_time).total_seconds() / 3600
                if age_hours > 24:
                    warnings.append(f"Data is {age_hours:.0f} hours old")
            except (ValueError, TypeError):
                pass

        # Check data completeness
        if not data.get("data") and not data.get("content"):
            warnings.append("Data appears incomplete")

        # Determine overall status
        if issues:
            status = ComplianceStatus.FAILED
        elif warnings:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.PASSED

        return {
            "status": status.value,
            "passed": status == ComplianceStatus.PASSED,
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def _check_prohibited_phrases(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check for prohibited phrases in recommendation."""
        issues = []

        # Check in reasoning
        reasoning = recommendation.get("reasoning", "")
        for phrase in self.PROHIBITED_PHRASES:
            if phrase.lower() in reasoning.lower():
                issues.append(f"Prohibited phrase found: '{phrase}'")

        # Check in summary
        summary = recommendation.get("summary", "")
        for phrase in self.PROHIBITED_PHRASES:
            if phrase.lower() in summary.lower():
                issues.append(f"Prohibited phrase found in summary: '{phrase}'")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
        }

    def _check_disclaimers(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check for required disclaimers."""
        issues = []

        disclaimers = recommendation.get("disclaimers", [])
        disclaimers_text = " ".join(disclaimers).lower()

        # Check if at least one required disclaimer is present
        has_disclaimer = any(
            phrase in disclaimers_text
            for phrase in self.REQUIRED_DISCLAIMERS
        )

        if not has_disclaimer:
            issues.append("Missing required disclaimer about financial advice")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
        }

    def _check_risk_warnings(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check for proper risk warnings."""
        warnings = []

        risk_level = recommendation.get("risk_level")
        if risk_level in ["high", "very_high"]:
            # Check if high risk warning is present
            disclaimers = recommendation.get("disclaimers", [])
            has_risk_warning = any(
                "risk" in d.lower() and "high" in d.lower()
                for d in disclaimers
            )
            if not has_risk_warning:
                warnings.append("High risk recommendation missing explicit risk warning")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
        }

    def _check_source_attribution(
        self,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check for proper source attribution."""
        warnings = []

        citations = recommendation.get("citations", [])
        if not citations:
            warnings.append("Recommendation lacks source citations")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
        }

    async def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance statistics."""
        # This would query actual compliance check results
        return {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }


# Global service instance
compliance_gate_service = ComplianceGateService()
