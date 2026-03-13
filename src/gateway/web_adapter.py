"""
Web Gateway - FastAPI 平台适配器

支持通过 HTTP/WebSocket 与智能体交互
"""
import uuid
from typing import Dict, Any, Optional
from .base import BaseGateway
from src.logger import logger


class WebGateway(BaseGateway):
    """
    Web 平台适配器

    用于 FastAPI 场景，将 HTTP 请求转换为内部格式
    """

    def __init__(self, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        初始化 Web 适配器

        Args:
            user_id: 用户 ID（可选，默认生成）
            session_id: 会话 ID（可选，默认生成）
        """
        self.user_id = user_id or f"web_user_{uuid.uuid4().hex[:8]}"
        self.session_id = session_id or str(uuid.uuid4())
        self._pending_request = None

    def receive(self) -> Dict[str, Any]:
        """
        接收用户消息

        在 Web 适配器中，这个方法通常不直接使用，
        而是通过 API 接口接收请求后直接调用 process()。

        Returns:
            消息字典
        """
        if self._pending_request:
            request = self._pending_request
            self._pending_request = None
            return request

        return {
            "action": "idle",
            "user_id": self.user_id,
            "content": "",
            "session_id": self.session_id
        }

    def send(self, message: str, user_id: str):
        """
        发送回复给用户

        在 Web 适配器中，响应由 API 直接返回，
        此方法主要用于日志记录或 WebSocket 推送。

        Args:
            message: 回复内容
            user_id: 用户 ID
        """
        logger.info(f"Web Gateway 发送消息给 {user_id}: {message[:50]}...")

    def set_request(self, content: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        设置待处理的请求（供 API 调用）

        Args:
            content: 用户输入
            session_id: 会话 ID（可选）
            user_id: 用户 ID（可选）

        Returns:
            请求字典
        """
        if session_id:
            self.session_id = session_id
        if user_id:
            self.user_id = user_id

        self._pending_request = {
            "user_id": self.user_id,
            "content": content,
            "session_id": self.session_id
        }

        return self._pending_request

    def health_check(self) -> bool:
        """健康检查"""
        return True


# 预留 WebSocket 适配器
class WebSocketGateway(BaseGateway):
    """
    WebSocket 平台适配器（预留）

    支持实时双向通信，适合流式输出场景
    """

    def __init__(self, websocket, user_id: Optional[str] = None):
        """
        初始化 WebSocket 适配器

        Args:
            websocket: WebSocket 连接对象
            user_id: 用户 ID
        """
        self.websocket = websocket
        self.user_id = user_id or f"ws_user_{uuid.uuid4().hex[:8]}"
        self.session_id = str(uuid.uuid4())

    async def receive(self) -> Dict[str, Any]:
        """接收 WebSocket 消息"""
        try:
            data = await self.websocket.receive_json()
            return {
                "user_id": self.user_id,
                "content": data.get("message", ""),
                "session_id": data.get("session_id", self.session_id)
            }
        except Exception as e:
            logger.error(f"WebSocket 接收消息失败: {e}")
            return {"action": "error"}

    async def send(self, message: str, user_id: str):
        """通过 WebSocket 发送消息"""
        try:
            await self.websocket.send_json({
                "type": "message",
                "content": message,
                "user_id": user_id
            })
        except Exception as e:
            logger.error(f"WebSocket 发送消息失败: {e}")

    def health_check(self) -> bool:
        """健康检查"""
        return self.websocket is not None
