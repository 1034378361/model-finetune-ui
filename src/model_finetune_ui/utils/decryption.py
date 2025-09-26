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
        # 标准水质参数（固定）
        self.water_params = [
            "turbidity", "ss", "sd", "do", "codmn",
            "codcr", "chla", "tn", "tp", "chroma", "nh3n"
        ]
        # 特征站点将根据数据动态推断
        self.feature_stations = None

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

            # 步骤1：验证文件路径
            logger.info("🔍 步骤1/4: 验证文件路径和属性...")
            validation_result = self._validate_file_path(bin_file_path)
            if not validation_result["valid"]:
                logger.error(f"❌ 文件路径验证失败: {validation_result['error']}")
                return None

            file_size = validation_result.get("size", 0)
            logger.info(f"✅ 文件验证通过: {bin_file_path} ({file_size:,} bytes)")

            # 步骤2：获取解密配置
            logger.info("🔧 步骤2/4: 获取解密配置...")
            decryption_config = self.get_decryption_config()
            logger.info("✅ 解密配置已加载")

            # 步骤3：执行解密
            logger.info("🔓 步骤3/4: 执行BIN文件解密...")
            try:
                # 首先尝试使用外部解密函数
                from autowaterqualitymodeler.utils.encryption import decrypt_file

                decrypted_result = decrypt_file(bin_file_path)
                if decrypted_result:
                    # 检查返回的是字典还是字符串
                    if isinstance(decrypted_result, dict):
                        decrypted_data = decrypted_result
                        logger.info("✅ 解密成功 (返回字典格式)")
                    elif isinstance(decrypted_result, str):
                        import json
                        decrypted_data = json.loads(decrypted_result)
                        logger.info("✅ 解密成功 (JSON字符串已解析)")
                    else:
                        logger.error(f"❌ 未知的解密结果类型: {type(decrypted_result)}")
                        decrypted_data = None
                else:
                    logger.error("❌ 解密函数返回空结果")
                    decrypted_data = None
            except ImportError:
                # 如果外部函数不可用，使用简化解密
                logger.warning("⚠️ 外部解密函数不可用，尝试简化解密")
                decrypted_data = self._simple_decrypt(bin_file_path)

            if decrypted_data:
                # 步骤4：验证和分析解密数据
                logger.info("🔍 步骤4/4: 验证解密数据结构...")
                validation_result = self._validate_decrypted_data(decrypted_data)
                if not validation_result["valid"]:
                    logger.error(f"❌ 解密数据验证失败: {validation_result['error']}")
                    return None

                # 显示解密结果摘要
                model_type = decrypted_data.get("type", "未知")
                feature_count = len(self.feature_stations) if self.feature_stations else 0

                logger.info("🎉 BIN文件解密完成！")
                logger.info(f"📊 模型信息: Type {model_type} ({feature_count}特征×{len(self.water_params)}参数)")
                logger.info(f"📁 数据结构: {len([k for k, v in decrypted_data.items() if isinstance(v, list)])}个数据数组")

                return decrypted_data
            else:
                logger.error("❌ bin文件解密失败")
                return None

        except Exception as e:
            logger.error(f"❌ 解密过程中发生错误: {str(e)}")
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
            feature_count = len(self.feature_stations) if self.feature_stations else 0

            logger.info("📋 开始解析数据为CSV格式...")
            logger.info(f"📊 模型配置: Type {model_type}, {feature_count}个特征站点, {len(self.water_params)}个水质参数")

            csv_data = {}

            if model_type == 0:
                logger.info("🎯 解析Type 0模型数据 (A系数 + Range数据)...")
                csv_data.update(self._parse_type_0_data(decrypted_data))
            elif model_type == 1:
                logger.info("🎯 解析Type 1模型数据 (w, a, b, A系数 + Range数据)...")
                csv_data.update(self._parse_type_1_data(decrypted_data))
            else:
                logger.error(f"❌ 不支持的模型类型: {model_type}")
                return {}

            # 显示解析结果统计
            total_cells = sum(df.size for df in csv_data.values())
            total_non_zero = sum((df != 0).sum().sum() for df in csv_data.values()
                               if df.select_dtypes(include=[float, int]).size > 0)

            logger.info("✅ CSV数据解析完成！")
            logger.info(f"📄 生成文件数量: {len(csv_data)}个")
            logger.info(f"📊 数据统计: {total_cells:,}个数据单元, {total_non_zero:,}个非零值")

            # 显示各文件详情
            for filename, df in csv_data.items():
                non_zero_count = (df != 0).sum().sum() if df.select_dtypes(include=[float, int]).size > 0 else df.size
                logger.info(f"  📈 {filename}: {df.shape[0]}×{df.shape[1]} ({non_zero_count}个非零值)")

            return csv_data

        except Exception as e:
            logger.error(f"❌ 解析CSV格式时发生错误: {str(e)}")
            return {}

    def _parse_type_0_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Type 0数据（A系数 + Range）"""
        csv_data = {}

        try:
            # 解析A系数
            if "A" in data:
                a_values = data["A"]
                if len(a_values) == len(self.water_params):
                    # 检查是否有异常值
                    if any(pd.isna(val) for val in a_values):
                        logger.warning("A系数中包含NaN值")

                    df_a = pd.DataFrame(
                        {"A": a_values},
                        index=self.water_params
                    )
                    csv_data["A_coefficients"] = df_a
                    logger.info(f"解析A系数: {df_a.shape}")
                else:
                    logger.error(f"A系数长度不匹配: 期望{len(self.water_params)}, 实际{len(a_values)}")

            # 解析Range数据
            csv_data.update(self._parse_range_data(data))

        except Exception as e:
            logger.error(f"Type 0数据解析失败: {str(e)}")

        return csv_data

    def _parse_type_1_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Type 1数据（w、a、b、A系数 + Range）"""
        csv_data = {}

        try:
            # 解析w系数 (特征x参数)
            if "w" in data:
                w_values = data["w"]
                expected_size = len(self.feature_stations) * len(self.water_params)
                if len(w_values) == expected_size:
                    w_matrix = self._reshape_to_matrix(w_values, len(self.feature_stations), len(self.water_params))
                    if w_matrix:  # 检查重塑是否成功
                        df_w = pd.DataFrame(w_matrix, index=self.feature_stations, columns=self.water_params)
                        # 检查异常值
                        if df_w.isna().any().any():
                            logger.warning("w系数中包含NaN值")
                        csv_data["w_coefficients"] = df_w
                        logger.info(f"解析w系数: {df_w.shape}")
                else:
                    logger.error(f"w系数长度不匹配: 期望{expected_size}, 实际{len(w_values)}")

            # 解析a系数 (特征x参数)
            if "a" in data:
                a_values = data["a"]
                expected_size = len(self.feature_stations) * len(self.water_params)
                if len(a_values) == expected_size:
                    a_matrix = self._reshape_to_matrix(a_values, len(self.feature_stations), len(self.water_params))
                    if a_matrix:
                        df_a = pd.DataFrame(a_matrix, index=self.feature_stations, columns=self.water_params)
                        if df_a.isna().any().any():
                            logger.warning("a系数中包含NaN值")
                        csv_data["a_coefficients"] = df_a
                        logger.info(f"解析a系数: {df_a.shape}")
                else:
                    logger.error(f"a系数长度不匹配: 期望{expected_size}, 实际{len(a_values)}")

            # 解析b系数 (参数x特征)
            if "b" in data:
                b_values = data["b"]
                expected_size = len(self.water_params) * len(self.feature_stations)
                if len(b_values) == expected_size:
                    b_matrix = self._reshape_to_matrix(b_values, len(self.water_params), len(self.feature_stations))
                    if b_matrix:
                        df_b = pd.DataFrame(b_matrix, index=self.water_params, columns=self.feature_stations)
                        if df_b.isna().any().any():
                            logger.warning("b系数中包含NaN值")
                        csv_data["b_coefficients"] = df_b
                        logger.info(f"解析b系数: {df_b.shape}")
                else:
                    logger.error(f"b系数长度不匹配: 期望{expected_size}, 实际{len(b_values)}")

            # 解析A系数
            if "A" in data:
                A_values = data["A"]
                if len(A_values) == len(self.water_params):
                    if any(pd.isna(val) for val in A_values):
                        logger.warning("A系数中包含NaN值")
                    df_A = pd.DataFrame(
                        {"A": A_values},
                        index=self.water_params
                    )
                    csv_data["A_coefficients"] = df_A
                    logger.info(f"解析A系数: {df_A.shape}")
                else:
                    logger.error(f"A系数长度不匹配: 期望{len(self.water_params)}, 实际{len(A_values)}")

            # 解析Range数据
            csv_data.update(self._parse_range_data(data))

        except Exception as e:
            logger.error(f"Type 1数据解析失败: {str(e)}")

        return csv_data

    def _parse_range_data(self, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """解析Range数据"""
        csv_data = {}

        try:
            if "Range" in data:
                range_values = data["Range"]
                expected_size = len(self.water_params) * 2

                if len(range_values) == expected_size:
                    # 重新组织为min/max列
                    range_matrix = self._reshape_to_matrix(range_values, len(self.water_params), 2)
                    if range_matrix:
                        df_range = pd.DataFrame(range_matrix, index=self.water_params, columns=["min", "max"])

                        # 检查异常值
                        if df_range.isna().any().any():
                            logger.warning("Range数据中包含NaN值")

                        # 检查min/max关系合理性
                        invalid_ranges = df_range[df_range["min"] > df_range["max"]]
                        if not invalid_ranges.empty:
                            logger.warning(f"发现{len(invalid_ranges)}个参数的min > max: {invalid_ranges.index.tolist()}")

                        # 检查是否存在负值范围（可能不合理）
                        negative_ranges = df_range[(df_range["min"] < 0) | (df_range["max"] < 0)]
                        if not negative_ranges.empty:
                            logger.warning(f"发现{len(negative_ranges)}个参数包含负值: {negative_ranges.index.tolist()}")

                        csv_data["range_data"] = df_range
                        logger.info(f"解析Range数据: {df_range.shape}")
                else:
                    logger.error(f"Range数据长度不匹配: 期望{expected_size}, 实际{len(range_values)}")

        except Exception as e:
            logger.error(f"Range数据解析失败: {str(e)}")

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
        logger.info("💾 开始生成CSV文件...")
        csv_files = {}
        total_size = 0

        for data_type, df in csv_data.items():
            try:
                # 生成CSV字节流
                output = io.StringIO()
                df.to_csv(output, index=True, encoding='utf-8')
                csv_content = output.getvalue().encode('utf-8')

                filename = f"{data_type}.csv"
                csv_files[filename] = csv_content
                file_size = len(csv_content)
                total_size += file_size

                logger.info(f"✅ {filename}: {file_size:,} bytes, {df.shape[0]}×{df.shape[1]}")

            except Exception as e:
                logger.error(f"❌ 生成{data_type}的CSV文件失败: {str(e)}")

        if csv_files:
            logger.info("🎉 CSV文件生成完成！")
            logger.info(f"📄 文件总数: {len(csv_files)}个")
            logger.info(f"📊 总大小: {total_size:,} bytes ({total_size/1024:.1f} KB)")

        return csv_files

    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """验证文件路径和基本属性"""
        try:
            path_obj = Path(file_path)

            # 检查文件是否存在
            if not path_obj.exists():
                return {"valid": False, "error": f"文件不存在: {file_path}"}

            # 检查是否为文件（非目录）
            if not path_obj.is_file():
                return {"valid": False, "error": f"路径不是文件: {file_path}"}

            # 检查文件大小（不能为空，不能过大）
            file_size = path_obj.stat().st_size
            if file_size == 0:
                return {"valid": False, "error": "文件为空"}

            # 检查文件大小限制（100MB）
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                return {"valid": False, "error": f"文件过大 ({file_size} bytes > {max_size} bytes)"}

            # 检查文件扩展名
            allowed_extensions = {'.bin', '.json', '.txt'}  # 允许的扩展名
            if path_obj.suffix.lower() not in allowed_extensions:
                logger.warning(f"文件扩展名不常见: {path_obj.suffix}")

            return {"valid": True, "size": file_size}

        except Exception as e:
            return {"valid": False, "error": f"文件路径验证异常: {str(e)}"}

    def _infer_feature_count(self, data: Dict[str, Any]) -> int:
        """从数据中智能推断特征数量"""
        try:
            logger.info("🔍 智能分析特征配置...")
            param_count = len(self.water_params)

            # 分析各系数数组长度
            coeff_info = {}
            for key, value in data.items():
                if isinstance(value, list) and key != 'Range':
                    coeff_info[key] = len(value)

            logger.info(f"📊 发现系数数组: {coeff_info}")

            # 从w或a系数推断特征数量
            for coeff_key in ['w', 'a']:
                if coeff_key in data and isinstance(data[coeff_key], list):
                    coeff_length = len(data[coeff_key])

                    # 检查是否能被参数数量整除
                    if coeff_length % param_count == 0:
                        feature_count = coeff_length // param_count
                        logger.info(f"✅ 从{coeff_key}系数推断特征数量: {feature_count}个")
                        logger.info(f"📐 计算: {coeff_length} ÷ {param_count} = {feature_count} (特征×参数)")

                        # 验证其他系数是否一致
                        self._validate_feature_consistency(data, feature_count, param_count)
                        return feature_count

            # 如果无法从w/a推断，尝试从b系数推断
            if 'b' in data and isinstance(data['b'], list):
                b_length = len(data['b'])

                if b_length % param_count == 0:
                    feature_count = b_length // param_count
                    logger.info(f"✅ 从b系数推断特征数量: {feature_count}个")
                    logger.info(f"📐 计算: {b_length} ÷ {param_count} = {feature_count} (参数×特征)")
                    return feature_count

            # 默认返回26（向后兼容）
            logger.warning("⚠️ 无法推断特征数量，使用默认值26")
            return 26

        except Exception as e:
            logger.error(f"❌ 推断特征数量时出错: {str(e)}，使用默认值26")
            return 26

    def _validate_feature_consistency(self, data: Dict[str, Any], feature_count: int, param_count: int):
        """验证特征数量一致性"""
        try:
            expected_sizes = {
                'w': feature_count * param_count,
                'a': feature_count * param_count,
                'b': param_count * feature_count,
                'A': param_count,
                'Range': param_count * 2
            }

            inconsistencies = []
            for key, expected_size in expected_sizes.items():
                if key in data and isinstance(data[key], list):
                    actual_size = len(data[key])
                    if actual_size == expected_size:
                        logger.info(f"  ✅ {key}: {actual_size} (符合预期)")
                    else:
                        inconsistencies.append(f"{key}: {actual_size}≠{expected_size}")
                        logger.warning(f"  ⚠️ {key}: {actual_size} (期望{expected_size})")

            if inconsistencies:
                logger.warning(f"⚠️ 发现{len(inconsistencies)}个维度不一致: {', '.join(inconsistencies)}")
            else:
                logger.info("✅ 所有系数维度一致性验证通过")

        except Exception as e:
            logger.error(f"❌ 特征一致性验证出错: {str(e)}")

    def _validate_decrypted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证解密后的数据结构"""
        try:
            # 检查基本结构
            if not isinstance(data, dict):
                return {"valid": False, "error": "解密数据不是字典格式"}

            # 检查type字段
            if "type" not in data:
                return {"valid": False, "error": "缺少模型类型字段 'type'"}

            model_type = data.get("type")
            if not isinstance(model_type, (int, float)):
                return {"valid": False, "error": f"模型类型必须是数字: {type(model_type)}"}

            model_type = int(model_type)
            if model_type not in [0, 1]:
                return {"valid": False, "error": f"不支持的模型类型: {model_type}"}

            # 智能推断特征数量并动态设置
            feature_count = self._infer_feature_count(data)
            self.feature_stations = [f"STZ{i}" for i in range(1, feature_count + 1)]
            logger.info(f"动态设置特征站点: {len(self.feature_stations)}个 (STZ1-STZ{feature_count})")

            # 根据模型类型验证必需字段
            if model_type == 0:
                return self._validate_type_0_data(data)
            elif model_type == 1:
                return self._validate_type_1_data(data)

        except Exception as e:
            return {"valid": False, "error": f"数据结构验证异常: {str(e)}"}

    def _validate_type_0_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证Type 0数据结构"""
        required_fields = ["A", "Range"]
        missing_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            return {"valid": False, "error": f"Type 0模式缺少必需字段: {missing_fields}"}

        # 验证A系数
        a_values = data["A"]
        if not isinstance(a_values, list):
            return {"valid": False, "error": f"A系数必须是列表格式，当前类型: {type(a_values)}"}

        if len(a_values) != len(self.water_params):
            return {"valid": False, "error": f"A系数长度不匹配: 期望{len(self.water_params)}, 实际{len(a_values)}"}

        # 验证A系数值类型和范围
        for i, val in enumerate(a_values):
            if not isinstance(val, (int, float)):
                return {"valid": False, "error": f"A系数[{i}]不是数字类型: {type(val)}"}
            if abs(val) > 1000:  # 合理性检查
                logger.warning(f"A系数[{i}]值较大: {val}")

        # 验证Range数据
        range_values = data["Range"]
        if not isinstance(range_values, list):
            return {"valid": False, "error": f"Range数据必须是列表格式，当前类型: {type(range_values)}"}

        expected_range_length = len(self.water_params) * 2
        if len(range_values) != expected_range_length:
            return {"valid": False, "error": f"Range数据长度不匹配: 期望{expected_range_length}, 实际{len(range_values)}"}

        # 验证Range值
        for i, val in enumerate(range_values):
            if not isinstance(val, (int, float)):
                return {"valid": False, "error": f"Range数据[{i}]不是数字类型: {type(val)}"}

        # 验证min/max配对
        for i in range(0, len(range_values), 2):
            if i + 1 < len(range_values):
                min_val, max_val = range_values[i], range_values[i + 1]
                if min_val > max_val:
                    logger.warning(f"Range数据第{i//2+1}组: min({min_val}) > max({max_val})")

        return {"valid": True}

    def _validate_type_1_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证Type 1数据结构"""
        required_fields = ["w", "a", "b", "A", "Range"]
        missing_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            return {"valid": False, "error": f"Type 1模式缺少必需字段: {missing_fields}"}

        # 验证各系数数组的长度
        expected_sizes = {
            "w": len(self.feature_stations) * len(self.water_params),  # 26*11
            "a": len(self.feature_stations) * len(self.water_params),  # 26*11
            "b": len(self.water_params) * len(self.feature_stations),  # 11*26
            "A": len(self.water_params),  # 11
            "Range": len(self.water_params) * 2  # 11*2
        }

        for field, expected_size in expected_sizes.items():
            field_data = data[field]

            if not isinstance(field_data, list):
                return {"valid": False, "error": f"{field}系数必须是列表格式，当前类型: {type(field_data)}"}

            if len(field_data) != expected_size:
                return {"valid": False, "error": f"{field}系数长度不匹配: 期望{expected_size}, 实际{len(field_data)}"}

            # 验证数值类型
            for i, val in enumerate(field_data):
                if not isinstance(val, (int, float)):
                    return {"valid": False, "error": f"{field}系数[{i}]不是数字类型: {type(val)}"}

                # 合理性检查
                if field != "Range" and abs(val) > 1000:
                    logger.warning(f"{field}系数[{i}]值较大: {val}")

        # 验证Range数据的min/max配对
        range_values = data["Range"]
        for i in range(0, len(range_values), 2):
            if i + 1 < len(range_values):
                min_val, max_val = range_values[i], range_values[i + 1]
                if min_val > max_val:
                    logger.warning(f"Range数据第{i//2+1}组: min({min_val}) > max({max_val})")

        return {"valid": True}