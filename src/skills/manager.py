import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Type
from src.logger import logger
from .base import BaseSkill

class SkillManager:
    """
    技能管理器：单例模式，负责注册和查找技能
    """
    _instance = None
    _skills: Dict[str, Type[BaseSkill]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, skill_class: Type[BaseSkill]):
        """注册技能到管理器"""
        # 使用类名的小写作为技能ID
        skill_id = skill_class.__name__.lower()
        cls._skills[skill_id] = skill_class
        logger.info(f"技能已注册: {skill_id} -> {skill_class.description}")
        return skill_class

    @classmethod
    def get_skill(cls, skill_id: str) -> BaseSkill:
        """获取技能实例"""
        skill_class = cls._skills.get(skill_id.lower())
        if not skill_class:
            raise ValueError(f"未找到技能: {skill_id}")
        return skill_class()

# 定义装饰器，用于自动注册
def skill(cls):
    return SkillManager.register(cls)