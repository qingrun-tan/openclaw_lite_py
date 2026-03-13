"""
Pytest 配置文件

定义全局测试夹具和配置
"""
import pytest
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def test_session_id():
    """测试会话 ID"""
    return "test_session"


@pytest.fixture
def mock_env(monkeypatch):
    """模拟环境变量"""
    monkeypatch.setenv("OPENCLAW_API_KEY", "test_api_key")
    monkeypatch.setenv("OPENCLAW_API_BASE", "https://api.test.com/v1")
    monkeypatch.setenv("OPENCLAW_MODEL", "test-model")
    return monkeypatch
