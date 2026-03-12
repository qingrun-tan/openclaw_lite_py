openclaw_lite/
├── .env.template          # 环境变量模板（安全：不包含真实密钥）
├── .gitignore             # Git忽略文件（必须包含.env、__pycache__）
├── requirements.txt       # Python依赖管理（类似pom.xml）
├── README.md              # 项目文档
├── src/                   # 源代码目录
│   ├── __init__.py        # 标记src为包
│   ├── config.py          # 配置加载模块
│   ├── logger.py          # 日志配置模块
│   ├── gateway/           # 网关层
│   │   ├── __init__.py
│   │   ├── base.py        # 抽象基类（定义接口规范）
│   │   └── cli_adapter.py # 命令行适配器实现
│   └── main.py            # 程序入口
├── tests/                 # 单元测试目录
├── logs/                  # 日志输出目录
└── data/                  # 数据持久化目录