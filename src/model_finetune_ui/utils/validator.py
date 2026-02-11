#!/usr/bin/env python
"""
数据验证器

验证用户上传的数据格式和内容。
不对维度做固定值约束，仅校验文件间维度关系是否一致。
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

    不假设固定的参数数量或特征数量，仅基于文件间维度关系进行校验：
    - w/a 维度一致 (F×P)
    - b 维度为 w/a 的转置 (P×F)
    - A 行数 = 参数数 P
    - Range 行数 = 参数数 P, 列数 = 2 (min/max)
    """

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
                required_files = ["w", "a", "b", "A", "Range"]
            else:
                required_files = ["A", "Range"]

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

            # 验证各文件基本格式（非空、全数值）
            if model_type == 1:
                if not self._validate_matrix_basic(processed_data, ["w", "a", "b"]):
                    return False

            if not self._validate_a_coefficient(processed_data["A"]):
                return False

            if not self._validate_range_data(processed_data["Range"]):
                return False

            # 验证文件间维度一致性
            if not self._validate_cross_file_dimensions(processed_data, model_type):
                return False

            logger.info("数据格式验证通过")
            return True

        except Exception as e:
            logger.error(f"验证数据格式时发生错误: {str(e)}")
            return False

    def _validate_matrix_basic(
        self, processed_data: dict[str, pd.DataFrame], matrix_names: list[str]
    ) -> bool:
        """验证系数矩阵的基本格式（非空、全数值）"""
        try:
            for name in matrix_names:
                if name not in processed_data:
                    continue

                matrix = processed_data[name]

                if matrix.empty:
                    logger.error(f"{name}矩阵为空")
                    return False

                if (
                    matrix.select_dtypes(include=[np.number]).shape[1]
                    != matrix.shape[1]
                ):
                    logger.error(f"{name}矩阵包含非数值列")
                    return False

                logger.info(f"{name}矩阵基本格式验证通过: {matrix.shape}")

            return True

        except Exception as e:
            logger.error(f"验证系数矩阵时发生错误: {str(e)}")
            return False

    def _validate_a_coefficient(self, a_data: pd.DataFrame) -> bool:
        """验证A系数基本格式"""
        try:
            if a_data.empty:
                logger.error("A系数数据为空")
                return False

            if (
                a_data.select_dtypes(include=[np.number]).shape[1]
                != a_data.shape[1]
            ):
                logger.error("A系数包含非数值列")
                return False

            logger.info(f"A系数基本格式验证通过: {a_data.shape}")
            return True

        except Exception as e:
            logger.error(f"验证A系数时发生错误: {str(e)}")
            return False

    def _validate_range_data(self, range_data: pd.DataFrame) -> bool:
        """验证Range数据基本格式"""
        try:
            if range_data.empty:
                logger.error("Range数据为空")
                return False

            numeric_cols = range_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                logger.error("Range数据没有数值列")
                return False

            if range_data.shape[0] < 2:
                logger.warning("Range数据行数太少，可能影响范围计算")

            logger.info(f"Range数据基本格式验证通过: {range_data.shape}")
            return True

        except Exception as e:
            logger.error(f"验证Range数据时发生错误: {str(e)}")
            return False

    def _validate_cross_file_dimensions(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> bool:
        """验证文件间维度一致性

        维度关系（以 P=参数数, F=特征数 为例）：
        - w: F×P,  a: F×P  → 维度完全一致
        - b: P×F             → 与 w/a 转置
        - A: P×1             → 行数 = P
        - Range: P×2         → 行数 = P (min/max两列)
        """
        try:
            if model_type == 1:
                w = processed_data["w"]
                a = processed_data["a"]
                b = processed_data["b"]
                a_coeff = processed_data["A"]
                range_data = processed_data["Range"]

                # w/a 维度必须完全一致
                if w.shape != a.shape:
                    logger.error(
                        f"w和a矩阵维度不一致: w={w.shape}, a={a.shape}"
                    )
                    return False

                # 从 w 推断: 行数=F(特征数), 列数=P(参数数)
                f_count = w.shape[0]  # 特征数
                p_count = w.shape[1]  # 参数数

                # b 应为 P×F
                if b.shape != (p_count, f_count):
                    logger.error(
                        f"b矩阵维度与w/a不匹配: b={b.shape}, 期望=({p_count}, {f_count})"
                    )
                    return False

                # A 行数应为 P
                if a_coeff.shape[0] != p_count:
                    logger.error(
                        f"A系数行数与参数数不一致: A行数={a_coeff.shape[0]}, 参数数={p_count}"
                    )
                    return False

                # Range 行数应为 P
                if range_data.shape[0] != p_count:
                    logger.error(
                        f"Range行数与参数数不一致: Range行数={range_data.shape[0]}, 参数数={p_count}"
                    )
                    return False

                logger.info(
                    f"维度一致性验证通过: {p_count}个参数 × {f_count}个特征"
                )

            elif model_type == 0:
                a_coeff = processed_data["A"]
                range_data = processed_data["Range"]

                p_count = a_coeff.shape[0]

                # Range 行数应与 A 行数一致
                if range_data.shape[0] != p_count:
                    logger.error(
                        f"Range行数与A系数行数不一致: Range行数={range_data.shape[0]}, A行数={p_count}"
                    )
                    return False

                logger.info(f"维度一致性验证通过: {p_count}个参数")

            return True

        except Exception as e:
            logger.error(f"验证维度一致性时发生错误: {str(e)}")
            return False

    def check_data_consistency(
        self, processed_data: dict[str, pd.DataFrame], model_type: int
    ) -> tuple[bool, list[str]]:
        """
        检查数据一致性（软性警告，不阻止流程）

        Args:
            processed_data: 处理后的数据字典
            model_type: 模型类型

        Returns:
            (是否一致, 警告消息列表)
        """
        warnings = []

        try:
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
            for matrix_name in ["w", "a", "b"]:
                if matrix_name in processed_data:
                    matrix = processed_data[matrix_name]

                    if matrix.min().min() < -1000 or matrix.max().max() > 1000:
                        warnings.append(f"{matrix_name}矩阵存在极值，可能需要检查")

                    zero_ratio = (matrix == 0).sum().sum() / matrix.size
                    if zero_ratio > 0.8:
                        warnings.append(
                            f"{matrix_name}矩阵有{zero_ratio:.1%}的零值，可能需要检查"
                        )

            # 检查A系数
            if "A" in processed_data:
                a_matrix = processed_data["A"]
                if a_matrix.min().min() < -10 or a_matrix.max().max() > 10:
                    warnings.append("A系数存在极值，可能需要检查")

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
