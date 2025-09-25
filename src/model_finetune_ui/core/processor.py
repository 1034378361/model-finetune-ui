#!/usr/bin/env python
"""
模型数据处理器

基于原项目的_format_result函数逻辑，处理用户上传的CSV文件
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ModelProcessor:
    """模型数据处理器，处理用户上传的CSV数据并格式化为模型所需格式。

    基于原项目的_format_result函数逻辑，支持Type 0（微调模式）和Type 1（完整建模模式）
    两种模型类型的数据处理。处理包括系数矩阵转换、Range系数计算等功能。
    """

    def __init__(self):
        # 默认的水质参数索引
        self.default_water_quality_params = [
            "turbidity",
            "ss",
            "sd",
            "do",
            "codmn",
            "codcr",
            "chla",
            "tn",
            "tp",
            "chroma",
            "nh3n",
        ]

        # 默认的特征列名
        self.default_feature_stations = [f"STZ{i}" for i in range(1, 27)]

    def process_user_data(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> dict[str, Any] | None:
        """
        处理用户上传的数据

        Args:
            processed_data: 包含各类数据的字典
            model_type: 模型类型，0或1

        Returns:
            格式化的结果字典
        """
        try:
            logger.info(f"开始处理用户数据，模型类型: {model_type}")

            # 验证model_type
            if model_type not in [0, 1]:
                raise ValueError("model_type 必须是 0 或 1")

            # 获取数据
            range_data = processed_data.get("Range")
            if range_data is None:
                raise ValueError("缺少Range数据")

            # 构建结果字典
            format_result = {"type": model_type}

            # 处理不同类型的数据
            if model_type == 1:
                # 完整建模模式，需要w、a、b系数，A系数自动生成
                w_data = processed_data.get("w")
                a_data = processed_data.get("a")
                b_data = processed_data.get("b")

                if any(data is None for data in [w_data, a_data, b_data]):
                    raise ValueError("Type 1模式需要w、a、b三个系数文件")

                # 转换为扁平化列表
                format_result["w"] = w_data.values.flatten().tolist()
                format_result["a"] = a_data.values.flatten().tolist()
                format_result["b"] = b_data.values.flatten().tolist()

                # 自动生成A系数：根据Range数据的水质参数索引创建全1矩阵
                A_coefficients = pd.DataFrame(
                    1.0,  # 全部填充为1
                    index=b_data.index,
                    columns=["A"],
                )
                format_result["A"] = A_coefficients.values.flatten().tolist()

                logger.info(
                    f"为Type 1模式自动生成A微调系数，共{len(b_data)}个参数，全部设为1.0"
                )

            elif model_type == 0:
                # 微调模式，只需要A系数
                A_data = processed_data.get("A")
                if A_data is None:
                    raise ValueError("Type 0模式需要A系数文件")

                format_result["A"] = A_data.values.flatten().tolist()

            format_result["Range"] = range_data.values.flatten().tolist()

            logger.info("数据处理完成")
            return format_result

        except Exception as e:
            logger.error(f"处理用户数据时发生错误: {str(e)}")
            return None

    def validate_data_dimensions(
        self, data: pd.DataFrame, expected_shape: tuple = None
    ) -> bool:
        """
        验证数据维度

        Args:
            data: 要验证的DataFrame
            expected_shape: 期望的形状（行数，列数）

        Returns:
            验证结果
        """
        try:
            if expected_shape:
                if data.shape != expected_shape:
                    logger.warning(
                        f"数据维度不匹配，期望: {expected_shape}, 实际: {data.shape}"
                    )
                    return False

            # 检查是否有数值数据
            if data.select_dtypes(include=[np.number]).empty:
                logger.error("数据中没有数值列")
                return False

            return True

        except Exception as e:
            logger.error(f"验证数据维度时发生错误: {str(e)}")
            return False

    def get_data_summary(
        self, processed_data: dict[str, pd.DataFrame]
    ) -> dict[str, Any]:
        """
        获取数据摘要信息

        Args:
            processed_data: 处理后的数据字典

        Returns:
            数据摘要信息
        """
        summary = {}

        try:
            for data_type, data in processed_data.items():
                if isinstance(data, pd.DataFrame):
                    summary[data_type] = {
                        "shape": data.shape,
                        "columns": data.columns.tolist(),
                        "index": (
                            data.index.tolist()
                            if len(data.index) <= 20
                            else data.index.tolist()[:20]
                        ),
                        "has_null": data.isnull().any().any(),
                        "numeric_columns": data.select_dtypes(
                            include=[np.number]
                        ).columns.tolist(),
                    }

        except Exception as e:
            logger.error(f"获取数据摘要时发生错误: {str(e)}")

        return summary
