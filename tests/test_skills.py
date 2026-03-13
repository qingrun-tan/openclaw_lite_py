"""
技能系统单元测试

测试技能管理器和内置技能的功能
"""
import pytest
import sys
import os

# 添加 src 到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills import SkillManager, skill, BaseSkill
from src.skills.base import BaseSkill as BaseSkillOrigin
from src.skills.builtin_skills import (
    Echoeskill, CalculatorSkill, DateTimeSkill,
    TextProcessSkill, JsonProcessSkill
)


class TestSkillManager:
    """技能管理器测试"""

    def test_register_skill(self):
        """测试技能注册"""
        initial_count = len(SkillManager._skills)

        # 创建临时技能类
        @skill
        class TestSkill(BaseSkill):
            description = "测试技能"

            def execute(self, params):
                return "test"

        # 验证技能已注册
        assert len(SkillManager._skills) == initial_count + 1
        assert "testskill" in SkillManager._skills

    def test_get_skill(self):
        """测试获取技能实例"""
        skill_instance = SkillManager.get_skill("echoskill")
        assert isinstance(skill_instance, Echoeskill)

    def test_get_skill_not_found(self):
        """测试获取不存在的技能"""
        with pytest.raises(ValueError):
            SkillManager.get_skill("nonexistent_skill")


class TestBuiltInSkills:
    """内置技能测试"""

    def test_echo_skill(self):
        """测试回显技能"""
        skill = Echoeskill()
        result = skill.execute({"message": "Hello, World!"})
        assert result == "Hello, World!"

    def test_calculator_skill_basic(self):
        """测试计算器基本运算"""
        skill = CalculatorSkill()
        assert skill.execute({"expression": "2 + 2"}) == "4"
        assert skill.execute({"expression": "10 * 5"}) == "50"
        assert skill.execute({"expression": "20 / 4"}) == "5.0"

    def test_calculator_skill_functions(self):
        """测试计算器函数"""
        skill = CalculatorSkill()
        assert "3.141593" in skill.execute({"expression": "round(pi, 6)"})
        assert skill.execute({"expression": "sqrt(16)"}) == "4.0"
        assert skill.execute({"expression": "abs(-5)"}) == "5"

    def test_calculator_skill_security(self):
        """测试计算器安全检查"""
        skill = CalculatorSkill()
        # 危险表达式应该被拦截
        result = skill.execute({"expression": "__import__('os').system('ls')"})
        assert "错误" in result

    def test_datetime_skill(self):
        """测试时间技能"""
        skill = DateTimeSkill()
        # 测试当前时间
        assert len(skill.execute({"action": "current_time"})) == 8
        # 测试当前日期
        assert len(skill.execute({"action": "current_date"})) == 10
        # 测试时间戳
        timestamp = skill.execute({"action": "current_timestamp"})
        assert timestamp.isdigit()

    def test_text_process_skill(self):
        """测试文本处理技能"""
        skill = TextProcessSkill()

        # 长度
        assert skill.execute({"action": "length", "text": "hello"}) == "5"

        # 大小写
        assert skill.execute({"action": "upper", "text": "hello"}) == "HELLO"
        assert skill.execute({"action": "lower", "text": "HELLO"}) == "hello"

        # 替换
        assert skill.execute({"action": "replace", "text": "hello world", "old": "world", "new": "python"}) == "hello python"

        # 计数
        assert skill.execute({"action": "count", "text": "hello world", "substring": "l"}) == "3"

    def test_json_process_skill(self):
        """测试 JSON 处理技能"""
        skill = JsonProcessSkill()
        json_str = '{"name": "test", "value": 123}'

        # 解析
        result = skill.execute({"action": "parse", "json_str": json_str})
        assert "test" in result
        assert "123" in result

        # 获取键值
        result = skill.execute({"action": "get", "json_str": json_str, "key": "name"})
        assert "test" in result

    def test_json_process_skill_invalid(self):
        """测试无效 JSON 处理"""
        skill = JsonProcessSkill()
        result = skill.execute({"action": "parse", "json_str": "invalid json"})
        assert "错误" in result


class TestSkillSecurity:
    """技能安全测试"""

    def test_echo_skill_risk_check(self):
        """测试回显技能无安全限制"""
        skill = Echoeskill()
        assert skill.risk_check({"message": "any content"}) is True

    def test_calculator_skill_risk_check(self):
        """测试计算器安全检查"""
        skill = CalculatorSkill()

        # 正常表达式应该通过
        assert skill.risk_check({"expression": "2 + 2"}) is True

        # 危险表达式应该被拦截
        assert skill.risk_check({"expression": "import os"}) is False
        assert skill.risk_check({"expression": "__import__('os')"}) is False
        assert skill.risk_check({"expression": "open('/etc/passwd')"}) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
