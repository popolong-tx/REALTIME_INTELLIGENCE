"""
券商接口抽象基类
所有券商实现都需要继承此类
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


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


class BrokerInterface(ABC):
    """券商接口抽象基类"""

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取股票报价"""
        pass

    @abstractmethod
    async def get_realtime_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """获取实时报价"""
        pass

    @abstractmethod
    async def get_kline(
        self,
        symbol: str,
        period: str = "Day",
        count: int = 100,
    ) -> Dict[str, Any]:
        """获取K线数据"""
        pass

    @abstractmethod
    async def get_account_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        pass

    @abstractmethod
    async def get_positions(self) -> Dict[str, Any]:
        """获取持仓"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """撤单"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        pass

    @abstractmethod
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取订单历史"""
        pass


class BrokerFactory:
    """券商工厂类"""

    _brokers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, broker_class: type):
        """注册券商实现"""
        cls._brokers[name] = broker_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BrokerInterface:
        """创建券商实例"""
        if name not in cls._brokers:
            raise ValueError(f"Unknown broker: {name}")
        return cls._brokers[name](**kwargs)

    @classmethod
    def list_brokers(cls) -> List[str]:
        """列出所有已注册的券商"""
        return list(cls._brokers.keys())
