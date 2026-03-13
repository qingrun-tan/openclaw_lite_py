"""
Agent Engine - ReAct 循环实现

ReAct (Reasoning + Acting) 是一种智能体推理范式：
- Reasoning: 模型分析问题，思考下一步行动
- Acting: 执行行动，获取观察结果
- 循环: 将观察结果反馈给模型，继续推理直到任务完成
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from .llm_client import LLMClient, Message
from ..memory import BaseMemory
from ..skills import SkillManager
from ..logger import logger


class AgentEngine:
    """
    智能体引擎：负责完整的观察-计划-行动循环
    """

    def __init__(
        self,
        llm_client: LLMClient,
        memory: BaseMemory,
        max_loops: int = 10,
        temperature: float = 0.7
    ):
        """
        初始化智能体引擎

        Args:
            llm_client: 大模型客户端
            memory: 记忆存储
            max_loops: 最大循环次数（防止死循环）
            temperature: 模型温度参数
        """
        self.llm_client = llm_client
        self.memory = memory
        self.max_loops = max_loops
        self.temperature = temperature

        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
        logger.info(f"AgentEngine 初始化完成，最大循环次数: {max_loops}")

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词，包含可用技能描述和工作流程指导
        """
        # 动态获取所有已注册技能的描述
        skill_descriptions = []
        for skill_id, skill_class in SkillManager._skills.items():
            skill_descriptions.append(f"- {skill_id}: {skill_class.description}")

        skills_text = "\n".join(skill_descriptions)

        return f"""你是一个功能强大的 AI 智能体助手，能够使用工具来完成复杂的任务。

## 可用工具

{skills_text}

## 工作流程

你将采用 ReAct (Reasoning + Acting) 模式来处理用户请求：

1. **思考 (Think)**: 分析用户的请求，理解需要做什么
2. **行动 (Act)**: 选择合适的工具并执行
3. **观察 (Observe)**: 观察工具执行的结果
4. **循环**: 根据观察结果继续思考，直到任务完成

## 回答格式

你必须始终以 JSON 格式回复，包含以下字段：

```json
{{
  "thought": "你的思考过程，解释你为什么选择这个行动",
  "action": "工具名称或 'final_answer'",
  "params": {{
    // 工具参数，仅当 action 不是 'final_answer' 时需要
  }},
  "final_answer": "最终答案，仅当 action 是 'final_answer' 时需要"
}}
```

## 重要规则

1. 如果任务可以通过现有知识直接回答，使用 `action: "final_answer"` 并提供答案
2. 如果需要使用工具，先在 `thought` 中说明你的推理过程
3. 工具执行失败时，分析失败原因并尝试其他方法
4. 如果任务过于复杂或超出能力范围，诚实说明
5. 始终确保 `action` 字段是一个有效的工具名称或 "final_answer"
6. 必须返回有效的 JSON 格式，不要添加任何额外文本

开始处理用户的请求吧！
"""

    def _parse_decision(self, raw_response: str) -> Dict[str, Any]:
        """
        解析模型的决策响应

        Args:
            raw_response: 模型返回的原始文本

        Returns:
            解析后的决策字典
        """
        # 尝试解析 JSON
        try:
            decision = json.loads(raw_response)
            # 验证必需字段
            if "action" not in decision:
                raise ValueError("决策中缺少 'action' 字段")
            return decision
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 原始响应: {raw_response[:100]}")
            # 尝试从文本中提取 JSON
            if "```json" in raw_response:
                try:
                    json_start = raw_response.find("```json") + 7
                    json_end = raw_response.find("```", json_start)
                    decision = json.loads(raw_response[json_start:json_end].strip())
                    return decision
                except:
                    pass
            elif "```" in raw_response:
                try:
                    json_start = raw_response.find("```") + 3
                    json_end = raw_response.find("```", json_start)
                    decision = json.loads(raw_response[json_start:json_end].strip())
                    return decision
                except:
                    pass

            # 如果无法解析，作为最终答案处理
            return {
                "action": "final_answer",
                "thought": "模型未返回有效的 JSON 格式，将响应作为最终答案",
                "final_answer": raw_response.strip()
            }

    def _execute_action(self, action: str, params: Dict[str, Any]) -> str:
        """
        执行指定的动作

        Args:
            action: 动作名称
            params: 动作参数

        Returns:
            执行结果字符串
        """
        try:
            # 检查是否为最终答案
            if action == "final_answer":
                return params.get("final_answer", "")

            # 获取技能实例
            skill = Skill.get_skill(action)

            # 执行安全检查
            if hasattr(skill, 'risk_check') and not skill.risk_check(params):
                logger.warning(f"安全检查失败: {action}")
                return f"错误: 安全检查未通过，拒绝执行此操作"

            # 执行技能
            result = skill.execute(params)
            logger.info(f"技能 {action} 执行成功")
            return result

        except ValueError as e:
            error_msg = f"错误: 找不到技能 '{action}'，可用技能: {list(SkillManager._skills.keys())}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"技能执行异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def run_async(self, user_input: str, session_id: str) -> str:
        """
        异步执行请求（生产环境推荐）

        Args:
            user_input: 用户输入
            session_id: 会话 ID

        Returns:
            最终响应字符串
        """
        # 为了支持真正的异步，这里可以并行执行多个操作
        # 目前简单包装同步调用
        await asyncio.sleep(0.01)
        return self.run(user_input, session_id)

    def run(self, user_input: str, session_id: str) -> str:
        """
        执行请求的主入口（同步）

        Args:
            user_input: 用户输入
            session_id: 会话 ID

        Returns:
            最终响应字符串
        """
        logger.info(f"开始处理请求: {user_input[:50]}...")

        # 1. 观察：加载会话历史
        history = self.memory.get_history(session_id)

        # 如果是新的会话，添加系统提示词
        if not history or history[0].role != "system":
            history = [Message(role="system", content=self.system_prompt)]
        else:
            # 确保系统提示词是最新的
            history[0] = Message(role="system", content=self.system_prompt)

        # 添加用户输入
        history.append(Message(role="user", content=user_input))

        # 2. ReAct 循环
        thoughts = []  # 记录思考过程
        observations = []  # 记录观察结果

        for loop_count in range(1, self.max_loops + 1):
            logger.info(f"ReAct 循环 #{loop_count}")

            try:
                # 调用大模型
                llm_response = self.llm_client.chat(history, temperature=self.temperature)
                decision_raw = llm_response.content

                logger.info(f"模型决策: {decision_raw[:200]}...")

                # 解析决策
                decision = self._parse_decision(decision_raw)
                action = decision.get("action", "").strip().lower()
                thought = decision.get("thought", "")
                params = decision.get("params", {})

                # 记录思考过程
                thoughts.append(f"#{loop_count}. {thought}")

                # 保存模型响应到历史
                history.append(Message(role="assistant", content=decision_raw))

                # 检查是否为最终答案
                if action == "final_answer":
                    final_answer = decision.get("final_answer", "")

                    # 保存最终答案到记忆
                    self.memory.add_message(session_id, Message(role="user", content=user_input))
                    self.memory.add_message(session_id, Message(role="assistant", content=decision_raw))

                    # 构建完整响应
                    if len(thoughts) > 1:
                        response = f"## 思考过程\n\n"
                        response += "\n".join(thoughts) + "\n\n"
                        response += f"## 最终答案\n\n{final_answer}"
                    else:
                        response = final_answer

                    logger.info("ReAct 循环完成，返回最终答案")
                    return response

                # 执行行动
                observation = self._execute_action(action, params)
                observations.append(f"#{loop_count}. 执行 {action}: {observation[:100]}...")

                # 将观察结果添加到历史，供模型继续推理
                history.append(Message(role="user", content=f"观察结果: {observation}"))

                logger.info(f"观察结果: {observation[:100]}...")

            except Exception as e:
                logger.error(f"ReAct 循环异常: {e}", exc_info=True)
                return f"处理过程中出现错误: {str(e)}"

        # 超过最大循环次数
        error_msg = f"达到最大循环次数 ({self.max_loops})，任务未完成。"
        logger.error(error_msg)

        # 保存交互历史
        self.memory.add_message(session_id, Message(role="user", content=user_input))
        self.memory.add_message(session_id, Message(role="assistant", content=error_msg))

        return f"{error_msg}\n\n## 已完成的步骤\n\n" + "\n".join(observations)


# 导出别名，方便使用
from ..skills import SkillManager
Skill = SkillManager
