# Changelog

所有值得注意的项目更改都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2025-09-25

### Added
- 🚀 基础的Model Finetune UI应用
- 📊 支持两种模型类型：Type 0（微调模式）和Type 1（完整建模模式）
- 🌊 支持11种标准水质参数：turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n
- 🎯 支持26个特征站点：STZ1-STZ26（升级支持STZ26特征）
- 📁 文件上传和处理功能（支持CSV格式）
- 🔐 模型结果加密保存功能
- 📋 数据验证和格式检查
- 📥 CSV模板文件生成和下载
- 🎨 基于Streamlit的用户友好界面
- ⚙️ 完整的配置管理系统
- 📚 详细的项目文档（README.md, CLAUDE.md）

### Features
- **Type 0 模式**：微调模式，使用A系数进行模型微调
- **Type 1 模式**：完整建模模式，使用w、a、b、A全套系数
- **模板默认值**：所有模板默认值设置为0（优化用户体验）
- **数据处理器**：核心的ModelProcessor类处理用户数据
- **数据验证器**：DataValidator类确保数据格式正确性
- **加密管理器**：EncryptionManager类安全保存模型结果
- **文件处理器**：FileHandler类处理文件上传和读取
- **模板生成器**：TemplateGenerator类生成标准CSV模板

### Technical
- 🏗️ 标准Python包结构（src/layout）
- 🧪 完整的测试框架（pytest, >80%覆盖率目标）
- 🔧 现代开发工具链：uv包管理器，ruff代码检查，black格式化，mypy类型检查
- 📦 现代pyproject.toml配置
- 🚀 多种启动方式：uv run, streamlit run, python run.py
- 🌐 Streamlit Cloud部署支持

### Dependencies
- streamlit >= 1.28.0 - Web应用框架
- pandas >= 2.0.0 - 数据处理
- numpy >= 1.24.0 - 数值计算
- matplotlib >= 3.7.0 - 数据可视化
- seaborn >= 0.12.0 - 统计可视化
- plotly >= 5.15.0 - 交互式图表
- cryptography >= 41.0.0 - 加密功能
- autowaterqualitymodeler >= 4.0.5 - 核心水质建模库

## [Unreleased]

### Planned
- 🔄 Git分支策略实施
- 📖 Google/NumPy风格docstring标准化
- 🧪 测试覆盖率提升至>80%
- 📈 性能优化和监控
- 🌍 国际化支持
- 📱 响应式UI改进