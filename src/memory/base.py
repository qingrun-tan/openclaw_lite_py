from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.agent.llm_client import Message


class BaseMemory(ABC):
    """
    记忆层抽象基类
    定义会话存储的标准接口
    """

    @abstractmethod
    def get_history(self, session_id: str) -> List[Message]:
        """获取指定会话的历史消息"""
        pass

    @abstractmethod
    def add_message(self, session_id: str, message: Message):
        """向指定会话添加一条消息"""
        pass

    @abstractmethod
    def clear_session(self, session_id: str):
        """清除会话（可选实现）"""
        pass