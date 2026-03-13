# src/memory/redis_memory.py
# 需要先安装: pip install redis
import json
from typing import List
from .base import BaseMemory
from src.agent.llm_client import Message
from ..logger import logger

# import redis # 实际使用时取消注释

class RedisMemory(BaseMemory):
    """
    生产环境推荐：基于Redis的记忆实现
    优势：高性能、支持自动过期、分布式共享
    """

    def __init__(self, host='localhost', port=6379, db=0):
        # self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        logger.info("Redis Memory initialized (Mock mode)")

    def get_session_key(self, session_id: str) -> str:
        return f"openclaw:session:{session_id}"

    def get_history(self, session_id: str) -> List[Message]:
        # data = self.client.get(self.get_session_key(session_id))
        # if not data: return []
        # return [Message(**item) for item in json.loads(data)]
        return []  # Mock

    def add_message(self, session_id: str, message: Message):
        # history = self.get_history(session_id)
        # history.append(message)
        # 序列化并存储，设置过期时间例如24小时
        # self.client.setex(self.get_session_key(session_id), 86400, json.dumps([m.__dict__ for m in history]))
        pass