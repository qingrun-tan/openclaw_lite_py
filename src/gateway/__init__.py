"""
Gateway 层 - 平台适配器统一导入
"""
from .base import BaseGateway
from .cli_adapter import CliGateway
from .web_adapter import WebGateway, WebSocketGateway

__all__ = ['BaseGateway', 'CliGateway', 'WebGateway', 'WebSocketGateway']
