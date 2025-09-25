#!/usr/bin/env python
"""
解密管理器

用于解密bin文件并解析出参数，支持保存为CSV格式
"""

import json
import logging
import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .utils import ConfigManager, EnhancedLogger, performance_monitor

logger = logging.getLogger(__name__)


class DecryptionManager:
    """解密管理器，用于解密bin文件并解析参数。

    支持解密加密的模型文件，解析出w、a、b、A系数和Range数据，
    并提供CSV格式导出功能。
    """

    def __init__(self):
        # 标准水质参数
        self.water_params = [
            "turbidity", "ss", "sd", "do", "codmn",
            "codcr", "chla", "tn", "tp", "chroma", "nh3n"
        ]
        # 标准特征站点
        self.feature_stations = [f"STZ{i}" for i in range(1, 27)]

    def get_decryption_config(self) -> Dict[str, Any]:
        """获取解密配置"""
        try:
            return ConfigManager.get_encryption_config()
        except Exception as e:
            logger.error(f"无法获取解密配置: {e}")
            # 提供默认配置
            return {
                "password": "default_password",
                "salt": "default_salt",
                "iv": "default_iv"
            }

    @performance_monitor("decrypt_bin_file")
    def decrypt_bin_file(self, bin_file_path: str) -> Optional[Dict[str, Any]]:
        """
        解密bin文件

        Args:
            bin_file_path: bin文件路径

        Returns:
            解密后的数据字典，失败返回None
        """
        try:
            EnhancedLogger.log_operation_context(
                "decrypt_bin_file",
                file_path=bin_file_path
            )

            if not Path(bin_file_path).exists():
                logger.error(f"文件不存在: {bin_file_path}")
                return None

            # 获取解密配置
            decryption_config = self.get_decryption_config()

            # 尝试解密文件
            try:
                # 首先尝试使用外部解密函数
                from .utils import decrypt_file_to_data
                decrypted_data = decrypt_file_to_data(
                    file_path=bin_file_path,
                    password=decryption_config["password"],
                    salt=decryption_config["salt"],
                    iv=decryption_config["iv"],
                    logger=logger
                )
            except ImportError:
                # 如果外部函数不可用，使用简化解密
                logger.warning("外部解密函数不可用，尝试简化解密")
                decrypted_data = self._simple_decrypt(bin_file_path)

            if decrypted_data:
                logger.info(f"bin文件解密成功: {bin_file_path}")
                return decrypted_data
            else:
                logger.error("bin文件解密失败")
                return None

        except Exception as e:
            logger.error(f"解密过程中发生错误: {str(e)}")
            return None

    def _simple_decrypt(self, file_path: str) -> Optional[Dict[str, Any]]:
        """简化解密方法（当外部解密函数不可用时）"""
        try:
            # 尝试直接读取JSON（用于测试）
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info("使用简化解密成功")
            return data
        except:
            logger.error("简化解密也失败")
            return None

    @performance_monitor("parse_to_csv_format")
    def parse_to_csv_format(self, decrypted_data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        将解密数据解析为CSV格式

        Args:
            decrypted_data: 解密后的数据

        Returns:
            包含各系数DataFrame的字典
        """
        try:
            model_type = decrypted_data.get("type", 0)
            logger.info(f"解析模型类型: {model_type}")

            csv_data = {}

            if model_type == 0:
                # Type 0: 只有A系数和Range
                csv_data.update(self._parse_type_0_data(decrypted_data))
            elif model_type == 1:
                # Type 1: w、a、b、A系数和Range
                csv_data.update(self._parse_type_1_data(decrypted_data))
            else:
                logger.error(f"不支持的模型类型: {model_type}")
                return {}

            logger.info(f"成功解析出{len(csv_data)}个CSV文件")
            return csv_data

        except Exception as e:
            logger.error(f"解析CSV格式时发生错误: {str(e)}")
            return {}

    def _parse_type_0_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Type 0数据（A系数 + Range）"""
        csv_data = {}

        # 解析A系数
        if "A" in data:
            a_values = data["A"]
            if len(a_values) == len(self.water_params):
                df_a = pd.DataFrame(
                    {"A": a_values},
                    index=self.water_params
                )
                csv_data["A_coefficients"] = df_a
                logger.info(f"解析A系数: {df_a.shape}")

        # 解析Range数据
        csv_data.update(self._parse_range_data(data))

        return csv_data

    def _parse_type_1_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Type 1数据（w、a、b、A系数 + Range）"""
        csv_data = {}

        # 解析w系数 (特征x参数)
        if "w" in data:
            w_values = data["w"]
            expected_size = len(self.feature_stations) * len(self.water_params)
            if len(w_values) == expected_size:
                w_matrix = self._reshape_to_matrix(w_values, len(self.feature_stations), len(self.water_params))
                df_w = pd.DataFrame(w_matrix, index=self.feature_stations, columns=self.water_params)
                csv_data["w_coefficients"] = df_w
                logger.info(f"解析w系数: {df_w.shape}")

        # 解析a系数 (特征x参数)
        if "a" in data:
            a_values = data["a"]
            expected_size = len(self.feature_stations) * len(self.water_params)
            if len(a_values) == expected_size:
                a_matrix = self._reshape_to_matrix(a_values, len(self.feature_stations), len(self.water_params))
                df_a = pd.DataFrame(a_matrix, index=self.feature_stations, columns=self.water_params)
                csv_data["a_coefficients"] = df_a
                logger.info(f"解析a系数: {df_a.shape}")

        # 解析b系数 (参数x特征)
        if "b" in data:
            b_values = data["b"]
            expected_size = len(self.water_params) * len(self.feature_stations)
            if len(b_values) == expected_size:
                b_matrix = self._reshape_to_matrix(b_values, len(self.water_params), len(self.feature_stations))
                df_b = pd.DataFrame(b_matrix, index=self.water_params, columns=self.feature_stations)
                csv_data["b_coefficients"] = df_b
                logger.info(f"解析b系数: {df_b.shape}")

        # 解析A系数
        if "A" in data:
            a_values = data["A"]
            if len(a_values) == len(self.water_params):
                df_a = pd.DataFrame(
                    {"A": a_values},
                    index=self.water_params
                )
                csv_data["A_coefficients"] = df_a
                logger.info(f"解析A系数: {df_a.shape}")

        # 解析Range数据
        csv_data.update(self._parse_range_data(data))

        return csv_data

    def _parse_range_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Range数据"""
        csv_data = {}

        if "Range" in data:
            range_values = data["Range"]
            # Range应该是展平的min/max值
            if len(range_values) == len(self.water_params) * 2:
                # 重新组织为min/max列
                range_matrix = self._reshape_to_matrix(range_values, len(self.water_params), 2)
                df_range = pd.DataFrame(range_matrix, index=self.water_params, columns=["min", "max"])
                csv_data["range_data"] = df_range
                logger.info(f"解析Range数据: {df_range.shape}")

        return csv_data

    def _reshape_to_matrix(self, flat_list: list, rows: int, cols: int) -> list:
        """将扁平化列表重新组织为矩阵"""
        if len(flat_list) != rows * cols:
            logger.error(f"数据长度不匹配: 期望{rows}x{cols}={rows*cols}, 实际{len(flat_list)}")
            return []

        matrix = []
        for i in range(rows):
            row = flat_list[i*cols:(i+1)*cols]
            matrix.append(row)
        return matrix

    def generate_csv_files(self, csv_data: Dict[str, pd.DataFrame]) -> Dict[str, bytes]:
        """
        生成CSV文件的字节内容

        Args:
            csv_data: 包含DataFrame的字典

        Returns:
            包含CSV文件名和字节内容的字典
        """
        csv_files = {}

        for data_type, df in csv_data.items():
            try:
                # 生成CSV字节流
                output = io.StringIO()
                df.to_csv(output, index=True, encoding='utf-8')
                csv_content = output.getvalue().encode('utf-8')

                filename = f"{data_type}.csv"
                csv_files[filename] = csv_content

                logger.info(f"生成CSV文件: {filename} ({len(csv_content)} bytes)")

            except Exception as e:
                logger.error(f"生成{data_type}的CSV文件失败: {str(e)}")

        return csv_files