import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os


def setup_logger(name: str = "OpenClaw"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # 生产环境通常设为INFO或WARNING

    # 避免重复添加Handler
    if logger.handlers:
        return logger

    # 1. 控制台输出 (彩色日志，开发调试用)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # 2. 文件输出 (按天滚动，备查)
    # 确保logs目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = TimedRotatingFileHandler(
        f"{log_dir}/openclaw.log",
        when="midnight",
        interval=1,
        backupCount=7  # 保留7天
    )
    # 商用建议：使用json格式库，这里简化为标准文本
    file_formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# 全局日志实例
logger = setup_logger()