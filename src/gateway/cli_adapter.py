import uuid
from .base import BaseGateway
from typing import Dict, Any


class CliGateway(BaseGateway):
    """
    命令行适配器
    用于本地测试，模拟用户输入
    """

    def __init__(self):
        # 模拟一个固定的测试用户
        self.user_id = "cli_user_001"
        self.session_id = str(uuid.uuid4())

    def receive(self) -> Dict[str, Any]:
        try:
            # input() 类似于 Java的 Scanner.nextLine()
            content = input("\n[User] 请输入指令 (输入 'exit' 退出): ")
            if content.lower() in ['exit', 'quit']:
                return {"action": "exit"}

            return {
                "user_id": self.user_id,
                "content": content,
                "session_id": self.session_id
            }
        except EOFError:
            return {"action": "exit"}

    def send(self, message: str, user_id: str):
        print(f"\n[Agent] -> {message}")