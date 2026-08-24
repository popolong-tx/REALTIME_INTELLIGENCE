"""
Webhook API
支持接收和管理 Webhook
"""

from fastapi import APIRouter, HTTPException, Request, Header
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.services.webhook_service import (
    webhook_service,
    WebhookEventType,
    WebhookStatus,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# ==================== 请求模型 ====================

class CreateWebhookRequest(BaseModel):
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    workspace_id: str = "personal"


class UpdateWebhookRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    status: Optional[str] = None


# ==================== Webhook 管理 ====================

@router.post("/")
async def create_webhook(request: CreateWebhookRequest):
    """创建 Webhook"""
    try:
        events = [WebhookEventType(e) for e in request.events]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")

    webhook = webhook_service.create_webhook(
        name=request.name,
        url=request.url,
        events=events,
        secret=request.secret,
        headers=request.headers,
        workspace_id=request.workspace_id,
    )

    return webhook.to_dict()


@router.get("/")
async def list_webhooks(workspace_id: Optional[str] = None):
    """列出所有 Webhook"""
    webhooks = webhook_service.list_webhooks(workspace_id=workspace_id)
    return {"webhooks": [w.to_dict() for w in webhooks], "storage": "database"}


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: str):
    """获取 Webhook 详情"""
    webhook = webhook_service.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook.to_dict()


@router.put("/{webhook_id}")
async def update_webhook(webhook_id: str, request: UpdateWebhookRequest):
    """更新 Webhook"""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.url is not None:
        updates["url"] = request.url
    if request.events is not None:
        try:
            updates["events"] = [WebhookEventType(e) for e in request.events]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    if request.secret is not None:
        updates["secret"] = request.secret
    if request.status is not None:
        try:
            updates["status"] = WebhookStatus(request.status)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid status: {e}")

    webhook = webhook_service.update_webhook(webhook_id, **updates)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook.to_dict()


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """删除 Webhook"""
    if not webhook_service.delete_webhook(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "deleted"}


# ==================== 事件查询 ====================

@router.get("/{webhook_id}/events")
async def get_webhook_events(
    webhook_id: str,
    limit: int = 100,
):
    """获取 Webhook 事件历史"""
    events = webhook_service.get_events(webhook_id=webhook_id, limit=limit)
    return {"events": [e.to_dict() for e in events]}


# ==================== 接收端点 ====================

@router.post("/receive/longport")
async def receive_longport_webhook(request: Request):
    """接收长桥证券 Webhook"""
    payload = await request.json()
    headers = dict(request.headers)

    result = await webhook_service.handle_incoming_webhook(
        source="longport",
        payload=payload,
        headers=headers,
    )

    return result


@router.post("/receive/tradingview")
async def receive_tradingview_webhook(request: Request):
    """接收 TradingView Webhook"""
    payload = await request.json()
    headers = dict(request.headers)

    result = await webhook_service.handle_incoming_webhook(
        source="tradingview",
        payload=payload,
        headers=headers,
    )

    return result


@router.post("/receive/custom/{source}")
async def receive_custom_webhook(source: str, request: Request):
    """接收自定义 Webhook"""
    payload = await request.json()
    headers = dict(request.headers)

    result = await webhook_service.handle_incoming_webhook(
        source=source,
        payload=payload,
        headers=headers,
    )

    return result


# ==================== 事件类型 ====================

@router.get("/events/types")
async def list_event_types():
    """列出所有支持的事件类型"""
    return {
        "event_types": [
            {"value": e.value, "name": e.name}
            for e in WebhookEventType
        ]
    }
