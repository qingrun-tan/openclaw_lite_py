"""
内置技能库

包含常用的基础技能，涵盖了文件操作、系统命令、计算、时间等功能。
每个技能都实现了安全护栏机制，确保系统安全。
"""
import os
import subprocess
import datetime
import json
import re
import math
from typing import Dict, Any
from .base import BaseSkill
from src.skills.manager import skill, SkillManager
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config
from src.logger import logger


# ============================================================================
# 基础技能
# ============================================================================

@skill
class Echoeskill(BaseSkill):
    """回显消息，用于测试和调试"""
    description = "回显消息内容，用于测试和调试"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"message": "要回显的消息"}
        Returns:
            回显的消息
        """
        return params.get("message", "")


@skill
class FinalAnswerSkill(BaseSkill):
    """直接返回最终答案，不进行任何工具调用"""
    description = "直接返回最终答案，当任务可以通过现有知识直接回答时使用"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"answer": "最终答案"}
        Returns:
            最终答案
        """
        return params.get("answer", "")


# ============================================================================
# 文件操作技能
# ============================================================================

@skill
class ReadFileSkill(BaseSkill):
    """读取指定路径的文件内容"""
    description = "读取指定路径的文件内容，支持文本文件"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"file_path": "文件路径"}
        Returns:
            文件内容
        """
        path = params.get("file_path")
        if not path:
            return "错误：缺少 file_path 参数"

        # 【安全护栏1】路径穿越检查
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)

        if not abs_path.startswith(sandbox_dir):
            logger.warning(f"安全拦截：尝试访问沙箱外的文件 {abs_path}")
            return f"安全错误：仅允许访问沙箱目录 {sandbox_dir} 内的文件"

        if not os.path.exists(abs_path):
            return f"错误：文件不存在 {abs_path}"

        if not os.path.isfile(abs_path):
            return f"错误：{abs_path} 不是文件"

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 限制返回内容长度，避免 Token 溢出
                if len(content) > 50000:
                    logger.info(f"文件内容过长，返回前 50000 字符")
                    return content[:50000] + "\n\n... (内容过长，已截断)"
                return content
        except UnicodeDecodeError:
            try:
                with open(abs_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return f"错误：文件编码不支持，请确保是文本文件"
        except Exception as e:
            return f"读取文件失败: {str(e)}"


@skill
class WriteFileSkill(BaseSkill):
    """将内容写入指定文件"""
    description = "将内容写入指定路径的文件（会覆盖原有内容）"

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查文件路径是否在沙箱内"""
        path = params.get("file_path", "")
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)
        return abs_path.startswith(sandbox_dir)

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"file_path": "文件路径", "content": "要写入的内容"}
        Returns:
            操作结果
        """
        path = params.get("file_path")
        content = params.get("content", "")

        if not path:
            return "错误：缺少 file_path 参数"

        if not self.risk_check(params):
            return "安全错误：只能在沙箱目录内创建文件"

        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)

        # 确保目录存在
        dir_path = os.path.dirname(abs_path)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                return f"创建目录失败: {str(e)}"

        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"文件已写入: {abs_path}")
            return f"成功写入文件: {abs_path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"


@skill
class AppendFileSkill(BaseSkill):
    """在文件末尾追加内容"""
    description = "在指定文件的末尾追加内容，不覆盖原有内容"

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查文件路径是否在沙箱内"""
        path = params.get("file_path", "")
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)
        return abs_path.startswith(sandbox_dir)

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"file_path": "文件路径", "content": "要追加的内容"}
        Returns:
            操作结果
        """
        path = params.get("file_path")
        content = params.get("content", "")

        if not path:
            return "错误：缺少 file_path 参数"

        if not self.risk_check(params):
            return "安全错误：只能在沙箱目录内操作文件"

        abs_path = os.path.abspath(path)

        try:
            with open(abs_path, 'a', encoding='utf-8') as f:
                f.write(content if content.endswith('\n') else content + '\n')
            logger.info(f"文件已追加内容: {abs_path}")
            return f"成功追加内容到文件: {abs_path}"
        except Exception as e:
            return f"追加文件失败: {str(e)}"


@skill
class ListDirectorySkill(BaseSkill):
    """列出指定目录下的文件和子目录"""
    description = "列出指定目录下的文件和子目录"

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查目录路径是否在沙箱内"""
        path = params.get("dir_path", config.SANDBOX_DIR)
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)
        return abs_path.startswith(sandbox_dir)

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"dir_path": "目录路径（可选，默认为沙箱目录）", "recursive": "是否递归（可选，默认 false）"}
        Returns:
            目录内容列表
        """
        dir_path = params.get("dir_path", config.SANDBOX_DIR)
        recursive = params.get("recursive", False)

        if not dir_path:
            dir_path = config.SANDBOX_DIR

        if not self.risk_check(params):
            return "安全错误：只能列出沙箱目录内的内容"

        abs_path = os.path.abspath(dir_path)

        if not os.path.exists(abs_path):
            return f"错误：目录不存在 {abs_path}"

        if not os.path.isdir(abs_path):
            return f"错误：{abs_path} 不是目录"

        try:
            result = []

            def scan_directory(dpath, level=0):
                items = os.listdir(dpath)
                items.sort()

                for item in items:
                    item_path = os.path.join(dpath, item)
                    prefix = "  " * level

                    if os.path.isdir(item_path):
                        result.append(f"{prefix}[DIR] {item}/")
                        if recursive and level < 5:  # 限制递归深度
                            scan_directory(item_path, level + 1)
                    else:
                        size = os.path.getsize(item_path)
                        size_str = f"{size} B" if size < 1024 else f"{size // 1024} KB"
                        result.append(f"{prefix}[FILE] {item} ({size_str})")

            scan_directory(abs_path)
            return "\n".join(result) if result else "目录为空"

        except Exception as e:
            return f"列出目录失败: {str(e)}"


@skill
class DeleteFileSkill(BaseSkill):
    """删除指定文件"""
    description = "删除指定的文件（高危操作，需谨慎）"

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查文件路径是否在沙箱内"""
        path = params.get("file_path", "")
        abs_path = os.path.abspath(path)
        sandbox_dir = os.path.abspath(config.SANDBOX_DIR)
        return abs_path.startswith(sandbox_dir)

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"file_path": "文件路径"}
        Returns:
            操作结果
        """
        path = params.get("file_path")

        if not path:
            return "错误：缺少 file_path 参数"

        if not self.risk_check(params):
            return "安全错误：只能在沙箱目录内删除文件"

        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return f"错误：文件不存在 {abs_path}"

        try:
            os.remove(abs_path)
            logger.info(f"文件已删除: {abs_path}")
            return f"成功删除文件: {abs_path}"
        except Exception as e:
            return f"删除文件失败: {str(e)}"


# ============================================================================
# 系统命令技能
# ============================================================================

@skill
class RunCommandSkill(BaseSkill):
    """执行系统命令（高风险，需白名单）"""
    description = "执行系统命令（仅限白名单内的安全命令）"

    # 【安全护栏】命令白名单
    ALLOWED_COMMANDS = {
        # 文件系统
        "ls", "dir", "pwd", "cd",
        # 信息查看
        "echo", "date", "time", "whoami", "hostname", "uname",
        # 网络
        "ping", "curl", "wget", "nslookup",
        # 进程
        "ps", "top", "htop",
        # 其他
        "cat", "head", "tail", "grep", "wc", "tr", "cut"
    }

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查命令是否在白名单内"""
        cmd = params.get("command", "")
        cmd_name = cmd.split()[0] if cmd else ""

        if cmd_name not in self.ALLOWED_COMMANDS:
            logger.warning(f"安全拦截：未授权的命令尝试执行 '{cmd_name}'")
            return False
        return True

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"command": "要执行的命令", "timeout": "超时秒数（可选，默认10）"}
        Returns:
            命令执行结果
        """
        cmd = params.get("command", "")
        timeout = params.get("timeout", 10)

        if not cmd:
            return "错误：缺少 command 参数"

        if not self.risk_check(params):
            cmd_name = cmd.split()[0] if cmd else ""
            return f"安全错误：命令 '{cmd_name}' 不在白名单中，执行被拒绝。"

        try:
            # 【安全护栏】超时控制
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout if result.stdout else result.stderr
            logger.info(f"命令执行成功: {cmd[:50]}...")

            # 限制输出长度
            if len(output) > 5000:
                output = output[:5000] + "\n\n... (输出过长，已截断)"

            return output
        except subprocess.TimeoutExpired:
            return f"错误：命令执行超时（{timeout}秒）"
        except Exception as e:
            return f"执行出错: {str(e)}"


# ============================================================================
# 计算技能
# ============================================================================

@skill
class CalculatorSkill(BaseSkill):
    """执行数学计算"""
    description = "执行数学计算，支持基本运算符（+, -, *, /, %, ** 等）和常用数学函数"

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """检查表达式是否安全"""
        expression = params.get("expression", "")

        # 禁止危险的关键字
        dangerous_keywords = [
            "import", "exec", "eval", "compile", "open", "file",
            "__", "os", "sys", "subprocess", "commands", "system",
            "shell", "pipe", "popen"
        ]

        for keyword in dangerous_keywords:
            if keyword in expression.lower():
                logger.warning(f"安全拦截：计算表达式包含危险关键字 '{keyword}'")
                return False

        return True

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {"expression": "数学表达式，如 2 * (3 + 4) 或 sin(0.5)"}
        Returns:
            计算结果
        """
        expression = params.get("expression", "").strip()

        if not expression:
            return "错误：缺少 expression 参数"

        if not self.risk_check(params):
            return "安全错误：表达式包含不安全的内容"

        try:
            # 创建安全的计算环境
            safe_globals = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "sqrt": math.sqrt,
                "pow": math.pow,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
            }

            # 执行计算
            result = eval(expression, {"__builtins__": {}}, safe_globals)

            # 格式化结果
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 6)

            return str(result)

        except ZeroDivisionError:
            return "错误：除零错误"
        except NameError as e:
            return f"错误：未知的函数或变量 - {str(e)}"
        except SyntaxError as e:
            return f"错误：表达式语法错误 - {str(e)}"
        except Exception as e:
            return f"计算错误: {str(e)}"


# ============================================================================
# 时间日期技能
# ============================================================================

@skill
class DateTimeSkill(BaseSkill):
    """获取当前时间或格式化时间"""
    description = "获取当前时间或解析/格式化时间字符串"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {
                "action": "获取类型：current_time/current_date/current_datetime/parse/format（可选，默认 current_datetime）",
                "format": "时间格式字符串（可选）",
                "timestamp": "要解析的时间戳（可选）"
            }
        Returns:
            时间信息
        """
        action = params.get("action", "current_datetime")
        format_str = params.get("format", "")
        timestamp = params.get("timestamp")

        try:
            if action == "current_time":
                return datetime.datetime.now().strftime("%H:%M:%S")

            elif action == "current_date":
                return datetime.datetime.now().strftime("%Y-%m-%d")

            elif action == "current_datetime":
                if format_str:
                    return datetime.datetime.now().strftime(format_str)
                return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            elif action == "current_timestamp":
                return str(int(datetime.datetime.now().timestamp()))

            elif action == "parse" and timestamp:
                dt = datetime.datetime.fromtimestamp(float(timestamp))
                return dt.strftime("%Y-%m-%d %H:%M:%S")

            elif action == "info":
                now = datetime.datetime.now()
                info = {
                    "timestamp": str(int(now.timestamp())),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "iso": now.isoformat(),
                    "timezone": "UTC"  # 简化版
                }
                return json.dumps(info, indent=2, ensure_ascii=False)

            else:
                return "错误：未知的 action 值，支持：current_time/current_date/current_datetime/current_timestamp/parse/info"

        except Exception as e:
            return f"时间操作失败: {str(e)}"


# ============================================================================
# 文本处理技能
# ============================================================================

@skill
class TextProcessSkill(BaseSkill):
    """文本处理工具"""
    description = "处理文本，包括长度计算、大小写转换、查找替换、分割等"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {
                "action": "操作类型：length/lower/upper/replace/split/count/trim",
                "text": "要处理的文本",
                "old": "要替换的旧字符串（replace 时需要）",
                "new": "要替换的新字符串（replace 时需要）",
                "delimiter": "分隔符（split 时需要，默认空格）",
                "substring": "要查找或计数的子字符串（count 时需要）"
            }
        Returns:
            处理结果
        """
        action = params.get("action", "")
        text = params.get("text", "")

        if not text:
            return "错误：缺少 text 参数"

        try:
            if action == "length":
                return str(len(text))

            elif action == "lower":
                return text.lower()

            elif action == "upper":
                return text.upper()

            elif action == "replace":
                old = params.get("old", "")
                new = params.get("new", "")
                if old is None:
                    old = ""
                return text.replace(old, new)

            elif action == "split":
                delimiter = params.get("delimiter", " ")
                parts = text.split(delimiter)
                return "\n".join(parts)

            elif action == "count":
                substring = params.get("substring", "")
                return str(text.count(substring))

            elif action == "trim":
                return text.strip()

            elif action == "reverse":
                return text[::-1]

            else:
                return f"错误：未知的 action 值，支持：length/lower/upper/replace/split/count/trim/reverse"

        except Exception as e:
            return f"文本处理失败: {str(e)}"


# ============================================================================
# JSON 处理技能
# ============================================================================

@skill
class JsonProcessSkill(BaseSkill):
    """JSON 处理工具"""
    description = "解析、格式化或查询 JSON 数据"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {
                "action": "操作类型：parse/format/get",
                "json_str": "JSON 字符串",
                "key": "要获取的键（get 时需要）",
                "indent": "格式化缩进（format 时需要，默认 2）"
            }
        Returns:
            处理结果
        """
        action = params.get("action", "")
        json_str = params.get("json_str", "")

        if not json_str:
            return "错误：缺少 json_str 参数"

        try:
            if action == "parse":
                data = json.loads(json_str)
                return json.dumps(data, ensure_ascii=False, indent=2)

            elif action == "format":
                indent = params.get("indent", 2)
                data = json.loads(json_str)
                return json.dumps(data, ensure_ascii=False, indent=indent)

            elif action == "get":
                key = params.get("key", "")
                data = json.loads(json_str)
                if key in data:
                    value = data[key]
                    if isinstance(value, (dict, list)):
                        return json.dumps(value, ensure_ascii=False, indent=2)
                    return str(value)
                return f"错误：键 '{key}' 不存在"

            else:
                return "错误：未知的 action 值，支持：parse/format/get"

        except json.JSONDecodeError as e:
            return f"错误：JSON 解析失败 - {str(e)}"
        except Exception as e:
            return f"JSON 处理失败: {str(e)}"


# ============================================================================
# 记忆管理技能
# ============================================================================

@skill
class MemoryControlSkill(BaseSkill):
    """控制会话记忆"""
    description = "清除会话记忆或获取记忆摘要（系统内部使用）"

    def execute(self, params: Dict[str, Any]) -> str:
        """
        Args:
            params: {
                "action": "操作类型：clear/summary",
                "session_id": "会话 ID"
            }
        Returns:
            操作结果
        """
        # 这个技能通常由系统内部调用，不完全通过技能管理器
        return "此技能需要直接访问 Memory 实例，请通过 API 调用"


# 日志输出
logger.info(f"内置技能库已加载，共注册 {len(SkillManager._skills)} 个技能")
