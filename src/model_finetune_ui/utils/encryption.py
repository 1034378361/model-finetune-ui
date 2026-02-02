#!/usr/bin/env python
"""
加密管理器

复用原项目的加密逻辑，用于加密保存模型结果
仅使用旧格式（兼容C++）：[IV 16字节][加密数据]
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 导入本地工具
from .utils import ConfigManager, EnhancedLogger, performance_monitor

logger = logging.getLogger(__name__)


class EncryptionManager:
    """加密管理器"""

    def __init__(self):
        """初始化加密管理器"""
        self.output_base_dir = None

    def get_encryption_config(self) -> dict[str, Any]:
        """
        获取加密配置

        Returns:
            加密配置字典
        """
        try:
            # 使用本地配置管理器
            return ConfigManager.get_encryption_config()

        except Exception as e:
            logger.error(f"无法获取加密配置: {e}")
            raise RuntimeError("无法获取加密配置，请检查环境配置") from e

    @performance_monitor("encrypt_and_save")
    def encrypt_and_save(
        self, model_result: dict[str, Any], output_dir: str
    ) -> str | None:
        """
        加密并保存模型结果

        Args:
            model_result: 模型结果字典
            output_dir: 输出目录

        Returns:
            加密文件路径，失败返回None
        """
        try:
            # 创建输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(output_dir) / f"ui_run_{timestamp}"
            output_path.mkdir(parents=True, exist_ok=True)

            # 记录操作上下文
            EnhancedLogger.log_operation_context(
                "encrypt_and_save",
                model_type=model_result.get("type", "unknown"),
                output_dir=str(output_path),
            )

            # 获取加密配置
            encryption_config = self.get_encryption_config()

            # 验证模型结果格式
            if not self._validate_model_result(model_result):
                logger.error("模型结果格式验证失败")
                return None

            # 使用本地加密功能
            encrypted_path = encrypt_data_to_file(
                data_obj=model_result,
                password=encryption_config["password"],
                salt=encryption_config["salt"],
                iv=encryption_config["iv"],
                output_dir=str(output_path),
                logger=logger,
            )

            if encrypted_path:
                logger.info(f"模型已加密保存到: {encrypted_path}")
                EnhancedLogger.log_file_info(encrypted_path, "加密保存")
                return str(encrypted_path)
            else:
                logger.error("模型加密保存失败")
                return None

        except Exception as e:
            logger.error(f"加密保存过程中发生错误: {str(e)}")
            return None

    def _validate_model_result(self, model_result: dict[str, Any]) -> bool:
        """
        验证模型结果格式

        Args:
            model_result: 模型结果字典

        Returns:
            验证结果
        """
        try:
            # 检查必需字段
            if not isinstance(model_result, dict):
                logger.error("模型结果必须是字典格式")
                return False

            # 检查type字段
            if "type" not in model_result:
                logger.error("模型结果缺少type字段")
                return False

            model_type = model_result["type"]
            if model_type not in [0, 1]:
                logger.error(f"无效的模型类型: {model_type}")
                return False

            # 检查必需的系数字段
            if "A" not in model_result:
                logger.error("模型结果缺少A系数")
                return False

            if "Range" not in model_result:
                logger.error("模型结果缺少Range系数")
                return False

            # 如果是type 1，检查w、a、b系数
            if model_type == 1:
                required_coeffs = ["w", "a", "b"]
                for coeff in required_coeffs:
                    if coeff not in model_result:
                        logger.error(f"Type 1模型缺少{coeff}系数")
                        return False

            # 检查系数是否为列表格式
            coeff_keys = ["A", "Range"]
            if model_type == 1:
                coeff_keys.extend(["w", "a", "b"])

            for key in coeff_keys:
                if key in model_result:
                    if not isinstance(model_result[key], list):
                        logger.error(f"{key}系数必须是列表格式")
                        return False

                    if len(model_result[key]) == 0:
                        logger.error(f"{key}系数不能为空")
                        return False

            logger.info("模型结果格式验证通过")
            return True

        except Exception as e:
            logger.error(f"验证模型结果时发生错误: {str(e)}")
            return False

    def get_model_info(self, model_result: dict[str, Any]) -> dict[str, Any]:
        """
        获取模型信息摘要

        Args:
            model_result: 模型结果字典

        Returns:
            模型信息摘要
        """
        try:
            info = {
                "type": model_result.get("type", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "coefficients": {},
            }

            # 统计各系数的长度
            for key, value in model_result.items():
                if key != "type" and isinstance(value, list):
                    info["coefficients"][key] = {
                        "length": len(value),
                        "min_value": min(value) if value else None,
                        "max_value": max(value) if value else None,
                    }

            return info

        except Exception as e:
            logger.error(f"获取模型信息时发生错误: {str(e)}")
            return {"error": str(e)}

    def create_backup(
        self, model_result: dict[str, Any], output_dir: str
    ) -> str | None:
        """
        创建模型结果的备份文件（未加密）

        Args:
            model_result: 模型结果字典
            output_dir: 输出目录

        Returns:
            备份文件路径，失败返回None
        """
        try:
            import json

            # 创建备份目录
            backup_dir = Path(output_dir) / "backup"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"model_backup_{timestamp}.json"

            # 保存为JSON文件
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(model_result, f, indent=2, ensure_ascii=False)

            logger.info(f"模型备份已保存到: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"创建备份时发生错误: {str(e)}")
            return None


class LowLevelEncryptionManager:
    """底层加密管理器，使用配置文件管理加密参数"""

    def __init__(self, config_manager=None):
        """
        初始化加密管理器

        Args:
            config_manager: 系统配置管理器实例，用于获取加密参数
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager

        # 获取加密配置
        if config_manager:
            self.password = config_manager.get_system_config(
                "system", "encryption", "password"
            )
            self.salt = config_manager.get_system_config("system", "encryption", "salt")
            self.iv = config_manager.get_system_config("system", "encryption", "iv")
            self.iterations = (
                config_manager.get_system_config("system", "encryption", "iterations")
                or 100000
            )
            self.key_length = (
                config_manager.get_system_config("system", "encryption", "key_length")
                or 32
            )
        else:
            # 使用默认值
            self.password = "water_quality_analysis_key"
            self.salt = "water_quality_salt"
            self.iv = "fixed_iv_16bytes"
            self.iterations = 100000
            self.key_length = 32

        # 转换为字节
        self.password = (
            self.password.encode("utf-8")
            if isinstance(self.password, str)
            else self.password
        )
        self.salt = (
            self.salt.encode("utf-8") if isinstance(self.salt, str) else self.salt
        )
        self.iv = (self.iv.encode("utf-8") if isinstance(self.iv, str) else self.iv)[
            :16
        ]  # 确保IV是16字节

    def encrypt_data(self, data_obj: Any, output_dir: str | None = None) -> str | None:
        """
        加密数据并保存到文件

        Args:
            data_obj: 要加密的数据对象(将被转换为JSON)
            output_dir: 输出文件路径，若为None则自动生成

        Returns:
            str: 输出文件的路径，失败返回None
        """
        try:
            # 生成加密密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.key_length,
                salt=self.salt,
                iterations=self.iterations,
            )
            key = kdf.derive(self.password)

            # 准备加密器
            cipher = Cipher(algorithms.AES(key), modes.CBC(self.iv))
            encryptor = cipher.encryptor()

            # 将结果转换为JSON
            data_json = json.dumps(data_obj, ensure_ascii=False)

            # 对数据进行填充
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data_json.encode("utf-8")) + padder.finalize()

            # 加密数据
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            # 加密数据格式: [IV 16字节][加密数据] - 兼容C++
            final_data = self.iv + encrypted_data
            self.logger.info("加密完成（兼容C++格式）")

            # 如果未提供输出路径，则生成带时间戳的文件名
            if output_dir is None:
                # 从配置获取默认目录
                if self.config_manager:
                    output_dir = self.config_manager.get_system_config(
                        "system", "output", "models_dir"
                    )
                if not output_dir:
                    output_dir = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "..",
                        "output",
                        "models",
                    )
                os.makedirs(output_dir, exist_ok=True)

            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"encrypted_result_{timestamp}.bin")

            # 保存加密数据到文件
            with open(output_path, "wb") as f:
                f.write(final_data)

            self.logger.info(f"结果已加密并保存到: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"加密数据时出错: {str(e)}")
            return None

    def decrypt_file(self, file_path: str) -> dict | None:
        """
        解密文件内容

        Args:
            file_path: 加密文件路径

        Returns:
            dict: 解密后的JSON数据对象，失败时返回None
        """
        try:
            # 读取加密文件
            with open(file_path, "rb") as file:
                file_data = file.read()

            # 从文件读取IV（前16字节）
            iv = file_data[:16]
            encrypted_data = file_data[16:]

            # 从密码和盐值生成密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.key_length,
                salt=self.salt,
                iterations=self.iterations,
            )
            key = kdf.derive(self.password)

            # 解密
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()

            # 解密数据
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

            # 移除填充
            unpadder = padding.PKCS7(128).unpadder()
            decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

            # 解析JSON
            result = json.loads(decrypted_data)
            self.logger.info(f"成功解密文件: {file_path}")
            return result

        except Exception as e:
            self.logger.error(f"解密文件失败: {str(e)}")
            return None


# 保留旧的函数接口以保持向后兼容
def encrypt_data_to_file(
    data_obj,
    password=b"water_quality_analysis_key",
    salt=b"water_quality_salt",
    iv=b"fixed_iv_16bytes",
    output_dir=None,
    logger=None,
):
    """加密函数接口"""
    # 创建临时的加密管理器
    manager = LowLevelEncryptionManager()
    if logger:
        manager.logger = logger

    # 如果提供了自定义参数，更新管理器的参数
    if isinstance(password, bytes):
        manager.password = password
    if isinstance(salt, bytes):
        manager.salt = salt
    if isinstance(iv, bytes):
        manager.iv = iv[:16]

    return manager.encrypt_data(data_obj, output_dir)


def decrypt_file(
    file_path,
    password=b"water_quality_analysis_key",
    salt=b"water_quality_salt",
    logger=None,
):
    """旧的解密函数接口，保持向后兼容"""
    # 创建临时的加密管理器
    manager = LowLevelEncryptionManager()
    if logger:
        manager.logger = logger

    # 如果提供了自定义参数，更新管理器的参数
    if isinstance(password, bytes):
        manager.password = password
    if isinstance(salt, bytes):
        manager.salt = salt

    return manager.decrypt_file(file_path)
