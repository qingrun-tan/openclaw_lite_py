import os
from dotenv import load_dotenv

'''
    配置文件  ===》   application.yml
'''

class Config:
    def __init__(self):
        # 加载.env文件，如果不存在则忽略；
        load_dotenv()
        self.API_KEY = os.getenv("OPENCLAW_API_KEY")
        self.API_BASE = os.getenv("OPENCLAW_API_BASE", "https://api.openai.com/v1")
        self.MODEL_NAME = os.getenv("OPENCLAW_MODEL", "kimi-k2.5")

        # 服务配置
        self.PORT = int(os.getenv("OPENCLAW_PORT", "18789"))

        # 安全配置
        self.SANDBOX_DIR = os.path.abspath(os.getenv("OPENCLAW_SANDBOX", "./data/sandbox"))

        # 初始化校验
        if not self.API_KEY:
            raise ValueError("安全错误：未检测到API_KEY，请在.env文件中配置。")

    # 全局单例模式
config = Config()