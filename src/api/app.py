"""
FastAPI 应用 - OpenClaw Lite Web API

提供 RESTful API 接口，支持会话管理、聊天、技能查询等功能。
"""
import sys
import os
import uuid
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from .schemas import ChatRequest, ChatResponse, SessionInfo, SkillsListResponse
from ..agent import LLMClient
from src.agent.engine import AgentEngine
from ..memory import FileMemory, BaseMemory
from ..skills import SkillManager
from ..logger import logger
import src.skills.builtin_skills

# 全局组件实例（单例模式）
_llm_client = None
_engine = None
_memory = None


def get_components():
    """
    全局状态懒加载，确保只在第一次请求时初始化
    """
    global _llm_client, _engine, _memory
    if _engine is None:
        logger.info("初始化 Web 服务组件...")
        _llm_client = LLMClient()
        _memory = FileMemory()
        _engine = AgentEngine(_llm_client, _memory)
        logger.info("Web 服务组件就绪。")
    return _engine, _memory


def create_app():
    """创建 FastAPI 应用实例"""

    app = FastAPI(
        title="OpenClaw Lite API",
        description="企业级 AI 智能体接口 - ReAct 智能体框架",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加 CORS 中间件（允许前端跨域调用）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ============================================================================
    # 系统接口
    # ============================================================================

    @app.get("/")
    def read_root():
        """根路径 - 服务状态检查"""
        return {
            "message": "OpenClaw Lite is running",
            "status": "ok",
            "version": "2.0.0"
        }

    @app.get("/health")
    def health_check():
        """健康检查接口"""
        return {"status": "healthy"}

    @app.get("/skills", response_model=SkillsListResponse)
    def get_skills():
        """获取所有可用技能列表"""
        skills = []
        for skill_id, skill_class in SkillManager._skills.items():
            skills.append({
                "name": skill_id,
                "description": skill_class.description
            })

        return SkillsListResponse(
            count=len(skills),
            skills=skills
        )

    # ============================================================================
    # 会话管理接口
    # ============================================================================

    @app.post("/sessions", response_model=SessionInfo)
    def create_session():
        """创建新会话"""
        session_id = str(uuid.uuid4())
        return SessionInfo(
            session_id=session_id,
            message_count=0,
            created_at=os.path.basename(session_id)[:8]  # 简化时间
        )

    @app.get("/sessions/{session_id}", response_model=SessionInfo)
    def get_session_info(session_id: str):
        """获取会话信息"""
        _, memory = get_components()

        try:
            history = memory.get_history(session_id)
            message_count = len([m for m in history if m.role != "system"])

            return SessionInfo(
                session_id=session_id,
                message_count=message_count,
                created_at=os.path.basename(session_id)[:8]
            )
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}"
            )

    @app.delete("/sessions/{session_id}")
    def delete_session(session_id: str):
        """删除会话及其历史记录"""
        _, memory = get_components()

        try:
            memory.clear_session(session_id)
            logger.info(f"会话已删除: {session_id}")
            return {"message": "会话已删除", "session_id": session_id}
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除会话失败: {str(e)}"
            )

    # ============================================================================
    # 聊天接口
    # ============================================================================

    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest, req: Request):
        """
        核心聊天接口 - 支持 ReAct 循环

        Args: ChatRequest
            message: 用户输入的消息
            session_id: 会话 ID（可选，默认为 "default"）
            user_id: 用户 ID（可选，用于追踪）

        Returns: ChatResponse
            reply: 智能体回复
            session_id: 会话 ID
            status: 状态标识
        """
        try:
            # 获取客户端IP（简单的审计日志）
            client_host = req.client.host if req.client else "unknown"
            logger.info(f"收到 API 请求 from {client_host}: {request.message[:50]}...")

            # 获取组件
            engine, _ = get_components()

            # 调用 Agent 引擎
            reply_text = await engine.run_async(request.message, request.session_id)

            return ChatResponse(
                reply=reply_text,
                session_id=request.session_id,
                status="success"
            )

        except Exception as e:
            logger.error(f"API 处理异常: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}"
            )

    @app.post("/chat/stream")
    async def chat_stream(request: ChatRequest, req: Request):
        """
        流式聊天接口（预留接口，待实现）

        此接口将支持 SSE (Server-Sent Events) 流式输出，
        实时返回智能体的思考过程和执行结果。
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="流式接口正在开发中"
        )

    return app
