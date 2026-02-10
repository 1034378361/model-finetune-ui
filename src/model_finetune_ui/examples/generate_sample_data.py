#!/usr/bin/env python
"""
生成示例数据文件

用于测试UI项目的功能
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.model_finetune_ui.utils.config_manager import ConfigurationManager


def generate_sample_data():
    """生成示例数据文件"""

    # 创建示例数据目录
    examples_dir = Path(__file__).parent
    sample_data_dir = examples_dir / "sample_data"
    sample_data_dir.mkdir(exist_ok=True)

    # 从配置管理器获取参数
    config_manager = ConfigurationManager()
    water_params = config_manager.get_water_params()
    stations = config_manager.get_feature_stations()

    print("🔧 生成示例数据文件...")

    # 1. 生成w权重系数矩阵 (特征 × 水质参数)
    print("生成w权重系数矩阵...")
    w_data = pd.DataFrame(0.0, index=stations, columns=water_params)  # 默认值设置为0
    w_data.to_csv(sample_data_dir / "w_coefficients.csv")

    # 2. 生成a权重系数矩阵 (特征 × 水质参数)
    print("生成a权重系数矩阵...")
    a_data = pd.DataFrame(0.0, index=stations, columns=water_params)  # 默认值设置为0
    a_data.to_csv(sample_data_dir / "a_coefficients.csv")

    # 3. 生成b幂系数矩阵 (水质参数 × 特征)
    print("生成b幂系数矩阵...")
    b_data = pd.DataFrame(0.0, index=water_params, columns=stations)  # 默认值设置为0
    b_data.to_csv(sample_data_dir / "b_coefficients.csv")

    # 4. 生成A微调系数（仅用于Type 0模式）
    print("生成A微调系数...")
    A_data = pd.DataFrame(0.0, index=water_params, columns=["A"])  # 默认值设置为0
    A_data.to_csv(sample_data_dir / "A_coefficients.csv")

    # 5. 生成Range数据
    print("生成Range数据...")
    print("注意：Type 1模式将根据Range数据自动生成A微调系数（全部设为1.0）")
    np.random.seed(42)  # 设置随机种子以获得可重复的结果

    # 为每个水质参数生成合理的观测值范围
    range_data = {}

    # 定义各参数的合理范围
    param_ranges = {
        "turbidity": (0.5, 50),  # 浊度 NTU
        "ss": (1, 100),  # 悬浮物 mg/L
        "sd": (0.1, 5.0),  # 透明度 m
        "do": (4, 12),  # 溶解氧 mg/L
        "codmn": (1, 15),  # 高锰酸盐指数 mg/L
        "codcr": (5, 40),  # 化学需氧量 mg/L
        "chla": (0.1, 20),  # 叶绿素a μg/L
        "tn": (0.1, 5.0),  # 总氮 mg/L
        "tp": (0.01, 0.5),  # 总磷 mg/L
        "chroma": (5, 50),  # 色度 度
        "nh3n": (0.01, 2.0),  # 氨氮 mg/L
    }

    n_samples = 100  # 生成100个样本

    for param in water_params:
        min_val, max_val = param_ranges.get(param, (0, 10))
        # 使用对数正态分布生成更真实的水质数据
        mean = np.log((min_val + max_val) / 2)
        std = 0.5
        values = np.random.lognormal(mean, std, n_samples)

        # 限制在合理范围内
        values = np.clip(values, min_val, max_val)
        range_data[param] = values

    range_df = pd.DataFrame(range_data)
    range_df.to_csv(sample_data_dir / "range_data.csv", index=False)

    print(f"✅ 示例数据已生成到: {sample_data_dir}")
    print("\n文件列表:")
    for file in sample_data_dir.glob("*.csv"):
        size = file.stat().st_size
        print(f"  - {file.name} ({size} bytes)")

    # 生成数据说明文件
    generate_data_description(sample_data_dir)

    return sample_data_dir


def generate_data_description(data_dir: Path):
    """生成数据说明文件"""

    description = """# 示例数据说明

## 文件列表

### 1. w_coefficients.csv
- **描述**: w权重系数矩阵
- **维度**: 11行（水质参数）× 26列（特征）
- **数据类型**: 浮点数
- **用途**: Type 1完整建模模式使用

### 2. a_coefficients.csv
- **描述**: a权重系数矩阵
- **维度**: 11行（水质参数）× 26列（特征）
- **数据类型**: 浮点数
- **用途**: Type 1完整建模模式使用

### 3. b_coefficients.csv
- **描述**: b幂系数矩阵
- **维度**: 11行（水质参数）× 26列（特征）
- **数据类型**: 浮点数
- **用途**: Type 1完整建模模式使用

### 4. A_coefficients.csv
- **描述**: A微调系数矩阵
- **维度**: 11行（水质参数）× 1列（A）
- **数据类型**: 浮点数
- **用途**: **仅Type 0微调模式需要上传**，Type 1模式将自动生成（全部设为1.0）

### 5. range_data.csv
- **描述**: 范围数据，包含各水质参数的观测值
- **维度**: 100行（样本）× 11列（水质参数）
- **数据类型**: 浮点数
- **用途**: 用于计算各参数的min/max范围

## 水质参数说明

| 参数名 | 中文名 | 单位 | 典型范围 |
|-------|--------|------|----------|
| turbidity | 浊度 | NTU | 0.5-50 |
| ss | 悬浮物 | mg/L | 1-100 |
| sd | 透明度 | m | 0.1-5.0 |
| do | 溶解氧 | mg/L | 4-12 |
| codmn | 高锰酸盐指数 | mg/L | 1-15 |
| codcr | 化学需氧量 | mg/L | 5-40 |
| chla | 叶绿素a | μg/L | 0.1-20 |
| tn | 总氮 | mg/L | 0.1-5.0 |
| tp | 总磷 | mg/L | 0.01-0.5 |
| chroma | 色度 | 度 | 5-50 |
| nh3n | 氨氮 | mg/L | 0.01-2.0 |

## 特征说明

特征编号: STZ1 到 STZ26，共26个特征

## 使用方法

1. **Type 0 (微调模式)**:
   - 上传: A_coefficients.csv, range_data.csv

2. **Type 1 (完整建模模式)**:
   - 上传: w_coefficients.csv, a_coefficients.csv, b_coefficients.csv, range_data.csv
   - **注意**: A微调系数将根据Range数据自动生成，无需上传

## 注意事项

- 所有系数文件的行索引必须是水质参数名称
- w、a、b系数文件的列索引必须是特征编号（STZ1-STZ26）
- A微调系数文件的列索引必须是A列（仅Type 0模式需要）
- Range数据文件的列名必须是水质参数名称
- 数据类型必须是数值型（浮点数）
- **重要**：Type 1模式的A微调系数会自动生成，无需手动上传
"""

    with open(data_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(description)

    print("✅ 数据说明文件已生成")


def main():
    """主函数，供pyproject.toml脚本调用"""
    generate_sample_data()


if __name__ == "__main__":
    main()
