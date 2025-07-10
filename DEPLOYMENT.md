# Streamlit Cloud部署指南

## 🚀 部署选项

### 选项1：使用简化版本（推荐）
1. 在Streamlit Cloud中设置主文件为：`streamlit_app.py`
2. 使用 `requirements-minimal.txt` 作为依赖文件
3. 不使用 `packages.txt`

### 选项2：使用最小测试版本
1. 在Streamlit Cloud中设置主文件为：`app_minimal.py`
2. 使用 `requirements-minimal.txt` 作为依赖文件
3. 不使用 `packages.txt`

### 选项3：完整版本（如果选项1/2成功）
1. 在Streamlit Cloud中设置主文件为：`app.py`
2. 使用 `requirements.txt` 作为依赖文件
3. 使用 `packages.txt`：只包含 `curl`

## 🔧 部署步骤

### 第一步：测试最简版本
1. 先尝试部署 `streamlit_app.py` + `requirements-minimal.txt`
2. 如果成功，说明基础环境正常

### 第二步：逐步添加功能
1. 如果步骤1成功，可以尝试添加更多依赖
2. 逐个添加：`openpyxl`, `cryptography`, `python-dotenv`, `chardet`

### 第三步：完整功能测试
1. 最后尝试完整的 `app.py` 版本
2. 确保所有功能正常工作

## 🛠️ 文件配置

### streamlit_app.py
- 完全独立的应用，不依赖utils模块
- 内置所有必要功能
- 简化的数据处理逻辑
- 无需加密功能

### requirements-minimal.txt
```
streamlit
pandas
numpy
```

### .streamlit/config.toml
```toml
[server]
headless = true
port = 8501
address = "0.0.0.0"
enableCORS = false
```

## 📋 故障排除

### 常见错误1：packages.txt格式错误
**错误信息**: `E: Unable to locate package #`
**解决方案**: 确保packages.txt不包含注释，只包含一行：`curl`

### 常见错误2：健康检查失败
**错误信息**: `connect: connection refused`
**解决方案**: 确保.streamlit/config.toml配置正确

### 常见错误3：依赖安装失败
**错误信息**: `Error installing requirements`
**解决方案**: 使用更简单的requirements-minimal.txt

## 🎯 推荐部署流程

1. **第一次部署**：使用`streamlit_app.py` + `requirements-minimal.txt`
2. **测试功能**：上传文件，生成模板，处理数据
3. **验证成功**：确认所有核心功能正常工作
4. **可选升级**：如果需要加密功能，再尝试完整版本

## 🔐 环境变量配置

如果使用完整版本，需要在Streamlit Cloud中配置：
- `ENCRYPTION_KEY`: 32字节的加密密钥（可选）

## 📞 支持

如果遇到部署问题：
1. 查看Streamlit Cloud的错误日志
2. 尝试更简单的配置
3. 检查GitHub仓库的文件是否正确推送