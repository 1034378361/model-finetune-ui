#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例数据生成器

生成用于测试UI项目的示例CSV文件
"""

import pandas as pd
import numpy as np
from pathlib import Path

def generate_sample_data():
    """生成示例数据文件"""
    
    # 创建示例数据目录
    examples_dir = Path(__file__).parent
    examples_dir.mkdir(exist_ok=True)
    
    # 水质参数
    water_params = [
        "turbidity", "ss", "sd", "do", "codmn", 
        "codcr", "chla", "tn", "tp", "chroma", "nh3n"
    ]
    
    # 特征
    stations = [f"STZ{i}" for i in range(1, 26)]
    
    print("🎯 生成示例数据文件...")
    
    # 1. 生成W系数矩阵
    np.random.seed(42)
    w_data = np.random.uniform(-0.1, 0.1, size=(len(water_params), len(stations)))
    w_df = pd.DataFrame(w_data, index=water_params, columns=stations)
    w_df.to_csv(examples_dir / "sample_w_coefficients.csv")
    print(f"✅ W系数文件: {w_df.shape}")
    
    # 2. 生成A系数矩阵  
    a_data = np.random.uniform(-0.05, 0.05, size=(len(water_params), len(stations)))
    a_df = pd.DataFrame(a_data, index=water_params, columns=stations)
    a_df.to_csv(examples_dir / "sample_a_coefficients.csv")
    print(f"✅ A系数文件: {a_df.shape}")
    
    # 3. 生成B系数矩阵
    b_data = np.random.uniform(-0.02, 0.02, size=(len(water_params), len(stations)))
    b_df = pd.DataFrame(b_data, index=water_params, columns=stations)
    b_df.to_csv(examples_dir / "sample_b_coefficients.csv")
    print(f"✅ B系数文件: {b_df.shape}")
    
    # 4. 生成A增强系数
    A_data = np.random.uniform(0.8, 1.2, size=(len(water_params), 1))
    A_df = pd.DataFrame(A_data, index=water_params, columns=["A"])
    A_df.to_csv(examples_dir / "sample_A_coefficients.csv")
    print(f"✅ A增强系数文件: {A_df.shape}")
    
    # 5. 生成Range数据（模拟观测数据）
    np.random.seed(123)
    n_samples = 100
    
    # 为每个水质参数生成不同范围的随机数据
    range_data = {}
    param_ranges = {
        "turbidity": (0, 50),
        "ss": (0, 100),
        "sd": (0.5, 3.0),
        "do": (5, 15),
        "codmn": (1, 10),
        "codcr": (5, 30),
        "chla": (0, 100),
        "tn": (0.1, 5.0),
        "tp": (0.01, 0.5),
        "chroma": (5, 50),
        "nh3n": (0.01, 2.0)
    }
    
    for param in water_params:
        min_val, max_val = param_ranges[param]
        # 生成正态分布数据
        mean = (min_val + max_val) / 2
        std = (max_val - min_val) / 6
        data = np.random.normal(mean, std, n_samples)
        # 确保数据在合理范围内
        data = np.clip(data, min_val, max_val)
        range_data[param] = data
    
    range_df = pd.DataFrame(range_data)
    range_df.to_csv(examples_dir / "sample_range_data.csv", index=False)
    print(f"✅ Range数据文件: {range_df.shape}")
    
    # 6. 生成说明文件
    readme_content = """# 示例数据文件说明

## 文件列表

### Type 1 (完整建模模式) 需要的文件：
- `sample_w_coefficients.csv`: W系数矩阵 (11×25)
- `sample_a_coefficients.csv`: A系数矩阵 (11×25) 
- `sample_b_coefficients.csv`: B系数矩阵 (11×25)
- `sample_A_coefficients.csv`: A增强系数 (11×1)
- `sample_range_data.csv`: Range参考数据 (100×11)

### Type 0 (微调模式) 需要的文件：
- `sample_A_coefficients.csv`: A增强系数 (11×1)
- `sample_range_data.csv`: Range参考数据 (100×11)

## 数据说明

### 水质参数 (11个)
- turbidity: 浊度
- ss: 悬浮物
- sd: 透明度  
- do: 溶解氧
- codmn: 高锰酸盐指数
- codcr: 化学需氧量
- chla: 叶绿素a
- tn: 总氮
- tp: 总磷
- chroma: 色度
- nh3n: 氨氮

### 特征 (25个)
- STZ1 到 STZ25

### 使用方法
1. 启动UI应用：`python run.py`
2. 选择模型类型
3. 上传对应的CSV文件
4. 点击处理按钮
5. 下载生成的加密模型文件
"""
    
    with open(examples_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ 说明文件已生成")
    print(f"\n📁 示例文件保存在: {examples_dir}")
    print("\n🚀 现在可以使用这些文件测试UI应用了！")

if __name__ == "__main__":
    generate_sample_data()