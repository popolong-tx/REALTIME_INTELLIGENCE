"""
长桥证券 (LongPort) API 集成
文档: https://open.longportapp.com/docs
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import httpx
import hashlib
import hmac
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OrderSide(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(str, Enum):
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"
    STOP_LIMIT = "StopLimit"


class OrderStatus(str, Enum):
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    PARTIALLY_FILLED = "PartiallyFilled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"


class LongPortService:
    """长桥证券 API 服务"""

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://openapi.longportapp.com",
    ):
        self.app_key = app_key or getattr(settings, 'LONGPORT_APP_KEY', None)
        self.app_secret = app_secret or getattr(settings, 'LONGPORT_APP_SECRET', None)
        self.access_token = access_token or getattr(settings, 'LONGPORT_ACCESS_TOKEN', None)
        self.base_url = base_url
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=30.0,
            )
        return self._client

    def _get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        headers = {
            "Content-Type": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _sign_request(self, timestamp: str, body: str) -> str:
        """签名请求"""
        if not self.app_secret:
            return ""
        message = f"{timestamp}{body}"
        signature = hmac.new(
            self.app_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    # ==================== 行情接口 ====================

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取股票报价"""
        try:
            response = await self.client.get(f"/v1/quote?symbol={symbol}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取报价失败 {symbol}: {e}")
            return {"error": str(e)}

    async def get_realtime_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """获取实时报价"""
        try:
            response = await self.client.post(
                "/v1/quote/realtime",
                json={"symbols": symbols}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取实时报价失败: {e}")
            return {"error": str(e)}

    async def get_kline(
        self,
        symbol: str,
        period: str = "Day",
        count: int = 100,
    ) -> Dict[str, Any]:
        """获取K线数据"""
        try:
            response = await self.client.get(
                f"/v1/quote/kline",
                params={"symbol": symbol, "period": period, "count": count}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取K线失败 {symbol}: {e}")
            return {"error": str(e)}

    # ==================== 交易接口 ====================

    async def get_account_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        try:
            response = await self.client.get("/v1/account/balance")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            return {"error": str(e)}

    async def get_positions(self) -> Dict[str, Any]:
        """获取持仓"""
        try:
            response = await self.client.get("/v1/account/positions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return {"error": str(e)}

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """下单"""
        order_data = {
            "symbol": symbol,
            "side": side.value,
            "order_type": order_type.value,
            "quantity": quantity,
        }

        if price is not None:
            order_data["price"] = str(price)
        if stop_price is not None:
            order_data["stop_price"] = str(stop_price)
        if client_order_id:
            order_data["client_order_id"] = client_order_id

        try:
            response = await self.client.post(
                "/v1/order/submit",
                json=order_data
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"下单成功: {symbol} {side.value} {quantity} @ {price}")
            return result
        except Exception as e:
            logger.error(f"下单失败 {symbol}: {e}")
            return {"error": str(e)}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """撤单"""
        try:
            response = await self.client.post(
                "/v1/order/cancel",
                json={"order_id": order_id}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"撤单失败 {order_id}: {e}")
            return {"error": str(e)}

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            response = await self.client.get(f"/v1/order/{order_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"查询订单失败 {order_id}: {e}")
            return {"error": str(e)}

    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取订单历史"""
        params = {}
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status.value
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            response = await self.client.get("/v1/order/history", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取订单历史失败: {e}")
            return {"error": str(e)}

    # ==================== 工具方法 ====================

    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局实例
longport_service = LongPortService()
