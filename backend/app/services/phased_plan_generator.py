from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.recommendation_engine import recommendation_engine, RecommendationType
from app.services.xai_grok_service import xai_grok_service

logger = logging.getLogger(__name__)


class PlanPhase(str, Enum):
    OBSERVATION = "observation"
    INITIAL_ENTRY = "initial_entry"
    ACCUMULATION = "accumulation"
    ADJUSTMENT = "adjustment"
    EXIT = "exit"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TradingPlanPhase:
    """A phase in a trading plan."""

    def __init__(
        self,
        phase: PlanPhase,
        name: str,
        description: str,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        duration_days: Optional[int] = None,
        target_allocation: Optional[float] = None,
    ):
        self.phase = phase
        self.name = name
        self.description = description
        self.conditions = conditions
        self.actions = actions
        self.duration_days = duration_days
        self.target_allocation = target_allocation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "duration_days": self.duration_days,
            "target_allocation": self.target_allocation,
        }


class PhasedTradingPlan:
    """A phased trading plan with conditions."""

    def __init__(
        self,
        symbol: str,
        phases: List[TradingPlanPhase],
        user_profile: Dict[str, Any],
        risk_management: Dict[str, Any],
        validity_days: int = 30,
    ):
        self.symbol = symbol
        self.phases = phases
        self.user_profile = user_profile
        self.risk_management = risk_management
        self.validity_days = validity_days
        self.created_at = datetime.utcnow()
        self.valid_until = self.created_at + timedelta(days=validity_days)
        self.status = PlanStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "phases": [p.to_dict() for p in self.phases],
            "user_profile": self.user_profile,
            "risk_management": self.risk_management,
            "validity_days": self.validity_days,
            "created_at": self.created_at.isoformat(),
            "valid_until": self.valid_until.isoformat(),
            "status": self.status.value,
        }


class PhasedPlanGenerator:
    """Generator for phased trading plans."""

    async def generate_plan(
        self,
        symbol: str,
        user_profile: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a phased trading plan."""
        try:
            # Get recommendation if not provided
            if not recommendation:
                recommendation = await recommendation_engine.generate_recommendation(
                    symbol, user_profile
                )
                recommendation = recommendation.to_dict()

            # Extract user constraints
            target_return = user_profile.get("target_return", 0.1)
            investment_horizon = user_profile.get("investment_horizon", "medium")
            risk_tolerance = user_profile.get("risk_tolerance", "medium")
            available_capital = user_profile.get("available_capital", 100000)

            # Generate phases based on recommendation
            phases = self._generate_phases(
                recommendation, user_profile
            )

            # Generate risk management rules
            risk_management = self._generate_risk_management(
                recommendation, user_profile
            )

            # Create plan
            plan = PhasedTradingPlan(
                symbol=symbol,
                phases=phases,
                user_profile=user_profile,
                risk_management=risk_management,
                validity_days=self._calculate_validity_days(investment_horizon),
            )

            return plan.to_dict()

        except Exception as e:
            logger.error(f"Error generating phased plan for {symbol}: {e}")
            raise

    def _generate_phases(
        self,
        recommendation: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> List[TradingPlanPhase]:
        """Generate trading phases."""
        phases = []

        rec_type = recommendation.get("recommendation", "hold")
        risk_level = recommendation.get("risk_level", "medium")
        target_price = recommendation.get("target_price")
        stop_loss = recommendation.get("stop_loss")

        # Phase 1: Observation
        phases.append(TradingPlanPhase(
            phase=PlanPhase.OBSERVATION,
            name="观察期",
            description="观察市场走势，等待入场时机",
            conditions=[
                {
                    "type": "price",
                    "condition": "price stabilizes",
                    "description": "价格企稳，波动率降低",
                },
                {
                    "type": "volume",
                    "condition": "volume increases",
                    "description": "成交量放大，显示市场关注度",
                },
            ],
            actions=[
                {
                    "type": "monitor",
                    "action": "设置价格提醒",
                    "parameters": {
                        "upper": target_price,
                        "lower": stop_loss,
                    },
                },
            ],
            duration_days=3,
            target_allocation=0,
        ))

        # Phase 2: Initial Entry
        if rec_type in ["buy", "hold"]:
            entry_allocation = self._calculate_entry_allocation(risk_level, user_profile)
            phases.append(TradingPlanPhase(
                phase=PlanPhase.INITIAL_ENTRY,
                name="初始建仓",
                description="建立初始仓位",
                conditions=[
                    {
                        "type": "price",
                        "condition": "price at entry level",
                        "description": f"价格接近入场价 {recommendation.get('entry_price')}",
                    },
                    {
                        "type": "technical",
                        "condition": "bullish signal",
                        "description": "技术指标显示买入信号",
                    },
                ],
                actions=[
                    {
                        "type": "buy",
                        "action": "买入",
                        "parameters": {
                            "allocation": entry_allocation,
                            "order_type": "limit",
                            "price": recommendation.get("entry_price"),
                        },
                    },
                ],
                duration_days=7,
                target_allocation=entry_allocation,
            ))

            # Phase 3: Accumulation
            phases.append(TradingPlanPhase(
                phase=PlanPhase.ACCUMULATION,
                name="加仓期",
                description="根据走势逐步加仓",
                conditions=[
                    {
                        "type": "price",
                        "condition": "price above entry",
                        "description": "价格高于入场价",
                    },
                    {
                        "type": "performance",
                        "condition": "positive momentum",
                        "description": "显示正向动量",
                    },
                ],
                actions=[
                    {
                        "type": "buy",
                        "action": "分批加仓",
                        "parameters": {
                            "allocation": 0.1,
                            "order_type": "limit",
                        },
                    },
                ],
                duration_days=14,
                target_allocation=0.3,
            ))

        # Phase 4: Adjustment
        phases.append(TradingPlanPhase(
            phase=PlanPhase.ADJUSTMENT,
            name="调整期",
            description="根据市场变化调整仓位",
            conditions=[
                {
                    "type": "price",
                    "condition": "price near target",
                    "description": "价格接近目标价",
                },
                {
                    "type": "risk",
                    "condition": "risk level changes",
                    "description": "风险水平变化",
                },
            ],
            actions=[
                {
                    "type": "adjust",
                    "action": "调整止损",
                    "parameters": {
                        "new_stop_loss": "trailing",
                    },
                },
            ],
            duration_days=7,
        ))

        # Phase 5: Exit
        phases.append(TradingPlanPhase(
            phase=PlanPhase.EXIT,
            name="退出期",
            description="根据条件退出仓位",
            conditions=[
                {
                    "type": "price",
                    "condition": "price at target",
                    "description": f"价格达到目标价 {target_price}",
                },
                {
                    "type": "stop_loss",
                    "condition": "stop loss triggered",
                    "description": f"触发止损价 {stop_loss}",
                },
                {
                    "type": "time",
                    "condition": "plan expires",
                    "description": "计划到期",
                },
            ],
            actions=[
                {
                    "type": "sell",
                    "action": "卖出",
                    "parameters": {
                        "order_type": "market",
                        "quantity": "all",
                    },
                },
            ],
            duration_days=3,
        ))

        return phases

    def _generate_risk_management(
        self,
        recommendation: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate risk management rules."""
        risk_tolerance = user_profile.get("risk_tolerance", "medium")
        available_capital = user_profile.get("available_capital", 100000)

        # Position sizing based on risk tolerance
        if risk_tolerance == "conservative":
            max_position_pct = 0.1
            max_loss_pct = 0.02
        elif risk_tolerance == "aggressive":
            max_position_pct = 0.3
            max_loss_pct = 0.05
        else:
            max_position_pct = 0.2
            max_loss_pct = 0.03

        return {
            "stop_loss": recommendation.get("stop_loss"),
            "take_profit": recommendation.get("target_price"),
            "max_position_size": available_capital * max_position_pct,
            "max_loss_per_trade": available_capital * max_loss_pct,
            "trailing_stop": risk_tolerance != "conservative",
            "position_sizing": {
                "method": "fixed_percentage",
                "percentage": max_position_pct,
            },
            "risk_reward_ratio": 2.0,
        }

    def _calculate_entry_allocation(
        self,
        risk_level: str,
        user_profile: Dict[str, Any],
    ) -> float:
        """Calculate initial entry allocation."""
        risk_tolerance = user_profile.get("risk_tolerance", "medium")

        if risk_level in ["high", "very_high"]:
            if risk_tolerance == "conservative":
                return 0.05
            elif risk_tolerance == "aggressive":
                return 0.15
            else:
                return 0.10
        else:
            if risk_tolerance == "conservative":
                return 0.10
            elif risk_tolerance == "aggressive":
                return 0.25
            else:
                return 0.15

    def _calculate_validity_days(self, investment_horizon: str) -> int:
        """Calculate plan validity days."""
        if investment_horizon == "short":
            return 14
        elif investment_horizon == "long":
            return 90
        else:
            return 30


# Global generator instance
phased_plan_generator = PhasedPlanGenerator()
