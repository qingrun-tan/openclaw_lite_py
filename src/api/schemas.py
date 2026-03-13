"""
API 数据模型定义

使用 Pydantic 进行数据验证和序列化
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============================================================================
# 聊天相关
# ============================================================================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户输入的消息", min_length=1, max_length=5000)
    session_id: Optional[str] = Field("default", description="会话 ID")
    user_id: Optional[str] = Field("api_user", description="用户 ID")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="智能体的回复")
    session_id: str = Field(..., description="会话 ID")
    status: str = Field("success", description="状态标识")


# ============================================================================
# 会话管理
# ============================================================================

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话 ID")
    message_count: int = Field(..., description="消息数量")
    created_at: str = Field(..., description="创建时间")


class SessionCreateResponse(BaseModel):
    """创建会话响应"""
    session_id: str = Field(..., description="新创建的会话 ID")
    message: str = Field("会话创建成功", description="提示信息")


# ============================================================================
# 技能相关
# ============================================================================

class SkillInfo(BaseModel):
    """技能信息模型"""
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")


class SkillsListResponse(BaseModel):
    """技能列表响应"""
    count: int = Field(..., description="技能总数")
    skills: List[SkillInfo] = Field(..., description="技能列表")


# ============================================================================
# 系统信息
# ============================================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field("2.0.0", description="版本号")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细错误信息")
