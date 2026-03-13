"""
Skills 层 - 技能管理器统一导入
"""
from .manager import SkillManager, skill
from .base import BaseSkill

__all__ = ['SkillManager', 'BaseSkill', 'skill']