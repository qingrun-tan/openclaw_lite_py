# OpenClaw Lite - Makefile
# 用于快速执行常用命令

.PHONY: help install test run web clean docker-build docker-up docker-down

# 默认目标
help:
	@echo "OpenClaw Lite - 可用命令："
	@echo ""
	@echo "  make install      - 安装依赖"
	@echo "  make test         - 运行测试"
	@echo "  make run          - 启动 CLI 模式"
	@echo "  make web          - 启动 Web API 服务"
	@echo "  make clean        - 清理缓存和临时文件"
	@echo "  make docker-build  - 构建 Docker 镜像"
	@echo "  make docker-up    - 启动 Docker 容器"
	@echo "  make docker-down  - 停止 Docker 容器"

# 安装依赖
install:
	@echo "安装 Python 依赖..."
	pip install -r requirements.txt
	pip install fastapi uvicorn pydantic pytest pytest-asyncio

# 运行测试
test:
	@echo "运行测试..."
	pytest tests/ -v

# 启动 CLI 模式
run:
	@echo "启动 CLI 模式..."
	python src/main.py

# 启动 Web API 服务
web:
	@echo "启动 Web API 服务..."
	uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 18789 --reload

# 清理
clean:
	@echo "清理缓存和临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

# Docker 构建
docker-build:
	@echo "构建 Docker 镜像..."
	docker-compose build

# Docker 启动
docker-up:
	@echo "启动 Docker 容器..."
	docker-compose up -d

# Docker 停止
docker-down:
	@echo "停止 Docker 容器..."
	docker-compose down
