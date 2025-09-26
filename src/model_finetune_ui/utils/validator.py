#!/usr/bin/env python
"""
数据验证器

验证用户上传的数据格式和内容
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

# 导入本地工具
from .utils import DataValidator as BaseDataValidator
from .utils import EnhancedLogger, performance_monitor

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器，用于验证用户上传数据的格式和内容。

    此类提供数据格式验证、类型检查和数据一致性验证功能，
    支持Type 0和Type 1两种模型类型的数据验证。
    """

    def __init__(self):
        # 标准水质参数
        self.standard_water_params = [
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

        # 标准特征编号
        self.standard_stations = [f"STZ{i}" for i in range(1, 27)]

    @performance_monitor("validate_data_format")
    def validate_data_format(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> bool:
        """
        验证数据格式

        Args:
            processed_data: 处理后的数据字典
            model_type: 模型类型

        Returns:
            验证结果
        """
        try:
            EnhancedLogger.log_operation_context(
                "validate_data_format",
                model_type=model_type,
                files_count=len(processed_data),
            )

            # 检查必需文件
            if model_type == 1:
                required_files = ['w', 'a', 'b', 'A', 'Range']  # Type 1现在也需要A文件
            else:
                required_files = ['A', 'Range']  # Type 0需要A文件

            for file_type in required_files:
                if file_type not in processed_data:
                    logger.error(f"缺少必需文件: {file_type}")
                    return False

                if not isinstance(processed_data[file_type], pd.DataFrame):
                    logger.error(f"{file_type}文件不是DataFrame格式")
                    return False

                # 使用本地数据验证工具进行基础验证
                is_valid, error_msg = BaseDataValidator.validate_dataframe(
                    processed_data[file_type], name=f"{file_type}文件"
                )
                if not is_valid:
                    logger.error(f"{file_type}文件验证失败: {error_msg}")
                    return False

            # 验证各类数据
            if model_type == 1:
                # 验证系数矩阵
                if not self._validate_coefficient_matrices(processed_data):
                    return False

            if model_type == 0:
                # 验证A系数
                if not self._validate_a_coefficient(processed_data['A']):
                    return False

            # 验证Range数据
            if not self._validate_range_data(processed_data['Range']):
                return False

            logger.info("数据格式验证通过")
            return True

        except Exception as e:
            logger.error(f"验证数据格式时发生错误: {str(e)}")
            return False

    def _validate_coefficient_matrices(
        self, processed_data: dict[str, pd.DataFrame]
    ) -> bool:
        """验证系数矩阵（w、a、b）"""
        try:
            matrices = ['w', 'a', 'b']

            for matrix_name in matrices:
                if matrix_name not in processed_data:
                    continue

                matrix = processed_data[matrix_name]

                # 检查基本格式
                if matrix.empty:
                    logger.error(f"{matrix_name}矩阵为空")
                    return False

                # 检查数值类型
                if (
                    not matrix.select_dtypes(include=[np.number]).shape[1]
                    == matrix.shape[1]
                ):
                    logger.error(f"{matrix_name}矩阵包含非数值列")
                    return False

                # 检查行索引是否为水质参数
                water_params_in_index = [
                    param
                    for param in self.standard_water_params
                    if param in matrix.index
                ]
                if len(water_params_in_index) == 0:
                    logger.warning(f"{matrix_name}矩阵行索引中没有标准水质参数")

                # 检查列是否为特征
                stations_in_cols = [
                    col
                    for col in matrix.columns
                    if col in self.standard_stations or col.startswith('STZ')
                ]
                if len(stations_in_cols) == 0:
                    logger.warning(f"{matrix_name}矩阵列中没有标准特征格式")

                logger.info(f"{matrix_name}矩阵验证通过: {matrix.shape}")

            return True

        except Exception as e:
            logger.error(f"验证系数矩阵时发生错误: {str(e)}")
            return False

    def _validate_a_coefficient(self, a_data: pd.DataFrame) -> bool:
        """验证A系数"""
        try:
            # 检查基本格式
            if a_data.empty:
                logger.error("A系数数据为空")
                return False

            # 检查数值类型
            if (
                not a_data.select_dtypes(include=[np.number]).shape[1]
                == a_data.shape[1]
            ):
                logger.error("A系数包含非数值列")
                return False

            # 检查行索引
            water_params_in_index = [
                param for param in self.standard_water_params if param in a_data.index
            ]
            if len(water_params_in_index) == 0:
                logger.warning("A系数行索引中没有标准水质参数")

            # A系数通常是单列或少数几列
            if a_data.shape[1] > 5:
                logger.warning(f"A系数有{a_data.shape[1]}列，通常应该是1-2列")

            logger.info(f"A系数验证通过: {a_data.shape}")
            return True

        except Exception as e:
            logger.error(f"验证A系数时发生错误: {str(e)}")
            return False

    def _validate_range_data(self, range_data: pd.DataFrame) -> bool:
        """验证Range数据"""
        try:
            # 检查基本格式
            if range_data.empty:
                logger.error("Range数据为空")
                return False

            # 检查数值类型
            numeric_cols = range_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                logger.error("Range数据没有数值列")
                return False

            # 检查是否有足够的观测值
            if range_data.shape[0] < 2:
                logger.warning("Range数据样本数量太少，可能影响范围计算")

            # 检查列名是否包含水质参数
            water_params_in_cols = [
                col for col in range_data.columns if col in self.standard_water_params
            ]
            if len(water_params_in_cols) == 0:
                logger.warning("Range数据列中没有标准水质参数")

            logger.info(f"Range数据验证通过: {range_data.shape}")
            return True

        except Exception as e:
            logger.error(f"验证Range数据时发生错误: {str(e)}")
            return False

    def check_data_consistency(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> tuple[bool, list[str]]:
        """
        检查数据一致性

        Args:
            processed_data: 处理后的数据字典
            model_type: 模型类型

        Returns:
            (是否一致, 警告消息列表)
        """
        warnings = []

        try:
            if model_type == 1:
                # 检查系数矩阵的维度一致性
                matrices = ['w', 'a', 'b']
                shapes = []

                for matrix_name in matrices:
                    if matrix_name in processed_data:
                        shapes.append((matrix_name, processed_data[matrix_name].shape))

                # 检查行数是否一致
                if len(shapes) > 1:
                    row_counts = [shape[1][0] for shape in shapes]
                    if not all(count == row_counts[0] for count in row_counts):
                        warnings.append(f"系数矩阵行数不一致: {shapes}")

                # 检查w和a矩阵的列数是否一致
                if 'w' in processed_data and 'a' in processed_data:
                    if processed_data['w'].shape[1] != processed_data['a'].shape[1]:
                        warnings.append(
                            f"w和a矩阵列数不一致: {processed_data['w'].shape[1]} vs {processed_data['a'].shape[1]}"
                        )

            # 检查A系数和其他矩阵的行数是否一致
            if 'A' in processed_data and model_type == 1:
                if 'w' in processed_data:
                    if processed_data['A'].shape[0] != processed_data['w'].shape[0]:
                        warnings.append(
                            f"A系数和w矩阵行数不一致: {processed_data['A'].shape[0]} vs {processed_data['w'].shape[0]}"
                        )

            # 检查Range数据的列与其他矩阵的行是否有对应关系
            if 'Range' in processed_data:
                range_cols = set(processed_data['Range'].columns)

                if model_type == 1 and 'w' in processed_data:
                    matrix_rows = set(processed_data['w'].index)
                    common_params = range_cols.intersection(matrix_rows)
                    if len(common_params) == 0:
                        warnings.append("Range数据的列与系数矩阵的行没有共同的水质参数")

                if 'A' in processed_data:
                    a_rows = set(processed_data['A'].index)
                    common_params = range_cols.intersection(a_rows)
                    if len(common_params) == 0:
                        warnings.append("Range数据的列与A系数的行没有共同的水质参数")

            # 检查数据范围合理性
            self._check_data_ranges(processed_data, warnings)

            logger.info(f"数据一致性检查完成，发现{len(warnings)}个警告")
            return True, warnings

        except Exception as e:
            logger.error(f"检查数据一致性时发生错误: {str(e)}")
            return False, [f"检查数据一致性时发生错误: {str(e)}"]

    def _check_data_ranges(
        self, processed_data: dict[str, pd.DataFrame], warnings: list[str]
    ):
        """检查数据范围合理性"""
        try:
            # 检查系数矩阵的值范围
            for matrix_name in ['w', 'a', 'b']:
                if matrix_name in processed_data:
                    matrix = processed_data[matrix_name]

                    # 检查极值
                    if matrix.min().min() < -1000 or matrix.max().max() > 1000:
                        warnings.append(f"{matrix_name}矩阵存在极值，可能需要检查")

                    # 检查是否有过多零值
                    zero_ratio = (matrix == 0).sum().sum() / matrix.size
                    if zero_ratio > 0.8:
                        warnings.append(
                            f"{matrix_name}矩阵有{zero_ratio:.1%}的零值，可能需要检查"
                        )

            # 检查A系数
            if 'A' in processed_data:
                a_matrix = processed_data['A']
                if a_matrix.min().min() < -10 or a_matrix.max().max() > 10:
                    warnings.append("A系数存在极值，可能需要检查")

            # 检查Range数据
            if 'Range' in processed_data:
                range_data = processed_data['Range']

                # 使用本地工具验证水质指标合理性
                negative_params = []
                for param in range_data.columns:
                    if param in self.standard_water_params:
                        for value in range_data[param].dropna():
                            is_valid, error_msg = (
                                BaseDataValidator.validate_water_quality_indicator(
                                    value, param
                                )
                            )
                            if not is_valid and "不应为负数" in error_msg:
                                if param not in negative_params:
                                    negative_params.append(param)
                                break

                if negative_params:
                    warnings.append(f"以下水质参数存在负值: {negative_params}")

        except Exception as e:
            logger.error(f"检查数据范围时发生错误: {str(e)}")
            warnings.append(f"检查数据范围时发生错误: {str(e)}")

    def get_validation_report(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> dict[str, Any]:
        """
        获取详细的验证报告

        Args:
            processed_data: 处理后的数据字典
            model_type: 模型类型

        Returns:
            验证报告字典
        """
        report = {
            "model_type": model_type,
            "files_validated": len(processed_data),
            "validation_passed": False,
            "consistency_check_passed": False,
            "warnings": [],
            "errors": [],
            "file_details": {},
        }

        try:
            # 格式验证
            report["validation_passed"] = self.validate_data_format(
                processed_data, model_type
            )

            # 一致性检查
            consistency_result, warnings = self.check_data_consistency(
                processed_data, model_type
            )
            report["consistency_check_passed"] = consistency_result
            report["warnings"] = warnings

            # 文件详情
            for file_type, data in processed_data.items():
                report["file_details"][file_type] = {
                    "shape": data.shape,
                    "columns": data.columns.tolist(),
                    "index": data.index.tolist(),
                    "null_count": data.isnull().sum().sum(),
                    "data_types": data.dtypes.to_dict(),
                }

            logger.info("验证报告生成完成")
            return report

        except Exception as e:
            logger.error(f"生成验证报告时发生错误: {str(e)}")
            report["errors"].append(str(e))
            return report
