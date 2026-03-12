import json
import asyncio
from typing import Optional
from .llm_client import LLMClient, Message
from ..memory import BaseMemory
from ..skills import SkillManager
from ..logger import logger


class AgentEngine:
    """
    智能体引擎：负责观察-计划-行动循环
    """

    def __init__(self, llm_client: LLMClient, memory: BaseMemory):
        self.llm_client = llm_client
        self.memory = memory
        self.max_loops = 5  # 防止死循环的最大思考次数

        # 构建System Prompt
        self._init_system_prompt()

    def _init_system_prompt(self):
        # 动态获取技能描述
        skill_desc = "\n".join([f"- {k}: {v.description}" for k, v in SkillManager._skills.items()])

        self.system_prompt = f"""
        你是一个由模型驱动的智能体。
        你拥有以下工具可以使用：
        {skill_desc}

        工作流程：
        1. 分析用户意图。
        2. 如果需要调用工具，返回JSON: {{"action_type": "tool_name", "params": {{...}}, "thought": "..."}}。
        3. 如果不需要工具，直接回答，返回JSON: {{"action_type": "echoskill", "params": {{"message": "回答内容"}}, "thought": "..."}}。

        重要：必须返回有效的JSON格式。
        """

    async def run_async(self, user_input: str, session_id: str) -> str:
        """
        异步执行单次请求（生产环境推荐）
        模拟IO密集型操作（如API调用、文件读写）的异步处理
        """
        # 模拟异步延迟（实际生产中await真正的IO操作）
        await asyncio.sleep(0.1)
        return self.run(user_input, session_id)

    def run(self, user_input: str, session_id: str) -> str:
        """
        同步执行单次请求的主入口
        """
        # 1. 观察：加载记忆
        history = self.memory.get_history(session_id)
        # if not history:
        history.append(Message(role="system", content=self.system_prompt))

        # 记录用户输入
        history.append(Message(role="user", content=user_input))

        # 2. 计划与行动：循环思考
        # 这里为了简化，我们做单步推理。
        # 完整的ReAct循环会在这里while True，直到Agent认为任务完成。

        try:
            # 调用大模型
            llm_resp = self.llm_client.chat(history)
            decision_raw = llm_resp.content

            logger.info(f"Agent原始决策: {decision_raw}")

            # 解析决策
            try:
                decision = json.loads(decision_raw)
            except json.JSONDecodeError:
                # 如果模型没返回JSON，强制包装一下
                decision = {
                    "action_type": "echoskill",
                    "params": {"message": decision_raw},
                    "thought": "模型未返回JSON，直接回显。"
                }

            # 执行行动
            action_type = decision.get("action_type", "").lower()
            params = decision.get("params", {})
            thought = decision.get("thought", "")

            final_response = ""

            if action_type:
                try:
                    skill = SkillManager.get_skill(action_type)
                    # 执行技能
                    result = skill.execute(params)
                    final_response = f"[Agent思考]: {thought}\n[执行结果]: {result}"
                except ValueError:
                    final_response = f"错误：找不到技能 {action_type}"
                except Exception as e:
                    final_response = f"技能执行异常: {str(e)}"
            else:
                final_response = decision_raw

            # 3. 记忆：保存交互
            # 注意：保存的是原始交互，而不是执行结果，防止模型混淆
            self.memory.add_message(session_id, Message(role="user", content=user_input))
            self.memory.add_message(session_id, Message(role="assistant", content=decision_raw))

            return final_response

        except Exception as e:
            logger.error(f"Agent运行失败: {e}", exc_info=True)
            return f"系统繁忙: {str(e)}"