# 部署指南

本文档介绍如何将 Model Finetune UI 项目部署到不同的平台。

## 🚀 部署选项

### 方案 1: Streamlit Community Cloud (推荐)

**优点**: 免费、简单、官方支持  
**适用场景**: 开源项目、快速原型、演示应用

#### 步骤:

1. **准备GitHub仓库**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **访问 [Streamlit Cloud](https://share.streamlit.io/)**
   - 使用GitHub账号登录
   - 点击 "New app"
   - 选择你的仓库
   - 设置主分支为 `main`
   - 设置主文件为 `app.py`

3. **配置环境变量** (在Streamlit Cloud控制台)
   ```
   ENCRYPTION_KEY=your-32-character-key
   UI_OUTPUT_DIR=/tmp/ui_output
   UI_DEBUG=false
   ```

4. **部署完成**
   - Streamlit Cloud会自动构建和部署
   - 获得公开访问URL

### 方案 2: Docker 容器部署

**优点**: 完全控制、可私有、易扩展  
**适用场景**: 生产环境、企业内部部署

#### 本地测试:
```bash
# 构建镜像
docker build -t model-finetune-ui .

# 运行容器
docker run -p 8501:8501 \
  -e ENCRYPTION_KEY=your-32-character-key \
  -e UI_OUTPUT_DIR=/app/output \
  -v $(pwd)/ui_output:/app/output \
  model-finetune-ui
```

#### 云平台部署:

**Google Cloud Run:**
```bash
# 构建并推送到容器注册表
gcloud builds submit --tag gcr.io/PROJECT_ID/model-finetune-ui

# 部署到Cloud Run
gcloud run deploy --image gcr.io/PROJECT_ID/model-finetune-ui \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**AWS ECS/Fargate:**
```bash
# 推送到ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag model-finetune-ui:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/model-finetune-ui:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/model-finetune-ui:latest
```

### 方案 3: Heroku 部署

**优点**: 简单易用、集成度高  
**缺点**: 需要付费计划

#### 步骤:
1. **安装 Heroku CLI**
2. **创建应用**
   ```bash
   heroku create your-app-name
   ```

3. **设置环境变量**
   ```bash
   heroku config:set ENCRYPTION_KEY=your-key
   heroku config:set UI_OUTPUT_DIR=/tmp/ui_output
   ```

4. **创建 Procfile**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

5. **部署**
   ```bash
   git push heroku main
   ```

### 方案 4: GitHub Codespaces (开发环境)

**优点**: 快速启动、开发友好  
**适用场景**: 开发测试、临时演示

#### 步骤:
1. 在GitHub仓库中点击 "Code" -> "Codespaces" -> "Create codespace"
2. 在Codespace中运行:
   ```bash
   uv sync
   uv run streamlit run app.py
   ```

## 🔧 部署前准备

### 1. 环境变量配置

创建 `.env` 文件（基于 `.env.example`）:
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际值
```

**必须设置的环境变量:**
- `ENCRYPTION_KEY`: 32字符的加密密钥
- `UI_OUTPUT_DIR`: 输出目录路径

### 2. 依赖管理

确保 `requirements.txt` 包含所有必要依赖:
```bash
# 从pyproject.toml生成requirements.txt
uv export --no-hashes > requirements.txt
```

### 3. 安全配置

- 移除硬编码的敏感信息
- 设置适当的文件权限
- 配置HTTPS（生产环境）

## 🔒 安全考虑

### 环境变量安全
- 永远不要提交 `.env` 文件到版本控制
- 使用强随机密钥
- 定期轮换敏感密钥

### 文件上传安全
- 限制文件大小和类型
- 验证文件内容
- 使用临时目录处理上传文件

### 网络安全
- 在生产环境中启用HTTPS
- 配置适当的CORS策略
- 使用防火墙限制访问

## 📊 监控和日志

### 日志配置
```python
# 在生产环境中配置结构化日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 健康检查
- 配置应用健康检查端点
- 监控关键指标（响应时间、错误率）
- 设置告警通知

### 性能优化
- 启用Streamlit缓存
- 优化数据处理流程
- 配置适当的资源限制

## 🔄 CI/CD 流程

GitHub Actions工作流已配置在 `.github/workflows/deploy-streamlit.yml`，包括:

1. **代码质量检查**
   - 语法检查 (ruff)
   - 代码格式检查 (black)
   - 安全扫描 (bandit, safety)

2. **测试执行**
   - 单元测试 (pytest)
   - 覆盖率报告

3. **部署验证**
   - 配置文件验证
   - 依赖检查

## 🐛 故障排除

### 常见问题

**1. 导入错误**
```
ModuleNotFoundError: No module named 'xxx'
```
解决: 检查 `requirements.txt` 是否包含所有依赖

**2. 端口冲突**
```
Port 8501 is already in use
```
解决: 使用不同端口或停止占用进程

**3. 内存不足**
```
MemoryError
```
解决: 优化数据处理，使用流式处理

**4. 权限错误**
```
PermissionError: [Errno 13] Permission denied
```
解决: 检查文件权限和目录访问权限

### 调试工具

**本地调试:**
```bash
# 启用调试模式
export UI_DEBUG=true
uv run streamlit run app.py

# 查看详细日志
export UI_LOG_LEVEL=DEBUG
```

**容器调试:**
```bash
# 进入容器
docker exec -it container_name /bin/bash

# 查看容器日志
docker logs container_name
```

## 📞 支持

如果遇到部署问题，请:

1. 检查此文档的故障排除部分
2. 查看项目的GitHub Issues
3. 提交新的Issue并提供详细的错误信息

---

**注意**: 本指南假设你已经有基本的Git、Docker和云平台操作经验。如需更详细的步骤，请参考相应平台的官方文档。