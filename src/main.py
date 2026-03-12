import sys
import os
import asyncio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.config import config
from src.logger import logger
from src.gateway.cli_adapter import CliGateway
from src.agent import LLMClient
from src.agent.engine import AgentEngine
from src.memory import FileMemory
from src.skills import SkillManager

# 导入技能以触发注册
import src.skills.builtin_skills


async def main_async():
    """
    异步主函数：为后续扩展高并发做准备
    """
    logger.info("OpenClaw Lite 正在启动...")

    # 依赖注入组装
    llm_client = LLMClient()
    memory = FileMemory()
    engine = AgentEngine(llm_client, memory)
    gateway = CliGateway()

    logger.info("系统就绪。ReAct 循环已启动。")

    while True:
        request = gateway.receive()
        if request.get("action") == "exit":
            break

        user_input = request.get("content")
        session_id = request.get("session_id")
        user_id = request.get("user_id")

        logger.info(f"收到任务: {user_input[:20]}...")

        try:
            # 调用引擎处理 (使用await以支持潜在的异步扩展)
            response = await engine.run_async(user_input, session_id)
            gateway.send(response, user_id)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"主循环异常: {e}", exc_info=True)
            gateway.send(f"处理出错: {e}", user_id)


def main():
    """同步入口，启动事件循环"""
    try:
        # Python 3.7+ 推荐使用 asyncio.run
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出。")


if __name__ == "__main__":
    main()