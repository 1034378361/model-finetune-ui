# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

### 环境设置
```bash
# 同步依赖
uv sync

# 同步开发依赖
uv sync --dev
```

### 运行应用
```bash
# 推荐方式：使用项目脚本
uv run model-finetune-ui

# 使用启动脚本
uv run python run.py

# 直接运行Streamlit（新结构）
uv run streamlit run src/model_finetune_ui/app.py --server.port 8501
```

### 开发工具
```bash
# 代码格式化
uv run black .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy .

# 运行测试
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

### 项目概述
这是一个名为 **Model Finetune UI** 的基于 Streamlit 的 Web 应用，专门用于水质模型微调和数据处理。项目采用现代 Python 开发实践，使用 `uv` 包管理器，支持从 CSV 数据到加密模型文件的完整工作流程。

### 核心组件
主要有以下几个核心组件：

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

5. **解密管理器 (utils/decryption.py)** 🆕
   - `DecryptionManager` 类：BIN文件解密和参数提取
   - 支持Type 0和Type 1模型解密
   - 完整的数据验证和错误处理
   - 自动生成对应的CSV格式文件

6. **文件处理器 (utils/file_handler.py)**
   - 文件上传、读取、格式转换等功能

7. **配置管理 (config.py)**
   - `UIConfig`：UI 界面配置、水质参数定义
   - `EnvironmentConfig`：环境变量配置
   - `ValidationConfig`：验证规则配置

### 应用模式
项目支持两种工作模式：

**📦 加密模式 (CSV→BIN)**：
1. 用户选择模型类型 (Type 0 或 Type 1)
2. 上传相应的 CSV 文件
3. 数据验证器验证格式和一致性
4. 处理器转换数据格式并计算 Range 系数
5. 加密管理器保存加密的模型文件

**🔓 解密模式 (BIN→CSV)**：
1. 用户上传加密的 BIN 文件
2. 解密管理器解密并验证文件内容
3. 参数解析器将数据重构为原始格式
4. 生成对应的 CSV 文件供用户下载
5. 支持批量下载所有解析出的 CSV 文件

### 模型类型
- **Type 0 (微调模式)**：仅需 A 系数和 Range 数据
- **Type 1 (完整建模模式)**：需要 w、a、b、A 系数和 Range 数据

### 水质参数
标准的 11 个水质参数：turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n

### 特征配置
26 个特征：STZ1 到 STZ26

## 依赖关系

### 包管理系统
项目使用现代 Python 包管理器 `uv`：
- **主配置文件**: `pyproject.toml` - 包含项目元数据、依赖、构建配置
- **锁定文件**: `uv.lock` - 确保跨环境依赖版本一致性
- **云部署**: `requirements.txt` - Streamlit Cloud 专用的精简依赖
- **开发/生产分离**: 支持开发依赖分离管理

### 核心依赖
- **Web 框架**: Streamlit >= 1.28.0
- **数据处理**: pandas >= 2.0.0, numpy >= 1.24.0  
- **可视化**: matplotlib, seaborn, plotly
- **加密**: cryptography >= 41.0.0
- **UI 增强**: streamlit-option-menu, streamlit-aggrid

### 外部项目依赖
项目依赖于外部的主项目模块：
- `model_finetune.utils.ConfigManager`：配置管理
- `autowaterqualitymodeler.utils.encryption`：数据加密
- **容错机制**: `run.py` 会检查主项目模块可用性，不可用时警告但允许继续运行

## 文件格式要求

### 系数文件 (w, a, b, A)
- 行索引：水质参数名称
- 列索引：特征编号 (STZ1-STZ26) 或 A 列
- 数据类型：浮点数

### Range 数据文件
- 列名：水质参数名称
- 数据：该参数的观测值，用于计算 min/max 范围

## 数据验证

### 加密模式验证
- 文件格式验证：CSV 格式、数据类型
- 维度验证：行列数量和索引名称
- 一致性验证：不同文件间的数据一致性
- 范围验证：数值合理性和异常值检查

### 解密模式验证 🆕
- **文件路径验证**：文件存在性、大小限制（<100MB）、扩展名检查
- **数据结构验证**：JSON格式、必需字段检查、类型验证
- **模型类型验证**：支持Type 0/1，字段完整性验证
- **数值验证**：系数合理性检查、NaN值检测、min/max关系验证
- **维度验证**：数组长度匹配预期维度

### 验证阈值
- 最小样本数：2
- 最大零值比例：90%
- 最大空值比例：50%
- 系数值范围：-1000 到 1000
- A 系数范围：-10 到 10
- **解密文件大小限制**：100MB
- **系数合理性阈值**：绝对值 ≤ 1000

## 输出结果

### 加密模式输出
**加密模型文件**：
- 保存在 `ui_output/ui_run_timestamp/models/` 目录
- 使用 AES 加密保存
- 包含处理后的系数数据和 Range 信息

**备份文件**：
- 可选择创建未加密的 JSON 备份文件
- 用于调试和数据恢复

### 解密模式输出 🆕
**CSV参数文件**：
- **Type 0 模式**：生成 `A_coefficients.csv` 和 `range_data.csv`
- **Type 1 模式**：生成 `w_coefficients.csv`、`a_coefficients.csv`、`b_coefficients.csv`、`A_coefficients.csv`、`range_data.csv`
- 所有文件使用标准水质参数和特征站点作为索引
- 支持单文件下载和批量ZIP打包下载

**文件格式**：
- 标准CSV格式，UTF-8编码
- 行索引：水质参数或特征站点名称
- 列索引：对应的参数或特征编号
- Range数据包含min/max列

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

## 重要说明

### 测试框架
✅ **已完成**: 项目已建立完整的测试框架：
- 单元测试：`tests/unit/` - 测试各个模块功能
- 集成测试：`tests/integration/` - 测试完整工作流
- 测试数据：`tests/fixtures/` 和 `tests/data/` - 测试用的fixtures和数据
- 运行测试：`uv run pytest` - 执行所有测试
- 测试覆盖率：`uv run pytest --cov` - 查看代码覆盖率

### 部署配置
- **本地开发**: 使用 `pyproject.toml` 和 `uv` 进行完整依赖管理
- **Streamlit Cloud**: 使用 `requirements.txt` 进行简化部署
- **包文件**: `packages.txt` 用于系统级包依赖

### 项目脚本
在 `pyproject.toml` 中定义了两个可执行脚本：
- `model-finetune-ui`: 启动主应用
- `generate-sample-data`: 生成示例数据

## Git分支策略

### 分支结构
- **main**: 主分支，稳定发布版本
- **dev**: 开发分支，集成最新开发成果
- **feature/功能名**: 功能开发分支
- **fix/问题描述**: 问题修复分支
- **refactor/重构描述**: 代码重构分支

### 开发流程
```bash
# 1. 从main创建功能分支
git checkout main
git pull origin main
git checkout -b feature/new-feature

# 2. 开发完成后推送到远程
git push -u origin feature/new-feature

# 3. 创建Pull Request合并到dev分支

# 4. dev分支测试完成后合并到main分支
```

### 分支保护策略
- main分支受保护，禁止直接推送
- 所有修改必须通过Pull Request
- 合并前必须通过代码检查和测试
- 要求至少一次代码审查

### 提交规范
使用语义化提交信息：
- `feat:` - 新功能
- `fix:` - 问题修复
- `docs:` - 文档更新
- `style:` - 代码格式化
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建工具、依赖更新等