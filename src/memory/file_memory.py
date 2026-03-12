import json
import os
from typing import List
from .base import BaseMemory
from src.agent.llm_client import Message
from src.logger import logger


class FileMemory(BaseMemory):
    """
    基于本地文件系统的记忆实现
    每个会话对应一个JSON文件
    """

    def __init__(self, storage_dir: str = "./data/memory"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"创建记忆存储目录: {self.storage_dir}")

    def _get_file_path(self, session_id: str) -> str:
        # 安全处理文件名，防止路径穿越攻击
        safe_session_id = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_dir, f"{safe_session_id}.json")

    def get_history(self, session_id: str) -> List[Message]:
        file_path = self._get_file_path(session_id)
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将字典列表转换回Message对象列表
                return [Message(**item) for item in data]
        except Exception as e:
            logger.error(f"读取记忆文件失败 {file_path}: {e}")
            return []

    def add_message(self, session_id: str, message: Message):
        history = self.get_history(session_id)
        history.append(message)

        # 优化：只保留最近的N条消息，防止Token溢出（上下文窗口限制）
        # System Prompt (1条) + 最近20条对话
        MAX_HISTORY = 20
        if len(history) > MAX_HISTORY + 1:
            # 保留第一条（通常是System Prompt）和最近的20条
            history = [history[0]] + history[-MAX_HISTORY:]

        file_path = self._get_file_path(session_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 将Message对象列表转换为字典列表以便序列化
                data = [{"role": m.role, "content": m.content} for m in history]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"写入记忆文件失败 {file_path}: {e}")

    def clear_session(self, session_id: str):
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)