"""
券商接口 API
支持长桥证券等券商接入
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel

from app.services.broker.longport_service import (
    longport_service,
    OrderSide,
    OrderType,
)
from app.services.broker.base_broker import BrokerFactory
from app.core.config import settings
from app.services.audit_trail_service import audit_trail_service, AuditEventType
from app.services.emergency_shutdown_service import emergency_shutdown_service

router = APIRouter(prefix="/api/v1/broker", tags=["broker"])


async def enforce_live_order_policy(action: str, details: Optional[dict] = None) -> None:
    """Reject broker mutations unless both explicit server controls allow them."""
    if not await emergency_shutdown_service.is_operation_allowed("broker"):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "emergency_shutdown",
                "message": "Broker mutations are blocked by the emergency shutdown gate.",
            },
        )
    live_enabled = (
        settings.EXECUTION_MODE == "live"
        and settings.BROKER_LIVE_TRADING_ENABLED
    )
    if live_enabled:
        return
    await audit_trail_service.log_event(
        event_type=AuditEventType.SYSTEM_EVENT,
        user_id="api_user",
        resource_type="broker_order",
        action=f"blocked_{action}",
        details={
            "execution_mode": settings.EXECUTION_MODE,
            "live_trading_enabled": settings.BROKER_LIVE_TRADING_ENABLED,
            **(details or {}),
        },
    )
    raise HTTPException(
        status_code=403,
        detail={
            "code": "simulation_only",
            "message": "Live broker order mutations are disabled by server policy.",
            "execution_mode": settings.EXECUTION_MODE,
        },
    )


# ==================== 请求模型 ====================

class PlaceOrderRequest(BaseModel):
    symbol: str
    side: str  # Buy, Sell
    order_type: str  # Market, Limit, Stop, StopLimit
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None


class CancelOrderRequest(BaseModel):
    order_id: str


# ==================== 行情接口 ====================

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """获取股票报价"""
    result = await longport_service.get_quote(symbol)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/quotes")
async def get_realtime_quotes(symbols: List[str]):
    """获取实时报价"""
    result = await longport_service.get_realtime_quotes(symbols)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/kline/{symbol}")
async def get_kline(
    symbol: str,
    period: str = "Day",
    count: int = 100,
):
    """获取K线数据"""
    result = await longport_service.get_kline(symbol, period, count)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==================== 交易接口 ====================

@router.get("/account/balance")
async def get_account_balance():
    """获取账户余额"""
    result = await longport_service.get_account_balance()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/account/positions")
async def get_positions():
    """获取持仓"""
    result = await longport_service.get_positions()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/order")
async def place_order(request: PlaceOrderRequest):
    """下单"""
    await enforce_live_order_policy(
        "place_order",
        {"symbol": request.symbol, "side": request.side, "quantity": request.quantity},
    )
    try:
        side = OrderSide(request.side)
        order_type = OrderType(request.order_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid order parameters: {e}")

    result = await longport_service.place_order(
        symbol=request.symbol,
        side=side,
        order_type=order_type,
        quantity=request.quantity,
        price=request.price,
        stop_price=request.stop_price,
        client_order_id=request.client_order_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/order/cancel")
async def cancel_order(request: CancelOrderRequest):
    """撤单"""
    await enforce_live_order_policy("cancel_order", {"order_id": request.order_id})
    result = await longport_service.cancel_order(request.order_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/order/{order_id}")
async def get_order_status(order_id: str):
    """查询订单状态"""
    result = await longport_service.get_order_status(order_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/orders")
async def get_order_history(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取订单历史"""
    result = await longport_service.get_order_history(
        symbol=symbol,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==================== 券商管理 ====================

@router.get("/brokers")
async def list_brokers():
    """列出所有支持的券商"""
    return {
        "execution_mode": settings.EXECUTION_MODE,
        "order_mutations_enabled": (
            settings.EXECUTION_MODE == "live"
            and settings.BROKER_LIVE_TRADING_ENABLED
        ),
        "brokers": [
            {
                "id": "longport",
                "name": "长桥证券",
                "status": "active" if longport_service.access_token else "not_configured",
            }
        ]
    }
