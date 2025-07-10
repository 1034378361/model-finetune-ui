# 🚀 Model Finetune UI 部署指南

你的项目已成功推送到GitHub: https://github.com/1034378361/model-finetune-ui

## 📋 部署选项

### 🌟 Option 1: Streamlit Community Cloud (推荐 - 免费)

#### 立即部署步骤：

1. **访问 Streamlit Cloud**
   - 打开 https://share.streamlit.io/
   - 使用GitHub账号登录

2. **创建新应用**
   - 点击 "New app"
   - 选择 "From existing repo"
   - Repository: `1034378361/model-finetune-ui`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: 选择一个自定义域名（可选）

3. **配置环境变量**
   点击 "Advanced settings"，添加：
   ```
   ENCRYPTION_KEY = "your-32-character-encryption-key-here"
   UI_OUTPUT_DIR = "/tmp/ui_output"
   UI_DEBUG = "false"
   ```

4. **点击 "Deploy"**
   - 等待构建完成（约2-5分钟）
   - 获得公开访问URL

#### 优势：
- ✅ 完全免费
- ✅ 自动SSL证书
- ✅ GitHub集成
- ✅ 自动部署更新

---

### 🐳 Option 2: Docker 部署

#### 本地Docker测试：
```bash
# 1. 构建镜像
docker build -t model-finetune-ui .

# 2. 运行容器
docker run -p 8501:8501 \
  -e ENCRYPTION_KEY="your-32-character-key" \
  -e UI_OUTPUT_DIR="/app/output" \
  -v $(pwd)/ui_output:/app/output \
  model-finetune-ui

# 3. 访问应用
# http://localhost:8501
```

#### 云平台部署：

**Google Cloud Run:**
```bash
# 1. 设置项目
gcloud config set project YOUR_PROJECT_ID

# 2. 构建并推送
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/model-finetune-ui

# 3. 部署
gcloud run deploy model-finetune-ui \
  --image gcr.io/YOUR_PROJECT_ID/model-finetune-ui \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENCRYPTION_KEY=your-key
```

**AWS ECS/Fargate:**
```bash
# 1. 推送到ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URI
docker tag model-finetune-ui:latest YOUR_ECR_URI/model-finetune-ui:latest
docker push YOUR_ECR_URI/model-finetune-ui:latest

# 2. 创建ECS服务
aws ecs create-service --cluster your-cluster --service-name model-finetune-ui --task-definition your-task-def
```

---

### ☁️ Option 3: Heroku 部署

```bash
# 1. 安装Heroku CLI并登录
heroku login

# 2. 创建应用
heroku create your-unique-app-name

# 3. 设置环境变量
heroku config:set ENCRYPTION_KEY=your-32-character-key
heroku config:set UI_OUTPUT_DIR=/tmp/ui_output

# 4. 部署
git push heroku main

# 5. 打开应用
heroku open
```

---

### 🔧 Option 4: 自动化部署脚本

使用项目内置的部署脚本：

```bash
# Streamlit Cloud 准备
./scripts/deploy.sh streamlit

# Docker 部署
./scripts/deploy.sh docker

# Heroku 部署
ENCRYPTION_KEY=your-key ./scripts/deploy.sh heroku
```

---

## 🔑 重要：环境变量配置

**必须设置的环境变量：**

```bash
# 生成32字符的加密密钥
ENCRYPTION_KEY="abcdef1234567890abcdef1234567890"

# 可选配置
UI_OUTPUT_DIR="/tmp/ui_output"
UI_DEBUG="false"
UI_MAX_FILE_SIZE_MB="50"
UI_LOG_LEVEL="INFO"
```

**生成安全密钥：**
```bash
# 方法1：使用OpenSSL
openssl rand -hex 16

# 方法2：使用Python
python -c "import secrets; print(secrets.token_hex(16))"

# 方法3：在线生成
# 访问：https://www.random.org/strings/
```

---

## 📊 部署验证清单

部署完成后，请验证以下功能：

- [ ] **基础功能**
  - [ ] 应用能正常加载
  - [ ] 模型类型选择正常
  - [ ] 模板文件可以下载

- [ ] **文件处理**
  - [ ] CSV文件可以上传
  - [ ] 数据验证正常工作
  - [ ] 错误信息显示正确

- [ ] **数据处理**
  - [ ] Type 0模式处理正常
  - [ ] Type 1模式处理正常
  - [ ] 结果文件可以下载

- [ ] **性能测试**
  - [ ] 页面加载时间 < 10秒
  - [ ] 文件上传响应 < 30秒
  - [ ] 数据处理完成 < 60秒

---

## 🔄 CI/CD 自动化

你的项目已经配置了GitHub Actions，会自动执行：

1. **代码质量检查**
   - 语法检查 (ruff)
   - 代码格式检查 (black)
   - 类型检查 (mypy)

2. **安全扫描**
   - 依赖安全检查 (safety)
   - 代码安全扫描 (bandit)

3. **配置验证**
   - 必要文件检查
   - 依赖完整性验证

查看构建状态：https://github.com/1034378361/model-finetune-ui/actions

---

## 📱 快速访问链接

**项目地址：**
- GitHub仓库: https://github.com/1034378361/model-finetune-ui
- 部署文档: https://github.com/1034378361/model-finetune-ui/blob/main/DEPLOYMENT.md
- 问题报告: https://github.com/1034378361/model-finetune-ui/issues

**部署平台：**
- Streamlit Cloud: https://share.streamlit.io/
- Heroku Dashboard: https://dashboard.heroku.com/apps
- Google Cloud Console: https://console.cloud.google.com/

---

## 🆘 故障排除

### 常见问题：

**1. 环境变量未设置**
```
KeyError: 'ENCRYPTION_KEY'
```
**解决：** 在部署平台的环境变量设置中添加 `ENCRYPTION_KEY`

**2. 依赖安装失败**
```
ERROR: Could not find a version that satisfies...
```
**解决：** 检查 `requirements.txt` 文件，确保所有依赖版本正确

**3. 端口访问问题**
```
Port 8501 is not available
```
**解决：** 检查防火墙设置，或使用不同端口

**4. 文件权限错误**
```
PermissionError: [Errno 13] Permission denied
```
**解决：** 检查输出目录权限，使用 `/tmp` 目录

### 获取帮助：

1. **查看日志**
   - Streamlit Cloud: 在应用管理页面查看日志
   - Heroku: `heroku logs --tail`
   - Docker: `docker logs container_name`

2. **联系支持**
   - 在GitHub仓库提交Issue
   - 查看部署平台的官方文档
   - 参考项目的 `DEPLOYMENT_CHECKLIST.md`

---

## 🎉 恭喜！

你的Model Finetune UI项目已经成功推送到GitHub，现在可以选择任意一种部署方式来让全世界访问你的应用！

**推荐开始：** 从Streamlit Community Cloud开始，它是最简单且免费的选项。

---

**最后更新:** 2025年7月10日  
**项目版本:** v1.0.0