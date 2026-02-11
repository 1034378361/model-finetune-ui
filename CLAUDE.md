# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

```bash
# 环境设置
uv sync              # 同步依赖
uv sync --dev        # 含开发依赖

# 运行应用
uv run model-finetune-ui                                          # 推荐
uv run streamlit run src/model_finetune_ui/app.py --server.port 8501  # 直接运行

# 开发工具
uv run ruff check .         # 代码检查
uv run ruff check . --fix   # 自动修复
uv run black .              # 格式化（skip-string-normalization = true）
uv run mypy .               # 类型检查

# 测试
uv run pytest                                                      # 全部测试
uv run pytest tests/unit/test_validator.py                         # 单文件
uv run pytest tests/unit/test_validator.py::test_validate_coefficients_data  # 单测试
uv run pytest --cov                                                # 覆盖率

# 生成示例数据
uv run generate-sample-data
```

## 项目架构

Streamlit Web应用，用于水质模型系数的加密打包（CSV→BIN）和解密还原（BIN→CSV）。

### 源码结构 (`src/model_finetune_ui/`)

- **app.py** — `ModelFinetuneApp`：Streamlit主应用，管理双模式UI（加密/解密）、文件上传、进度展示、侧边栏日志面板
- **config.py** — 三个配置类：`UIConfig`（水质参数、特征站点、模型类型定义）、`EnvironmentConfig`（环境变量）、`ValidationConfig`（验证阈值）
- **core/processor.py** — `ModelProcessor`：系数数据处理、Range计算、格式化
- **utils/encryption.py** — `EncryptionManager`（高层）+ `LowLevelEncryptionManager`（底层AES）+ `encrypt_data_to_file()`（兼容函数接口）
- **utils/decryption.py** — `DecryptionManager`：BIN解密、格式自动检测、维度推断、CSV生成
- **utils/validator.py** — `DataValidator`：系数维度/类型/范围/一致性验证
- **utils/file_handler.py** — 文件上传读取和格式转换
- **utils/template_generator.py** — CSV模板生成（内存中，返回bytes）
- **utils/logger.py** — `StreamlitLogHandler`：内存日志存储，支持级别过滤和HTML渲染
- **utils/utils.py** — `ConfigManager`、`EnhancedLogger`、`performance_monitor`装饰器

### 入口系统

项目有多个入口点（历史原因）：
- `pyproject.toml` 中 `model-finetune-ui` 脚本 → `src/model_finetune_ui/run.py:main()` — **推荐**
- 根目录 `run.py` — 旧入口，含环境检查和模块可用性验证
- 根目录 `app.py` — 直接Streamlit入口（遗留）

## 核心领域知识

### 模型类型

| 类型 | 名称 | 必需系数 | 系数维度 |
|------|------|----------|----------|
| Type 0 | 微调模式 | A, Range | A: [11], Range: [22] |
| Type 1 | 完整建模 | w, a, b, A, Range | w/a: [26×11扁平], b: [11×26扁平], A: [11], Range: [22] |

- **11个水质参数**（固定）：turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n
- **26个特征站点**（默认，可动态调整）：STZ1 ~ STZ26

### BIN文件格式与加密

项目支持两种加密格式，解密时自动检测：

**AES加密（标准模式）**：
- 算法：AES-256-CBC + PKCS7填充 + PBKDF2HMAC密钥派生
- 文件格式：`[IV 16字节][加密数据]` — 兼容C++端解密
- 配置来源：`ConfigManager.get_encryption_config()` → 环境变量或默认值
- 默认密钥参数：password=`water_quality_analysis_key`, salt=`water_quality_salt`, iv=`fixed_iv_16bytes`, iterations=100000

**hex_reverse加密（大华兼容模式）**：
- 算法：JSON → UTF-8 → hex编码 → 字符串倒序 → 写入文件
- 用途：大华预警器系统兼容
- 格式检测：检查前64字节是否全为十六进制字符

### 维度推断机制

解密时通过 `_infer_dimensions()` 自适应推断维度：
1. A数组长度 → 确定指标数（param_count）
2. w或a数组长度 ÷ 指标数 → 确定特征数（feature_count）
3. Type 0模型无w/a/b，feature_count为None
4. 若指标数≠11，自动生成 `param_1` ~ `param_N` 命名

### 数据流

```
加密: CSV上传 → FileHandler → DataValidator → ModelProcessor → EncryptionManager → BIN文件
解密: BIN上传 → DecryptionManager.decrypt_bin_file() → parse_to_csv_format() → generate_csv_files() → CSV bytes
```

## 外部依赖

项目可选依赖 `autowaterqualitymodeler.utils.encryption`（主项目加密模块）。本项目已内置完整的加密/解密实现（`LowLevelEncryptionManager`），外部模块仅作为解密失败时的后备。应用在模块不可用时会降级运行。

## 代码风格

- Python 3.10+，line-length 88
- Ruff（lint）+ Black（format，skip-string-normalization）
- MyPy严格模式（disallow_untyped_defs）
- 中文注释和日志消息
- 语义化提交：`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`

## Git分支策略

- **main**：受保护，禁止直接推送，需PR + 代码审查
- **dev**：开发集成分支
- **feature/**, **fix/**, **refactor/**：功能/修复/重构分支
- 流程：feature → PR → dev → 测试通过 → PR → main

## 测试

- `tests/conftest.py`：共享fixtures（temp_dir, sample_water_params, sample_coefficient_data等）
- `tests/unit/`：各模块单元测试
- `tests/integration/`：完整加密→解密往返测试
- pytest配置：`--strict-markers --strict-config`，pythonpath=["."]

## 部署

- **本地开发**：`uv` + `pyproject.toml`
- **Streamlit Cloud**：`requirements.txt`（精简依赖）+ `packages.txt`（系统包）
- **CI/CD**：`.github/workflows/deploy-streamlit.yml`
