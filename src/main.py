import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.config import config
from src.logger import logger
from src.gateway.cli_adapter import CliGateway
from src.agent.llm_client import LLMClient, Message
from src.memory import FileMemory
# 引入Skills
from src.skills import SkillManager


def main():
    logger.info("OpenClaw Lite 正在启动...")

    # 初始化组件
    gateway = CliGateway()
    llm_client = LLMClient()
    memory = FileMemory()

    # --- 关键点：导入技能模块以触发装饰器注册 ---
    # 在Java中，这可能需要XML配置或ComponentScan扫描
    # 在Python中，只需import，装饰器就会自动运行
    import src.skills.builtin_skills

    logger.info("系统就绪。")

    # 更新System Prompt，告诉AI它现在有哪些技能可用
    # 动态生成技能列表描述
    skill_descriptions = "\n".join([f"- {name}: {cls.description}" for name, cls in SkillManager._skills.items()])

    system_prompt_content = f"""
    你是一个智能体助手。你可以使用以下工具：
    {skill_descriptions}

    请根据用户指令，返回JSON格式的行动指令：
    {{
        "thought": "思考过程",
        "action_type": "技能名称（如 echoskill, readfileskill, runcommandskill）",
        "params": {{ "key": "value" }}
    }}
    如果涉及到文件地址，则key为file_path
    如果只是聊天，action_type设为 "echoskill"。
    """

    system_prompt = Message(role="system", content=system_prompt_content)

    while True:
        request = gateway.receive()
        if request.get("action") == "exit":
            break

        user_input = request.get("content")
        session_id = request.get("session_id")
        user_id = request.get("user_id")

        history = memory.get_history(session_id)
        # if not history:
        history.append(system_prompt)
        history.append(Message(role="user", content=user_input))

        try:
            llm_response = llm_client.chat(history)
            agent_decision = json.loads(llm_response.content)
            logger.info(f"Agent决策: {agent_decision}")

            action_type = agent_decision.get("action_type")
            params = agent_decision.get("params", {})

            reply_text = ""

            # 尝试调用技能
            try:
                if action_type:
                    skill_instance = SkillManager.get_skill(action_type)
                    # 执行技能
                    result = skill_instance.execute(params)
                    reply_text = f"[执行成功] {result}"
                else:
                    reply_text = "Agent未指定操作类型。"
            except ValueError as e:
                reply_text = f"技能调用失败: {str(e)}"
            except Exception as e:
                reply_text = f"技能执行异常: {str(e)}"
                logger.error(f"Skill执行异常: {e}", exc_info=True)

            # 更新记忆
            memory.add_message(session_id, Message(role="user", content=user_input))
            memory.add_message(session_id, Message(role="assistant", content=llm_response.content))

            gateway.send(reply_text, user_id)

        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
            gateway.send(f"系统内部错误: {str(e)}", user_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"系统发生致命错误: {str(e)}", exc_info=True)