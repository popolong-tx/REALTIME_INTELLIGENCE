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
        cache_key = f"xai_chat:zh-cn-v2:{hash(json.dumps(messages))}:{temperature}:{max_tokens}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        system_prompt = "\n".join(
            message.get("content", "")
            for message in messages
            if message.get("role") == "system"
        )
        language_rule = (
            "除 URL、股票代码、模型/工具标识和必要专有名词外，所有面向用户的回复必须使用简体中文。"
        )
        system_prompt = f"{system_prompt}\n\n{language_rule}" if system_prompt else language_rule
        role_labels = {"user": "用户", "assistant": "助手"}
        prompt = "\n\n".join(
            f"{role_labels.get(message.get('role', 'user'), '用户')}：{message.get('content', '')}"
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
股票：{symbol}
当前价格：{stock_data.get('current_price', '暂无')}
价格变化：{stock_data.get('price_change', '暂无')}（{stock_data.get('price_change_percent', '暂无')}%）
市值：{stock_data.get('market_cap', '暂无')}
市盈率：{stock_data.get('pe_ratio', '暂无')}
板块：{stock_data.get('sector', '暂无')}
行业：{stock_data.get('industry', '暂无')}
"""

        # Format news data
        news_summary = ""
        if news_data:
            news_summary = "\n近期新闻：\n"
            for news in news_data[:5]:
                news_summary += f"- {news.get('title', '')}: {news.get('description', '')[:100]}...\n"

        messages = [
            {
                "role": "system",
                "content": """你是一名专业股票分析师，必须使用简体中文，并且只能依据给定数据分析。
内容包括：
1. 技术分析
2. 基本面分析
3. 新闻情绪
4. 风险评估
5. 投资建议（买入/持有/卖出及置信度）

重要提示：内容仅供信息参考，不构成财务或投资建议。"""
            },
            {
                "role": "user",
                "content": f"请分析下列股票，并使用简体中文回答：\n{stock_info}{news_summary}"
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
                "content": """你是一名交易计划顾问，必须使用简体中文，并依据以下信息生成分阶段交易计划：
1. 用户投资目标与风险承受能力
2. 股票分析
3. 市场状况

计划必须结构化呈现：
1. 入场点与条件
2. 仓位规模
3. 止损位
4. 止盈目标
5. 时间线与里程碑
6. 风险管理规则

重要提示：内容仅供信息参考，不构成财务或投资建议。"""
            },
            {
                "role": "user",
                "content": f"""请为以下信息生成详细的分阶段交易计划，并使用简体中文回答：

股票：{symbol}
用户画像：
- 目标收益：{user_profile.get('target_return', '暂无')}%
- 投资周期：{user_profile.get('investment_horizon', '暂无')}
- 风险承受能力：{user_profile.get('risk_tolerance', '暂无')}
- 可用资金：{user_profile.get('available_capital', '暂无')}

股票分析：
{stock_analysis.get('analysis', '暂无')}"""
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
                "content": "你是一名金融新闻摘要员。使用简体中文提供简洁摘要和关键结论，不增加原文没有的事实。"
            },
            {
                "role": "user",
                "content": f"请用简体中文总结下列新闻：\n{news_text}"
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
