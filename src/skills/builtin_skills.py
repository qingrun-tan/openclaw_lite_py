import os
import subprocess
from typing import Dict, Any
from .base import BaseSkill
from src.skills.manager import skill  # 导入装饰器
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config
from src.logger import logger


@skill
class EchoSkill(BaseSkill):
    description = "回显消息，用于测试"

    def execute(self, params: Dict[str, Any]) -> str:
        return params.get("message", "")


@skill
class ReadFileSkill(BaseSkill):
    description = "读取指定路径的文件内容"

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("file_path")
        if not path:
            return "错误：缺少文件路径参数"

        # 【安全护栏1】路径穿越检查
        # 防止用户传入 ../../../etc/passwd
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)

        if not abs_path.startswith(sandbox_dir):
            logger.warning(f"安全拦截：尝试访问沙箱外的文件 {abs_path}")
            return f"安全错误：仅允许访问沙箱目录 {sandbox_dir} 内的文件"

        if not os.path.exists(abs_path):
            return f"错误：文件不存在 {abs_path}"

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取文件失败: {str(e)}"


@skill
class RunCommandSkill(BaseSkill):
    description = "执行系统命令（高风险，需白名单）"

    # 【安全护栏2】命令白名单
    ALLOWED_COMMANDS = {"ls", "dir", "echo", "date", "ping"}  # Windows/Linux通用示例

    def risk_check(self, params: Dict[str, Any]) -> bool:
        cmd = params.get("command", "")
        # 提取第一个单词作为命令名
        cmd_name = cmd.split()[0] if cmd else ""

        if cmd_name not in self.ALLOWED_COMMANDS:
            logger.warning(f"安全拦截：未授权的命令尝试执行 '{cmd_name}'")
            return False
        return True

    def execute(self, params: Dict[str, Any]) -> str:
        cmd = params.get("command")

        if not self.risk_check(params):
            return f"安全错误：命令 '{cmd}' 不在白名单中，执行被拒绝。"

        try:
            # 【安全护栏3】超时控制
            # 防止恶意命令挂起系统
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10  # 10秒超时
            )
            return result.stdout if result.stdout else result.stderr
        except subprocess.TimeoutExpired:
            return "错误：命令执行超时"
        except Exception as e:
            return f"执行出错: {str(e)}"