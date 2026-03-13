"""
记忆系统单元测试

测试文件记忆存储功能
"""
import pytest
import sys
import os
import json
import tempfile
import shutil

# 添加 src 到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory import FileMemory
from src.agent.llm_client import Message


class TestFileMemory:
    """文件记忆存储测试"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = FileMemory(storage_dir=self.temp_dir)

    def teardown_method(self):
        """每个测试后清理临时目录"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_and_get_message(self):
        """测试添加和获取消息"""
        session_id = "test_session"

        # 添加消息
        msg1 = Message(role="user", content="Hello")
        msg2 = Message(role="assistant", content="Hi there!")

        self.memory.add_message(session_id, msg1)
        self.memory.add_message(session_id, msg2)

        # 获取消息
        history = self.memory.get_history(session_id)

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
        assert history[1].content == "Hi there!"

    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        history = self.memory.get_history("nonexistent_session")
        assert history == []

    def test_clear_session(self):
        """测试清除会话"""
        session_id = "test_sessionToClear"

        # 添加消息
        self.memory.add_message(session_id, Message(role="user", content="Test"))
        assert len(self.memory.get_history(session_id)) > 0

        # 清除会话
        self.memory.clear_session(session_id)
        assert self.memory.get_history(session_id) == []

    def test_file_persistence(self):
        """测试文件持久化"""
        session_id = "persistent_session"

        # 添加消息
        self.memory.add_message(session_id, Message(role="user", content="Persist this"))
        self.memory.add_message(session_id, Message(role="assistant", content="OK"))

        # 创建新的记忆实例，模拟重启
        new_memory = FileMemory(storage_dir=self.temp_dir)
        history = new_memory.get_history(session_id)

        assert len(history) == 2
        assert history[0].content == "Persist this"
        assert history[1].content == "OK"

    def test_history_limit(self):
        """测试历史消息数量限制"""
        session_id = "long_session"

        # 添加超过限制的消息
        for i in range(30):
            self.memory.add_message(
                session_id,
                Message(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")
            )

        history = self.memory.get_history(session_id)

        # 应该只保留最近的 21 条（1 条 system + 20 条消息）
        # 注意：第一个消息是空的（没有 system prompt）
        assert len(history) <= 21

    def test_special_characters_in_session_id(self):
        """测试会话 ID 中的特殊字符"""
        session_id = "test/session\\with|special:chars"

        self.memory.add_message(session_id, Message(role="user", content="Test"))
        history = self.memory.get_history(session_id)

        assert len(history) == 1
        assert history[0].content == "Test"

    def test_multiple_sessions(self):
        """测试多个会话隔离"""
        session1 = "session_1"
        session2 = "session_2"

        # 为不同会话添加消息
        self.memory.add_message(session1, Message(role="user", content="Session 1"))
        self.memory.add_message(session2, Message(role="user", content="Session 2"))

        # 验证会话隔离
        history1 = self.memory.get_history(session1)
        history2 = self.memory.get_history(session2)

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].content == "Session 1"
        assert history2[0].content == "Session 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
