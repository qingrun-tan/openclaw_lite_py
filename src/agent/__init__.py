# src/agent/__init__.py

# 方式A：直接导入类（推荐，明确导出）
from .llm_client import LLMClient

# 这样，外部代码就可以直接 from agent import LLMClient 了
__all__ = ['LLMClient']