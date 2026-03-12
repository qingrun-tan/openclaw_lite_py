import json
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# 引入我们在第一步创建的日志和配置
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.logger import logger
from src.config import config


@dataclass
class Message:
    """消息数据类，类似Java的POJO"""
    role: str
    content: str


@dataclass
class LLMResponse:
    """响应封装类"""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)  # token使用情况
    raw_response: Optional[Dict] = None


class LLMClient:
    """
    大模型客户端
    负责与OpenAI兼容接口（如通义千问、Kimi、DeepSeek等）进行交互
    """

    def __init__(self):
        self.api_key = config.API_KEY
        self.base_url = config.API_BASE
        self.model = config.MODEL_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 成本控制：Token计数
        self.total_tokens_used = 0
        self.max_tokens_limit = 100000  # 示例：单次运行上限预警

    def _build_payload(self, messages: List[Message], temperature: float = 0.7) -> Dict:
        """构建请求体"""
        return {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1000
        }

    def chat(self, messages: List[Message], retry_count: int = 3) -> LLMResponse:
        """
        发起对话请求
        包含了异常处理和重试机制
        """
        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages)

        logger.info(f"正在请求模型 {self.model}，消息数: {len(messages)}")

        for attempt in range(retry_count):
            try:
                # requests.post 类似于 Java的 httpClient.post()
                response = requests.post(url, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()  # 如果状态码不是200，抛出HTTPError

                data = response.json()

                # 解析响应
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                # 更新Token统计
                current_tokens = usage.get("total_tokens", 0)
                self.total_tokens_used += current_tokens
                self._check_cost_limit(current_tokens)

                logger.info(f"模型调用成功，消耗Token: {current_tokens}")

                return LLMResponse(
                    content=content,
                    model=data.get("model"),
                    usage=usage,
                    raw_response=data
                )

            except requests.exceptions.HTTPError as e:
                logger.error(f"API请求失败: {e.response.status_code} - {e.response.text}")
                # 简单的退避重试策略
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"API调用重试{retry_count}次后仍失败: {str(e)}")

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                raise Exception("模型返回了非JSON格式的数据")

            except Exception as e:
                logger.error(f"未知错误: {str(e)}")
                raise

    def _check_cost_limit(self, current_tokens: int):
        """成本预警"""
        if self.total_tokens_used > self.max_tokens_limit:
            logger.warning(f"警告：Token消耗已达上限 ({self.total_tokens_used})，请注意成本控制！")

    def get_system_prompt(self) -> str:
        """
        提示词工程
        设计System Prompt来约束模型行为，使其返回结构化数据
        """
        return """
        你是一个智能体助手。你的任务是解析用户的自然语言指令，并返回JSON格式的行动指令。

        请根据用户输入，返回以下JSON结构：
        {
            "thought": "思考过程：分析用户意图",
            "action_type": "操作类型：echo/unknown",
            "params": {
                "message": "需要回显的内容或执行参数"
            }
        }

        如果用户只是打招呼，action_type设为"echo"。
        如果无法理解，action_type设为"unknown"。
        """