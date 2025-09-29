# Model Finetune UI Project 🚀

## 📋 项目简介

基于Streamlit构建的Web UI项目，从主项目提取核心功能，提供友好的用户界面用于水质配置。支持用户自定义上传w、a、b、校准A、Range等因子文件，生成加密的配置结果。

## 🎯 核心功能

- **🔧 配置类型选择**：支持Type 0（快速配置模式）和Type 1（完整配置模式）
- **📁 文件上传管理**：直观的文件上传界面，支持CSV/Excel格式
- **✅ 数据验证**：完整的数据格式和一致性验证
- **🔒 安全加密**：使用与主项目相同的加密机制保存配置
- **📊 实时反馈**：处理进度和结果的实时显示
- **📋 详细报告**：生成验证报告和处理摘要

## 🛠️ 技术栈

- **前端框架**：Streamlit 1.28+
- **数据处理**：pandas, numpy
- **可视化**：matplotlib, seaborn, plotly
- **加密模块**：autowaterqualitymodeler 4.0.4+
- **文件处理**：支持CSV、Excel格式

## 📂 项目结构

```
ui-project/
├── README.md                 # 项目说明
├── requirements.txt          # 项目依赖
├── run.py                   # 启动脚本
├── app.py                   # 主应用文件
├── config.py                # 配置管理
├── core/                    # 核心逻辑
│   ├── __init__.py
│   └── processor.py         # 数据处理器
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── encryption.py        # 加密管理
│   ├── file_handler.py      # 文件处理
│   └── validator.py         # 数据验证
├── static/                  # 静态资源
│   └── style.css           # 样式文件
└── examples/                # 示例数据
    ├── generate_sample_data.py
    └── sample_data/         # 示例CSV文件
```

## 🚀 快速开始

### 1. 本地开发

#### 环境准备
```bash
# 进入项目目录
cd /path/to/create_bin
```

#### 安装依赖
```bash
# 使用uv安装依赖
uv sync

# 或安装开发依赖
uv sync --dev
```

#### 生成示例数据（可选）
```bash
# 生成测试用的示例数据
uv run generate-sample-data
```

#### 启动应用
```bash
# 方式1：使用启动脚本（推荐）
uv run python run.py

# 方式2：直接启动streamlit
uv run streamlit run app.py --server.port 8501

# 方式3：使用项目脚本
uv run model-finetune-ui
```

访问地址：http://localhost:8501

### 2. 部署到生产环境

我们提供了多种部署选项，详细说明请参考 **[DEPLOYMENT.md](DEPLOYMENT.md)**。

#### 🌟 快速部署到 Streamlit Cloud (推荐)
```bash
# 使用部署脚本
./scripts/deploy.sh streamlit
```

#### 🐳 Docker 部署
```bash
# 本地Docker部署
./scripts/deploy.sh docker

# 或手动部署
docker build -t model-finetune-ui .
docker run -p 8501:8501 -e ENCRYPTION_KEY=your-key model-finetune-ui
```

#### ☁️ Heroku 部署
```bash
# 设置环境变量并部署
ENCRYPTION_KEY=your-key ./scripts/deploy.sh heroku
```

### 3. 环境配置

在部署前，请确保配置以下环境变量：

- `ENCRYPTION_KEY`: 32字符的加密密钥（**必须设置**）
- `UI_OUTPUT_DIR`: 输出目录路径（可选，默认 ./ui_output）
- `UI_DEBUG`: 调试模式（可选，默认 false）

可以复制 `.env.example` 为 `.env` 并填入相应值：
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

### 4. 验证部署

无论使用哪种部署方式，都可以通过以下方式验证：

- 访问应用URL
- 检查模板下载功能
- 上传示例数据测试处理流程
- 查看输出文件是否正确生成

## 💻 使用指南

### 配置类型说明

- **Type 0 - 快速配置模式**：
  - 仅需要校准因子A和Range数据
  - 适用于现有配置的快速调整
  - 处理速度快

- **Type 1 - 完整配置模式**：
  - 需要影响因子w、影响因子a、调节因子b和Range数据
  - **校准因子A自动生成**（根据Range数据，全部设为1.0）
  - 适用于从头建立新配置
  - 功能完整

### 文件要求

#### 因子文件格式（w、a、b、校准A）
```csv
,STZ1,STZ2,STZ3,...,STZ25
turbidity,0.123,0.456,0.789,...,0.321
ss,0.234,0.567,0.890,...,0.432
sd,0.345,0.678,0.901,...,0.543
...
```

#### Range数据格式
```csv
turbidity,ss,sd,do,codmn,...
1.23,4.56,7.89,10.12,13.45,...
2.34,5.67,8.90,11.23,14.56,...
...
```

### 🆕 新功能特性

#### 模板文件下载
- **便捷操作**：在文件上传页面可直接下载对应的CSV模板文件
- **格式正确**：模板文件已包含正确的行列名称格式
- **按需提供**：根据选择的配置类型自动显示所需的模板文件
- **使用流程**：下载模板 → 填入数据 → 上传CSV文件

#### 改进的文件上传界面
- **明确标识**：文件上传按钮改为"📄 上传CSV文件"
- **模板下载**：每个文件类型旁边提供对应的模板下载按钮
- **类型说明**：根据配置类型动态显示文件要求

### 操作步骤

1. **选择配置类型**：在侧边栏选择Type 0或Type 1
2. **下载模板文件**：点击对应的模板下载按钮获取空白CSV模板
3. **填写数据**：在模板文件中填入您的数据
4. **上传CSV文件**：使用"📄 上传CSV文件"按钮上传填好的文件
5. **验证数据**：系统自动验证文件格式和数据一致性
6. **开始处理**：点击"🚀 开始处理"按钮
7. **查看结果**：处理完成后下载加密的配置文件

## 🔐 安全配置

### 加密配置

确保主项目的`.env`文件包含必要的加密配置：

```bash
# 加密密钥配置
WATER_QUALITY_ENCRYPTION_KEY=your_32_byte_hex_key
WATER_QUALITY_SALT=your_16_byte_hex_salt
WATER_QUALITY_IV=your_16_byte_hex_iv
```

### 数据安全

- 所有配置结果使用AES加密保存
- 临时文件在处理完成后自动清理
- 支持备份文件生成（未加密，用于调试）

## 📊 数据验证

### 自动验证项目

- **格式验证**：检查CSV格式、数据类型
- **维度验证**：验证行列数量和索引名称
- **一致性验证**：检查不同文件间的数据一致性
- **范围验证**：检查数值合理性和异常值

### 验证报告

系统会生成详细的验证报告，包括：
- 文件基本信息
- 数据质量评估
- 警告和错误信息
- 处理建议

## 🤝 与主项目的关系

### 独立性设计
- **不修改主项目**：完全独立运行，不影响原项目
- **复用核心逻辑**：引用主项目的加密和配置模块
- **共享配置文件**：使用相同的`.env`配置

### 模块复用
```python
# 复用主项目模块
from model_finetune.utils import ConfigManager
from autowaterqualitymodeler.utils.encryption import encrypt_data_to_file
```

## 🔧 配置选项

### 环境变量
```bash
UI_OUTPUT_DIR=./ui_output          # 输出目录
UI_DEBUG=false                     # 调试模式
UI_MAX_FILE_SIZE_MB=50            # 最大文件大小
UI_LOG_LEVEL=INFO                 # 日志级别
```

### 配置文件
参见`config.py`中的详细配置选项。

## 🐛 故障排除

### 常见问题

1. **模块导入错误**
   ```bash
   # 确保主项目路径正确
   export PYTHONPATH=/path/to/model-finetune/src:$PYTHONPATH
   ```

2. **加密配置错误**
   ```bash
   # 检查.env文件是否存在且配置正确
   cat ../.env
   ```

3. **依赖包缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

### 日志调试

启用调试模式查看详细日志：
```bash
export UI_DEBUG=true
python run.py
```

## 📈 未来计划

### 短期目标
- [ ] 添加数据可视化功能
- [ ] 支持批量文件处理
- [ ] 添加处理历史记录
- [ ] 优化界面响应速度

### 长期目标
- [ ] 支持更多文件格式（JSON、Parquet）
- [ ] 添加配置性能分析
- [ ] 集成云端存储支持
- [ ] 开发API接口

## 📞 技术支持

- **主项目文档**：参见`../CLAUDE.md`
- **问题反馈**：在主项目仓库提交Issue
- **技术讨论**：联系项目维护者

---

**开发者**：基于model-finetune v1.0.4  
**最后更新**：2025年7月9日