#!/usr/bin/env python
"""
文件处理器

处理文件上传、验证和转换
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# 导入本地工具
from .utils import EncodingDetector, EnhancedLogger, FileUtils, performance_monitor

logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理器"""

    def __init__(self):
        self.temp_dir = None
        self.supported_formats = ['.csv', '.xlsx', '.xls']

    @performance_monitor("read_uploaded_file")
    def read_uploaded_file(self, uploaded_file, file_type: str) -> pd.DataFrame | None:
        """
        读取上传的文件

        Args:
            uploaded_file: Streamlit上传的文件对象
            file_type: 文件类型标识

        Returns:
            DataFrame或None
        """
        try:
            if uploaded_file is None:
                return None

            # 检查文件格式
            file_extension = Path(uploaded_file.name).suffix.lower()
            if file_extension not in self.supported_formats:
                logger.error(f"不支持的文件格式: {file_extension}")
                return None

            # 记录文件信息
            EnhancedLogger.log_operation_context(
                "read_uploaded_file",
                file_type=file_type,
                file_name=uploaded_file.name,
                file_size=(
                    uploaded_file.size if hasattr(uploaded_file, 'size') else "unknown"
                ),
            )

            # 读取文件
            if file_extension == '.csv':
                # 先保存到临时文件以便使用编码检测
                temp_path = self._save_uploaded_to_temp(uploaded_file)
                if temp_path:
                    df = EncodingDetector.read_csv_file(temp_path, index_col=0)
                    os.unlink(temp_path)  # 删除临时文件
                else:
                    df = pd.read_csv(uploaded_file, index_col=0)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file, index_col=0)
            else:
                logger.error(f"未知的文件格式: {file_extension}")
                return None

            if df is not None:
                EnhancedLogger.log_data_summary(df, f"{file_type}文件")
                logger.info(
                    f"成功读取{file_type}文件: {uploaded_file.name}, 形状: {df.shape}"
                )

            return df

        except Exception as e:
            logger.error(f"读取{file_type}文件时发生错误: {str(e)}")
            return None

    def validate_file_structure(
        self, df: pd.DataFrame, file_type: str
    ) -> tuple[bool, list[str]]:
        """
        验证文件结构

        Args:
            df: DataFrame
            file_type: 文件类型

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        try:
            # 基本检查
            if df.empty:
                errors.append(f"{file_type}文件为空")
                return False, errors

            # 检查数据类型
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) == 0:
                errors.append(f"{file_type}文件没有数值列")

            # 检查缺失值
            if df.isnull().all().any():
                errors.append(f"{file_type}文件存在完全为空的列")

            # 根据文件类型进行特定检查
            if file_type in ['w', 'a', 'b']:
                # 系数矩阵应该有多列
                if df.shape[1] < 2:
                    errors.append(f"{file_type}系数矩阵应该有多个特征列")

            elif file_type == 'A':
                # A系数通常是单列
                if df.shape[1] != 1:
                    logger.warning(f"A系数文件有{df.shape[1]}列，通常应该是1列")

            elif file_type == 'Range':
                # Range数据应该有多行观测值
                if df.shape[0] < 2:
                    errors.append("Range数据应该有多行观测值用于计算范围")

            # 检查索引是否为水质参数
            expected_params = [
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

            if file_type != 'Range':
                # 检查是否有预期的水质参数
                matching_params = [
                    param for param in expected_params if param in df.index
                ]
                if len(matching_params) == 0:
                    errors.append(f"{file_type}文件的行索引中没有找到标准水质参数")

            return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"验证{file_type}文件结构时发生错误: {str(e)}")
            return False, [f"验证{file_type}文件时发生错误: {str(e)}"]

    def standardize_dataframe(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """
        标准化DataFrame格式

        Args:
            df: 原始DataFrame
            file_type: 文件类型

        Returns:
            标准化后的DataFrame
        """
        try:
            # 复制DataFrame避免修改原始数据
            standardized_df = df.copy()

            # 清理索引和列名
            standardized_df.index = standardized_df.index.astype(str).str.strip()
            standardized_df.columns = standardized_df.columns.astype(str).str.strip()

            # 确保数值列是浮点类型
            for col in standardized_df.select_dtypes(include=[np.number]).columns:
                standardized_df[col] = pd.to_numeric(
                    standardized_df[col], errors='coerce'
                )

            # 处理缺失值
            if file_type in ['w', 'a', 'b', 'A']:
                # 系数矩阵的缺失值用0填充
                standardized_df = standardized_df.fillna(0.0)
            elif file_type == 'Range':
                # Range数据删除缺失值
                standardized_df = standardized_df.dropna()

            logger.info(f"{file_type}文件标准化完成: {standardized_df.shape}")
            return standardized_df

        except Exception as e:
            logger.error(f"标准化{file_type}文件时发生错误: {str(e)}")
            return df

    def get_file_preview(
        self, df: pd.DataFrame, max_rows: int = 10, max_cols: int = 10
    ) -> dict[str, Any]:
        """
        获取文件预览信息

        Args:
            df: DataFrame
            max_rows: 最大显示行数
            max_cols: 最大显示列数

        Returns:
            预览信息字典
        """
        try:
            preview = {
                "shape": df.shape,
                "columns": df.columns.tolist()[:max_cols],
                "index": df.index.tolist()[:max_rows],
                "data_types": df.dtypes.to_dict(),
                "sample_data": df.head(max_rows).to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "numeric_columns": df.select_dtypes(
                    include=[np.number]
                ).columns.tolist(),
                "stats": {},
            }

            # 添加数值列的统计信息
            for col in df.select_dtypes(include=[np.number]).columns[:max_cols]:
                preview["stats"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                }

            return preview

        except Exception as e:
            logger.error(f"获取文件预览时发生错误: {str(e)}")
            return {"error": str(e)}

    def save_temp_file(self, df: pd.DataFrame, file_type: str) -> str | None:
        """
        保存临时文件

        Args:
            df: DataFrame
            file_type: 文件类型

        Returns:
            临时文件路径
        """
        try:
            if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp()

            temp_path = Path(self.temp_dir) / f"{file_type}_temp.csv"
            df.to_csv(temp_path)

            logger.info(f"临时文件已保存: {temp_path}")
            return str(temp_path)

        except Exception as e:
            logger.error(f"保存临时文件时发生错误: {str(e)}")
            return None

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil

                shutil.rmtree(self.temp_dir)
                logger.info("临时文件已清理")
        except Exception as e:
            logger.error(f"清理临时文件时发生错误: {str(e)}")

    def _save_uploaded_to_temp(self, uploaded_file) -> str | None:
        """将上传文件保存到临时位置"""
        try:
            if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp()

            # 生成临时文件路径
            temp_filename = FileUtils.clean_filename(uploaded_file.name)
            temp_path = Path(self.temp_dir) / temp_filename

            # 保存文件
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())

            # 重置文件指针
            uploaded_file.seek(0)

            return str(temp_path)

        except Exception as e:
            logger.error(f"保存临时文件失败: {str(e)}")
            return None

    def __del__(self):
        """析构函数，清理临时文件"""
        self.cleanup_temp_files()
