"""
Webhook 服务
支持接收外部回调和触发交易信号
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import json
import hashlib
import hmac
import logging
import uuid

from app.core.database import SessionLocal
from app.models.platform_operations import (
    WebhookConfigRecord,
    WebhookEventRecord,
    utcnow_naive,
)

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook 事件类型"""
    PRICE_ALERT = "price_alert"
    TRADE_SIGNAL = "trade_signal"
    ORDER_UPDATE = "order_update"
    POSITION_UPDATE = "position_update"
    SYSTEM_EVENT = "system_event"
    CUSTOM = "custom"


class WebhookStatus(str, Enum):
    """Webhook 状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"


class Webhook:
    """Webhook 配置"""

    def __init__(
        self,
        id: str,
        name: str,
        url: str,
        events: List[WebhookEventType],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        status: WebhookStatus = WebhookStatus.ACTIVE,
        created_at: Optional[datetime] = None,
        workspace_id: str = "personal",
    ):
        self.id = id
        self.name = name
        self.url = url
        self.events = events
        self.secret = secret
        self.headers = headers or {}
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.workspace_id = workspace_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "events": [e.value for e in self.events],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "workspace_id": self.workspace_id,
            "storage": "database",
        }


class WebhookEvent:
    """Webhook 事件"""

    def __init__(
        self,
        id: str,
        webhook_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        status: str = "pending",
        response_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.id = id
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.payload = payload
        self.timestamp = timestamp or datetime.utcnow()
        self.status = status
        self.response_code = response_code
        self.response_body = response_body

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "response_code": self.response_code,
        }


class WebhookService:
    """Webhook 服务"""

    def __init__(self):
        self._handlers: Dict[WebhookEventType, List[Callable]] = {}

    @staticmethod
    def _webhook_from_record(record: WebhookConfigRecord) -> Webhook:
        return Webhook(
            id=record.id,
            name=record.name,
            url=record.url,
            events=[WebhookEventType(value) for value in (record.events or [])],
            secret=record.secret,
            headers=record.headers or {},
            status=WebhookStatus(record.status),
            created_at=record.created_at,
            workspace_id=record.workspace_id,
        )

    @staticmethod
    def _event_from_record(record: WebhookEventRecord) -> WebhookEvent:
        return WebhookEvent(
            id=record.id,
            webhook_id=record.webhook_id,
            event_type=WebhookEventType(record.event_type),
            payload=record.payload or {},
            timestamp=record.timestamp,
            status=record.status,
            response_code=record.response_code,
            response_body=record.response_body,
        )

    # ==================== Webhook 管理 ====================

    def create_webhook(
        self,
        name: str,
        url: str,
        events: List[WebhookEventType],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        workspace_id: str = "personal",
    ) -> Webhook:
        """创建 Webhook"""
        record = WebhookConfigRecord(
            name=name,
            url=url,
            events=[event.value for event in events],
            secret=secret,
            headers=headers or {},
            status=WebhookStatus.ACTIVE.value,
            workspace_id=workspace_id,
        )
        with SessionLocal() as db:
            db.add(record)
            db.commit()
            db.refresh(record)
            webhook = self._webhook_from_record(record)
        logger.info(f"Created webhook: {webhook.id} - {name}")
        return webhook

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """获取 Webhook"""
        with SessionLocal() as db:
            record = db.query(WebhookConfigRecord).filter(
                WebhookConfigRecord.id == webhook_id
            ).first()
            return self._webhook_from_record(record) if record else None

    def list_webhooks(self, workspace_id: Optional[str] = None) -> List[Webhook]:
        """列出所有 Webhook"""
        with SessionLocal() as db:
            query = db.query(WebhookConfigRecord)
            if workspace_id:
                query = query.filter(WebhookConfigRecord.workspace_id == workspace_id)
            records = query.order_by(WebhookConfigRecord.created_at.desc()).all()
            return [self._webhook_from_record(record) for record in records]

    def update_webhook(
        self,
        webhook_id: str,
        **kwargs,
    ) -> Optional[Webhook]:
        """更新 Webhook"""
        with SessionLocal() as db:
            record = db.query(WebhookConfigRecord).filter(
                WebhookConfigRecord.id == webhook_id
            ).first()
            if not record:
                return None
            for key, value in kwargs.items():
                if key == "events":
                    record.events = [event.value for event in value]
                elif key == "status":
                    record.status = value.value
                elif hasattr(record, key):
                    setattr(record, key, value)
            record.updated_at = utcnow_naive()
            db.commit()
            db.refresh(record)
            return self._webhook_from_record(record)

    def delete_webhook(self, webhook_id: str) -> bool:
        """删除 Webhook"""
        with SessionLocal() as db:
            record = db.query(WebhookConfigRecord).filter(
                WebhookConfigRecord.id == webhook_id
            ).first()
            if not record:
                return False
            db.query(WebhookEventRecord).filter(
                WebhookEventRecord.webhook_id == webhook_id
            ).delete(synchronize_session=False)
            db.delete(record)
            db.commit()
            return True

    # ==================== 事件处理 ====================

    def register_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable,
    ):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def dispatch_event(
        self,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
    ):
        """分发事件到所有匹配的 Webhook"""
        # 调用注册的处理器
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        # 通知所有订阅此事件的 Webhook
        matched = 0
        for webhook in self.list_webhooks():
            if event_type in webhook.events and webhook.status == WebhookStatus.ACTIVE:
                matched += 1
                record = WebhookEventRecord(
                    webhook_id=webhook.id,
                    event_type=event_type.value,
                    payload=payload,
                    status="pending",
                    timestamp=utcnow_naive(),
                )
                with SessionLocal() as db:
                    db.add(record)
                    db.commit()
                    db.refresh(record)
                    event = self._event_from_record(record)
                await self._send_webhook(webhook, event)

        if matched == 0:
            with SessionLocal() as db:
                db.add(WebhookEventRecord(
                    webhook_id="system",
                    event_type=event_type.value,
                    payload=payload,
                    status="no_subscribers",
                    timestamp=utcnow_naive(),
                    completed_at=utcnow_naive(),
                ))
                db.commit()

    async def _send_webhook(self, webhook: Webhook, event: WebhookEvent):
        """发送 Webhook 请求"""
        import httpx

        payload = {
            "event_id": event.id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "data": event.payload,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Id": webhook.id,
            "X-Event-Type": event.event_type.value,
            **webhook.headers,
        }

        # 签名
        if webhook.secret:
            body = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook.secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )

                event.status = "sent" if response.status_code == 200 else "failed"
                event.response_code = response.status_code
                event.response_body = response.text[:500]

                logger.info(f"Webhook sent to {webhook.url}: {response.status_code}")

        except Exception as e:
            event.status = "error"
            event.response_body = str(e)
            logger.error(f"Webhook error for {webhook.url}: {e}")
        finally:
            with SessionLocal() as db:
                record = db.query(WebhookEventRecord).filter(
                    WebhookEventRecord.id == event.id
                ).first()
                if record:
                    record.status = event.status
                    record.response_code = event.response_code
                    record.response_body = event.response_body
                    record.attempt_count = (record.attempt_count or 0) + 1
                    record.completed_at = utcnow_naive()
                    db.commit()

    # ==================== 接收入口 ====================

    async def handle_incoming_webhook(
        self,
        source: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """处理接收到的 Webhook"""
        logger.info(f"Received webhook from {source}")

        # 根据来源处理
        if source == "longport":
            return await self._handle_longport_webhook(payload, headers)
        elif source == "tradingview":
            return await self._handle_tradingview_webhook(payload, headers)
        elif source == "custom":
            return await self._handle_custom_webhook(payload, headers)
        else:
            return {"status": "error", "message": f"Unknown source: {source}"}

    async def _handle_longport_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """处理长桥证券 Webhook"""
        event_type = payload.get("event_type")

        if event_type == "order_update":
            await self.dispatch_event(
                WebhookEventType.ORDER_UPDATE,
                payload
            )
        elif event_type == "position_update":
            await self.dispatch_event(
                WebhookEventType.POSITION_UPDATE,
                payload
            )

        return {"status": "ok"}

    async def _handle_tradingview_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """处理 TradingView Webhook"""
        # TradingView 格式: {"action": "buy", "symbol": "AAPL", "price": 150.0}
        action = payload.get("action")
        symbol = payload.get("symbol")

        if action and symbol:
            await self.dispatch_event(
                WebhookEventType.TRADE_SIGNAL,
                {
                    "source": "tradingview",
                    "action": action,
                    "symbol": symbol,
                    "price": payload.get("price"),
                    **payload,
                }
            )
            return {"status": "ok", "message": "Signal received"}

        return {"status": "error", "message": "Invalid payload"}

    async def _handle_custom_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """处理自定义 Webhook"""
        await self.dispatch_event(
            WebhookEventType.CUSTOM,
            {"source": "custom", **payload}
        )
        return {"status": "ok"}

    # ==================== 查询 ====================

    def get_events(
        self,
        webhook_id: Optional[str] = None,
        event_type: Optional[WebhookEventType] = None,
        limit: int = 100,
    ) -> List[WebhookEvent]:
        """获取事件历史"""
        with SessionLocal() as db:
            query = db.query(WebhookEventRecord)
            if webhook_id:
                query = query.filter(WebhookEventRecord.webhook_id == webhook_id)
            if event_type:
                query = query.filter(WebhookEventRecord.event_type == event_type.value)
            records = (
                query.order_by(WebhookEventRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._event_from_record(record) for record in records]


# 全局实例
webhook_service = WebhookService()
