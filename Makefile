# Model Finetune UI - UV Makefile
# 简化常用的uv操作命令

.PHONY: help install install-dev update clean lint format type-check test run build deploy

# 默认目标
help:
	@echo "Model Finetune UI - UV项目管理"
	@echo ""
	@echo "可用命令:"
	@echo "  install      安装生产依赖"
	@echo "  install-dev  安装开发依赖"
	@echo "  update       更新所有依赖"
	@echo "  clean        清理缓存和临时文件"
	@echo "  lint         代码检查 (ruff)"
	@echo "  format       代码格式化 (black + ruff)"
	@echo "  type-check   类型检查 (mypy)"
	@echo "  test         运行测试"
	@echo "  run          启动应用"
	@echo "  run-dev      开发模式启动应用"
	@echo "  sample-data  生成示例数据"
	@echo "  build        构建项目"
	@echo "  deploy       部署准备"
	@echo "  setup        初始环境设置"

# 安装依赖
install:
	@echo "🔧 安装生产依赖..."
	uv sync

install-dev:
	@echo "🔧 安装开发依赖..."
	uv sync --dev

# 更新依赖
update:
	@echo "📦 更新依赖..."
	uv lock --upgrade
	uv sync

# 清理
clean:
	@echo "🧹 清理项目..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name "*~" -delete 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	rm -rf ui_output/ 2>/dev/null || true
	@echo "✅ 清理完成"

# 代码质量
lint:
	@echo "🔍 运行代码检查..."
	uv run ruff check .
	@echo "✅ 代码检查完成"

format:
	@echo "🎨 格式化代码..."
	uv run black .
	uv run ruff check --fix .
	@echo "✅ 代码格式化完成"

type-check:
	@echo "🔍 类型检查..."
	uv run mypy .
	@echo "✅ 类型检查完成"

# 测试
test:
	@echo "🧪 运行测试..."
	uv run pytest tests/ -v --cov=. --cov-report=term-missing
	@echo "✅ 测试完成"

# 运行应用
run:
	@echo "🚀 启动应用..."
	uv run model-finetune-ui

run-dev:
	@echo "🚀 开发模式启动应用..."
	UV_DEBUG=true uv run streamlit run app.py --server.runOnSave true

run-wsl:
	@echo "🚀 WSL环境启动应用..."
	./scripts/run-wsl.sh

# 示例数据
sample-data:
	@echo "📊 生成示例数据..."
	uv run generate-sample-data
	@echo "✅ 示例数据生成完成"

# 构建
build:
	@echo "🏗️ 构建项目..."
	uv build
	@echo "✅ 构建完成"

# 部署准备
deploy:
	@echo "🚀 准备部署..."
	@$(MAKE) clean
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	uv export --no-hashes --format requirements-txt > requirements.txt
	@echo "✅ 部署准备完成"

# 初始设置
setup:
	@echo "⚙️ 初始环境设置..."
	chmod +x scripts/*.sh
	./scripts/setup-uv.sh
	@echo "✅ 环境设置完成"

# Docker相关
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t model-finetune-ui .
	@echo "✅ Docker镜像构建完成"

docker-run:
	@echo "🐳 运行Docker容器..."
	docker run -p 8501:8501 \
		-e ENCRYPTION_KEY="${ENCRYPTION_KEY:-default-key-change-me}" \
		-e UI_OUTPUT_DIR="/app/output" \
		-v "$$(pwd)/ui_output:/app/output" \
		model-finetune-ui

# 开发工具
dev-tools:
	@echo "🔧 安装开发工具..."
	uv add --dev pre-commit
	uv run pre-commit install
	@echo "✅ 开发工具安装完成"

# 检查项目状态
status:
	@echo "📊 项目状态检查..."
	@echo "UV版本: $$(uv --version)"
	@echo "Python版本: $$(uv run python --version)"
	@echo "项目依赖数量: $$(uv tree | wc -l)"
	@if [ -f "uv.lock" ]; then echo "✅ 依赖锁定文件存在"; else echo "❌ 依赖锁定文件缺失"; fi
	@if [ -f ".env" ]; then echo "✅ 环境配置文件存在"; else echo "⚠️ 环境配置文件缺失 (可选)"; fi
	@echo ""
	@echo "最近的Git提交:"
	@git log --oneline -5 2>/dev/null || echo "未初始化Git仓库"

# 快速启动（适合新用户）
quickstart:
	@echo "🚀 快速启动 Model Finetune UI"
	@echo "================================"
	@$(MAKE) install
	@$(MAKE) sample-data
	@echo ""
	@echo "✅ 准备完成！现在可以运行 'make run' 启动应用"
	@echo "📖 更多信息请查看 README.md"