from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseGateway(ABC):
    """
    Gateway层抽象基类
    定义所有平台适配器必须实现的接口
    """

    @abstractmethod
    def receive(self) -> Dict[str, Any]:
        """
        接收用户消息
        返回格式: {"user_id": "xxx, "content": "用户输入", "session_id": "xxx"}
        """
        pass

    @abstractmethod
    def send(self, message: str, user_id: str):
        """
        发送回复给用户
        """
        pass

    def health_check(self) -> bool:
        """通用健康检查"""
        return True