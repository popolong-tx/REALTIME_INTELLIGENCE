from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.services.data_sources.data_aggregator import data_aggregator, DataSource
from app.core.cache import cache

logger = logging.getLogger(__name__)


class FinancialDataService:
    """Service for querying financial data."""

    async def get_financial_statements(
        self,
        symbol: str,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get financial statements (income, balance sheet, cash flow)."""
        cache_key = cache.get_stock_cache_key(symbol, "financial_statements")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await data_aggregator.get_financials(symbol, preferred_source)

            # Add computed metrics
            result["computed_metrics"] = self._compute_financial_metrics(result)

            # Cache for 24 hours
            cache.set(cache_key, result, expire=86400)

            return result

        except Exception as e:
            logger.error(f"Error getting financial statements for {symbol}: {e}")
            raise

    async def get_key_metrics(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Get key financial metrics."""
        # v2 normalizes all percentage ratios to decimals before they reach the UI.
        cache_key = cache.get_stock_cache_key(symbol, "key_metrics_v2")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get stock info for current price and basic metrics
            stock_info = await data_aggregator.get_stock_info(symbol)

            # Get financial statements
            financials = await self.get_financial_statements(symbol)

            dividend_yield = stock_info.get("dividend_yield")
            # Yahoo Finance currently returns dividendYield in percentage points
            # (for example 0.35 means 0.35%), while Alpha Vantage returns a
            # decimal ratio. Normalize both sources to a decimal ratio.
            if (
                dividend_yield is not None
                and stock_info.get("data_source") == DataSource.YAHOO_FINANCE.value
            ):
                dividend_yield = dividend_yield / 100

            metrics = {
                "symbol": symbol,
                "valuation_metrics": {
                    "pe_ratio": stock_info.get("pe_ratio"),
                    "pb_ratio": stock_info.get("price_to_book"),
                    "ps_ratio": stock_info.get("price_to_sales"),
                    "ev_to_ebitda": stock_info.get("ev_to_ebitda"),
                    "dividend_yield": dividend_yield,
                },
                "profitability_metrics": {
                    "gross_margin": stock_info.get("gross_margin"),
                    "operating_margin": stock_info.get("operating_margin"),
                    "net_margin": stock_info.get("profit_margin"),
                    "roe": stock_info.get("return_on_equity"),
                    "roa": stock_info.get("return_on_assets"),
                },
                "growth_metrics": {
                    "revenue_growth": stock_info.get("revenue_growth"),
                    "earnings_growth": stock_info.get("earnings_growth"),
                    "quarterly_revenue_growth": stock_info.get("quarterly_revenue_growth"),
                    "quarterly_earnings_growth": stock_info.get("quarterly_earnings_growth"),
                },
                "liquidity_metrics": {
                    "current_ratio": None,  # Would need balance sheet data
                    "quick_ratio": None,
                    "debt_to_equity": None,
                },
                "computed_from": financials.get("data_source"),
                "metric_units": {"ratios": "decimal"},
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, metrics, expire=3600)

            return metrics

        except Exception as e:
            logger.error(f"Error getting key metrics for {symbol}: {e}")
            raise

    async def get_financial_ratios(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Get financial ratios."""
        cache_key = cache.get_stock_cache_key(symbol, "financial_ratios")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            financials = await self.get_financial_statements(symbol)

            # Extract latest financial data
            income = financials.get("income_statement", [])
            balance = financials.get("balance_sheet", [])
            cashflow = financials.get("cash_flow", [])

            ratios = {
                "symbol": symbol,
                "profitability_ratios": self._calculate_profitability_ratios(income, balance),
                "liquidity_ratios": self._calculate_liquidity_ratios(balance),
                "efficiency_ratios": self._calculate_efficiency_ratios(income, balance),
                "leverage_ratios": self._calculate_leverage_ratios(balance),
                "valuation_ratios": self._calculate_valuation_ratios(income, balance),
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 24 hours
            cache.set(cache_key, ratios, expire=86400)

            return ratios

        except Exception as e:
            logger.error(f"Error getting financial ratios for {symbol}: {e}")
            raise

    def _compute_financial_metrics(
        self,
        financials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute additional financial metrics."""
        income = financials.get("income_statement", [])
        balance = financials.get("balance_sheet", [])

        if not income or not balance:
            return {}

        latest_income = income[0] if income else {}
        latest_balance = balance[0] if balance else {}

        return {
            "total_revenue": latest_income.get("Total Revenue"),
            "net_income": latest_income.get("Net Income"),
            "total_assets": latest_balance.get("Total Assets"),
            "total_liabilities": latest_balance.get("Total Liabilities Net Minority Interest"),
            "total_equity": latest_balance.get("Stockholders Equity"),
            "cash_and_equivalents": latest_balance.get("Cash And Cash Equivalents"),
        }

    def _calculate_profitability_ratios(
        self,
        income: List[Dict],
        balance: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate profitability ratios."""
        if not income:
            return {}

        latest = income[0]
        revenue = latest.get("Total Revenue", 0)
        gross_profit = latest.get("Gross Profit", 0)
        operating_income = latest.get("Operating Income", 0)
        net_income = latest.get("Net Income", 0)

        return {
            "gross_margin": (gross_profit / revenue * 100) if revenue else None,
            "operating_margin": (operating_income / revenue * 100) if revenue else None,
            "net_margin": (net_income / revenue * 100) if revenue else None,
        }

    def _calculate_liquidity_ratios(
        self,
        balance: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate liquidity ratios."""
        if not balance:
            return {}

        latest = balance[0]
        current_assets = latest.get("Current Assets", 0)
        current_liabilities = latest.get("Current Liabilities", 0)
        inventory = latest.get("Inventory", 0)
        cash = latest.get("Cash And Cash Equivalents", 0)

        current_ratio = current_assets / current_liabilities if current_liabilities else None
        quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities else None
        cash_ratio = cash / current_liabilities if current_liabilities else None

        return {
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "cash_ratio": cash_ratio,
        }

    def _calculate_efficiency_ratios(
        self,
        income: List[Dict],
        balance: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate efficiency ratios."""
        if not income or not balance:
            return {}

        latest_income = income[0]
        latest_balance = balance[0]

        revenue = latest_income.get("Total Revenue", 0)
        total_assets = latest_balance.get("Total Assets", 0)
        inventory = latest_balance.get("Inventory", 0)
        receivables = latest_balance.get("Accounts Receivable", 0)

        asset_turnover = revenue / total_assets if total_assets else None
        inventory_turnover = latest_income.get("Cost Of Revenue", 0) / inventory if inventory else None
        receivable_turnover = revenue / receivables if receivables else None

        return {
            "asset_turnover": asset_turnover,
            "inventory_turnover": inventory_turnover,
            "receivable_turnover": receivable_turnover,
        }

    def _calculate_leverage_ratios(
        self,
        balance: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate leverage ratios."""
        if not balance:
            return {}

        latest = balance[0]
        total_debt = latest.get("Total Debt", 0)
        total_equity = latest_balance.get("Stockholders Equity", 0)
        total_assets = latest.get("Total Assets", 0)

        debt_to_equity = total_debt / total_equity if total_equity else None
        debt_to_assets = total_debt / total_assets if total_assets else None
        equity_multiplier = total_assets / total_equity if total_equity else None

        return {
            "debt_to_equity": debt_to_equity,
            "debt_to_assets": debt_to_assets,
            "equity_multiplier": equity_multiplier,
        }

    def _calculate_valuation_ratios(
        self,
        income: List[Dict],
        balance: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate valuation ratios."""
        # These would typically need market data
        return {
            "note": "Valuation ratios require market data and are computed in key_metrics",
        }


# Global service instance
financial_data_service = FinancialDataService()
