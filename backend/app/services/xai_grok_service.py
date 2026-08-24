import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.config import settings
from app.core.cache import cache
from app.services.oci_responses_service import oci_responses_service

logger = logging.getLogger(__name__)


class XAIGrokService:
    """Compatibility facade that routes Grok inference through OCI."""

    def __init__(self):
        self.model_id = settings.OCI_GROK_MODEL_ID

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Return the legacy chat-completion shape using OCI Responses."""
        cache_key = f"xai_chat:{hash(json.dumps(messages))}:{temperature}:{max_tokens}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        system_prompt = "\n".join(
            message.get("content", "")
            for message in messages
            if message.get("role") == "system"
        )
        prompt = "\n\n".join(
            f"{message.get('role', 'user').title()}: {message.get('content', '')}"
            for message in messages
            if message.get("role") != "system"
        )
        response = await oci_responses_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt or None,
            temperature=temperature,
            max_tokens=max_tokens,
            model_id=self.model_id,
        )
        result = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response.get("inferenceResponse", {}).get("text", ""),
                    }
                }
            ],
            "metadata": response.get("metadata", {}),
        }
        cache.set(cache_key, result, expire=3600)
        return result

    async def analyze_stock(
        self,
        symbol: str,
        stock_data: Dict[str, Any],
        news_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Analyze stock using Grok."""
        # Format stock data
        stock_info = f"""
Stock: {symbol}
Current Price: {stock_data.get('current_price', 'N/A')}
Price Change: {stock_data.get('price_change', 'N/A')} ({stock_data.get('price_change_percent', 'N/A')}%)
Market Cap: {stock_data.get('market_cap', 'N/A')}
P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
Sector: {stock_data.get('sector', 'N/A')}
Industry: {stock_data.get('industry', 'N/A')}
"""

        # Format news data
        news_summary = ""
        if news_data:
            news_summary = "\nRecent News:\n"
            for news in news_data[:5]:
                news_summary += f"- {news.get('title', '')}: {news.get('description', '')[:100]}...\n"

        messages = [
            {
                "role": "system",
                "content": """You are a professional stock analyst. Provide analysis based on the given data.
Include:
1. Technical analysis
2. Fundamental analysis
3. News sentiment
4. Risk assessment
5. Investment recommendation (buy/hold/sell with confidence level)

Important: This is for informational purposes only and not financial advice."""
            },
            {
                "role": "user",
                "content": f"Analyze the following stock:\n{stock_info}{news_summary}"
            }
        ]

        result = await self.chat_completion(messages, temperature=0.5)

        # Extract analysis
        analysis = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        return {
            "symbol": symbol,
            "analysis": analysis,
            "stock_data": stock_data,
            "news_count": len(news_data) if news_data else 0,
            "model_id": self.model_id,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def generate_trading_plan(
        self,
        symbol: str,
        user_profile: Dict[str, Any],
        stock_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate trading plan using Grok."""
        messages = [
            {
                "role": "system",
                "content": """You are a trading plan advisor. Generate a phased trading plan based on:
1. User's investment goals and risk tolerance
2. Stock analysis
3. Market conditions

Provide a structured plan with:
1. Entry points and conditions
2. Position sizing
3. Stop-loss levels
4. Take-profit targets
5. Timeline and milestones
6. Risk management rules

Important: This is for informational purposes only and not financial advice."""
            },
            {
                "role": "user",
                "content": f"""Generate a trading plan for:

Stock: {symbol}
User Profile:
- Target Return: {user_profile.get('target_return', 'N/A')}%
- Investment Horizon: {user_profile.get('investment_horizon', 'N/A')}
- Risk Tolerance: {user_profile.get('risk_tolerance', 'N/A')}
- Available Capital: {user_profile.get('available_capital', 'N/A')}

Stock Analysis:
{stock_analysis.get('analysis', 'N/A')}

Please provide a detailed phased trading plan."""
            }
        ]

        result = await self.chat_completion(messages, temperature=0.5)

        # Extract plan
        plan = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        return {
            "symbol": symbol,
            "user_profile": user_profile,
            "trading_plan": plan,
            "model_id": self.model_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def summarize_news(
        self,
        news_articles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Summarize news articles using Grok."""
        # Format news
        news_text = "\n".join([
            f"- {article.get('title', '')}: {article.get('description', '')}"
            for article in news_articles[:10]
        ])

        messages = [
            {
                "role": "system",
                "content": "You are a financial news summarizer. Provide concise summaries with key takeaways."
            },
            {
                "role": "user",
                "content": f"Summarize the following news articles:\n{news_text}"
            }
        ]

        result = await self.chat_completion(messages, temperature=0.3)

        # Extract summary
        summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        return {
            "news_count": len(news_articles),
            "summary": summary,
            "model_id": self.model_id,
            "summarized_at": datetime.utcnow().isoformat(),
        }


# Global service instance
xai_grok_service = XAIGrokService()
