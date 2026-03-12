from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseSkill(ABC):
    """
    技能基类
    所有具体技能（如读文件、执行命令）都需继承此类
    """

    # 技能描述，用于告诉AI这个技能是做什么的
    description: str = "Base skill description"

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> str:
        """
        执行技能逻辑
        :param params: Agent解析出的参数
        :return: 执行结果字符串
        """
        pass

    def risk_check(self, params: Dict[str, Any]) -> bool:
        """
        安全护栏：高风险操作检查
        返回 True 表示允许执行，False 表示拦截
        """
        return True