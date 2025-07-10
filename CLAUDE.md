# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

### 快速开始
```bash
# 初始环境设置（首次使用）
make setup

# 或者手动设置
./scripts/setup-uv.sh

# 快速启动（适合新用户）
make quickstart
```

### 环境设置
```bash
# 同步依赖
uv sync
# 或
make install

# 同步开发依赖
uv sync --dev
# 或
make install-dev
```

### 运行应用
```bash
# 推荐方式：使用项目脚本
uv run model-finetune-ui
# 或
make run

# 开发模式启动
make run-dev

# 传统方式：使用启动脚本
uv run python run.py

# 直接运行Streamlit
uv run streamlit run app.py --server.port 8501
```

### 开发工具
```bash
# 代码格式化
make format
# 或
uv run black .

# 代码检查
make lint
# 或  
uv run ruff check .

# 类型检查
make type-check
# 或
uv run mypy .

# 运行测试
make test
# 或
uv run pytest
```

### 生成示例数据
```bash
# 方式1：直接运行
uv run python examples/generate_sample_data.py

# 方式2：使用项目脚本
uv run generate-sample-data
```

### 依赖管理
```bash
# 添加依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 移除依赖
uv remove package-name
```

## 项目架构

### 核心组件
这是一个基于 Streamlit 的 Web 应用，用于模型微调和数据处理。主要有以下几个核心组件：

1. **主应用 (app.py)**
   - `ModelFinetuneApp` 类：主应用逻辑
   - 处理用户交互、文件上传、数据处理流程
   - 支持两种模型类型：Type 0 (微调) 和 Type 1 (完整建模)

2. **数据处理器 (core/processor.py)**
   - `ModelProcessor` 类：核心数据处理逻辑
   - 处理用户上传的系数文件 (w, a, b, A) 和 Range 数据
   - 计算 Range 系数并格式化结果

3. **数据验证器 (utils/validator.py)**
   - `DataValidator` 类：数据格式和一致性验证
   - 验证系数矩阵维度、数据类型、范围合理性
   - 生成详细的验证报告

4. **加密管理器 (utils/encryption.py)**
   - `EncryptionManager` 类：模型结果加密保存
   - 依赖主项目的加密模块进行数据加密

5. **文件处理器 (utils/file_handler.py)**
   - 文件上传、读取、格式转换等功能

6. **配置管理 (config.py)**
   - `UIConfig`：UI 界面配置、水质参数定义
   - `EnvironmentConfig`：环境变量配置
   - `ValidationConfig`：验证规则配置

### 数据流程
1. 用户选择模型类型 (Type 0 或 Type 1)
2. 上传相应的 CSV 文件
3. 数据验证器验证格式和一致性
4. 处理器转换数据格式并计算 Range 系数
5. 加密管理器保存加密的模型文件

### 模型类型
- **Type 0 (微调模式)**：仅需 A 系数和 Range 数据
- **Type 1 (完整建模模式)**：需要 w、a、b、A 系数和 Range 数据

### 水质参数
标准的 11 个水质参数：turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n

### 特征配置
25 个特征：STZ1 到 STZ25

## 依赖关系

### 包管理
项目使用 `uv` 进行包管理：
- 依赖定义在 `pyproject.toml` 中
- 使用 `uv.lock` 锁定确切版本
- 支持开发依赖分离

### 主项目依赖
项目依赖于外部的主项目模块：
- `model_finetune.utils.ConfigManager`：配置管理
- `autowaterqualitymodeler.utils.encryption`：数据加密

### 启动检查
`run.py` 会检查主项目模块是否可用，如果不可用会警告但允许继续运行

## 文件格式要求

### 系数文件 (w, a, b, A)
- 行索引：水质参数名称
- 列索引：特征编号 (STZ1-STZ25) 或 A 列
- 数据类型：浮点数

### Range 数据文件
- 列名：水质参数名称
- 数据：该参数的观测值，用于计算 min/max 范围

## 数据验证

### 自动验证项目
- 文件格式验证：CSV 格式、数据类型
- 维度验证：行列数量和索引名称
- 一致性验证：不同文件间的数据一致性
- 范围验证：数值合理性和异常值检查

### 验证阈值
- 最小样本数：2
- 最大零值比例：90%
- 最大空值比例：50%
- 系数值范围：-1000 到 1000
- A 系数范围：-10 到 10

## 输出结果

### 加密模型文件
- 保存在 `ui_output/ui_run_timestamp/models/` 目录
- 使用 AES 加密保存
- 包含处理后的系数数据和 Range 信息

### 备份文件
- 可选择创建未加密的 JSON 备份文件
- 用于调试和数据恢复

## 示例数据

使用 `examples/generate_sample_data.py` 生成测试数据：
- 生成符合格式要求的示例 CSV 文件
- 包含合理的水质参数范围
- 用于测试应用功能

## 开发工作流

### 初始化项目
```bash
# 克隆项目后首次运行
uv sync

# 生成示例数据
uv run generate-sample-data

# 启动应用
uv run model-finetune-ui
```

### 添加新功能
```bash
# 添加新依赖
uv add new-package

# 运行应用测试
uv run python run.py

# 如果是开发依赖
uv add --dev dev-package
```

### 项目构建
```bash
# 构建项目
uv build

# 安装为可编辑包
uv pip install -e .
```