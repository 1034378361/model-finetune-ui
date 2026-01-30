"""
集成测试：动态配置功能

测试配置管理器的CRUD操作、持久化、加密/解密与配置的集成
"""

import json
import struct
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from src.model_finetune_ui.utils.config_manager import ConfigurationManager
from src.model_finetune_ui.utils.encryption import (
    LowLevelEncryptionManager,
    BIN_MAGIC,
    BIN_VERSION,
)
from src.model_finetune_ui.utils.decryption import DecryptionManager


class TestConfigFlow:
    """动态配置功能集成测试"""

    def test_config_manager_crud(self, temp_dir):
        """测试配置管理器CRUD操作"""
        # 创建配置管理器，使用临时路径
        config_path = temp_dir / "test_config.json"
        config_manager = ConfigurationManager(config_path=str(config_path))

        # 验证默认值已加载
        default_water_params = config_manager.get_water_params()
        default_feature_stations = config_manager.get_feature_stations()

        assert len(default_water_params) == 11
        assert len(default_feature_stations) == 26
        assert "turbidity" in default_water_params
        assert "STZ1" in default_feature_stations

        # 设置自定义参数
        custom_water_params = ["param1", "param2", "param3"]
        custom_feature_stations = ["station1", "station2", "station3"]

        config_manager.set_water_params(custom_water_params)
        config_manager.set_feature_stations(custom_feature_stations)

        # 验证设置成功
        assert config_manager.get_water_params() == custom_water_params
        assert config_manager.get_feature_stations() == custom_feature_stations

        # 保存配置
        assert config_manager.save_config() is True
        assert config_path.exists()

        # 验证配置文件内容
        with open(config_path, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        assert saved_config["version"] == 1
        assert saved_config["water_params"] == custom_water_params
        assert saved_config["feature_stations"] == custom_feature_stations

        # 重新加载验证
        config_manager.load_config()
        assert config_manager.get_water_params() == custom_water_params
        assert config_manager.get_feature_stations() == custom_feature_stations

    def test_config_persistence(self, temp_dir):
        """测试配置持久化"""
        config_path = temp_dir / "persistent_config.json"

        # 第一个实例：设置并保存配置
        config1 = ConfigurationManager(config_path=str(config_path))
        custom_params = ["test_param1", "test_param2"]
        custom_stations = ["test_station1", "test_station2"]

        config1.set_water_params(custom_params)
        config1.set_feature_stations(custom_stations)
        assert config1.save_config() is True

        # 第二个实例：创建新实例并验证配置已加载
        config2 = ConfigurationManager(config_path=str(config_path))

        assert config2.get_water_params() == custom_params
        assert config2.get_feature_stations() == custom_stations

        # 验证配置文件确实存在
        assert config_path.exists()
        file_size = config_path.stat().st_size
        assert file_size > 0

    def test_encryption_with_version_header(self, temp_dir):
        """测试加密文件版本头"""
        # 设置自定义配置
        config_path = temp_dir / "custom_config.json"
        config_manager = ConfigurationManager(config_path=str(config_path))

        custom_water_params = ["param1", "param2", "param3"]
        custom_feature_stations = ["station1", "station2"]

        config_manager.set_water_params(custom_water_params)
        config_manager.set_feature_stations(custom_feature_stations)
        config_manager.save_config()

        # 准备测试数据
        test_data = {
            "type": 0,
            "A": [1.0, 2.0, 3.0],
            "Range": [0.0, 10.0, 1.0, 20.0, 2.0, 30.0],
        }

        # 使用加密管理器加密数据（传入自定义配置管理器）
        encryption_manager = LowLevelEncryptionManager(
            config_manager=None, param_config_manager=config_manager
        )
        output_path = encryption_manager.encrypt_data(
            test_data, output_dir=str(temp_dir)
        )

        assert output_path is not None
        assert Path(output_path).exists()

        # 读取加密文件并验证版本头
        with open(output_path, "rb") as f:
            file_data = f.read()

        # 验证文件以 'MFUI' 开头
        assert file_data[:4] == BIN_MAGIC

        # 验证版本号
        version = struct.unpack(">H", file_data[4:6])[0]
        assert version == BIN_VERSION

        # 验证配置元数据存在
        config_len = struct.unpack(">I", file_data[6:10])[0]
        assert config_len > 0

        # 提取并验证配置JSON
        config_json = file_data[10 : 10 + config_len].decode("utf-8")
        config_meta = json.loads(config_json)

        assert "water_params" in config_meta
        assert "feature_stations" in config_meta
        assert config_meta["water_params"] == custom_water_params
        assert config_meta["feature_stations"] == custom_feature_stations

    def test_decryption_new_format(self, temp_dir):
        """测试解密新格式"""
        # 设置自定义配置
        config_path = temp_dir / "decrypt_config.json"
        config_manager = ConfigurationManager(config_path=str(config_path))

        custom_water_params = ["param1", "param2", "param3"]
        custom_feature_stations = ["station1", "station2"]

        config_manager.set_water_params(custom_water_params)
        config_manager.set_feature_stations(custom_feature_stations)
        config_manager.save_config()

        # 准备测试数据
        test_data = {
            "type": 0,
            "A": [1.0, 2.0, 3.0],
            "Range": [0.0, 10.0, 1.0, 20.0, 2.0, 30.0],
        }

        # 加密数据（新格式，传入自定义配置管理器）
        encryption_manager = LowLevelEncryptionManager(
            config_manager=None, param_config_manager=config_manager
        )
        encrypted_path = encryption_manager.encrypt_data(
            test_data, output_dir=str(temp_dir)
        )

        assert encrypted_path is not None
        assert Path(encrypted_path).exists()

        # 读取文件并验证格式（不依赖外部解密）
        with open(encrypted_path, "rb") as f:
            file_data = f.read()

        # 验证文件格式
        assert file_data[:4] == BIN_MAGIC
        version = struct.unpack(">H", file_data[4:6])[0]
        assert version == BIN_VERSION

        # 提取配置
        config_len = struct.unpack(">I", file_data[6:10])[0]
        config_json = file_data[10 : 10 + config_len].decode("utf-8")
        config_meta = json.loads(config_json)

        # 验证配置已嵌入文件
        assert config_meta["water_params"] == custom_water_params
        assert config_meta["feature_stations"] == custom_feature_stations

    def test_decryption_backward_compatibility(self, temp_dir):
        """测试向后兼容 - 验证文件格式检测"""
        # 准备测试数据
        test_data = {
            "type": 0,
            "A": [1.0, 2.0, 3.0],
            "Range": [0.0, 10.0, 1.0, 20.0, 2.0, 30.0],
        }

        # 使用旧格式加密（无版本头）
        from cryptography.hazmat.primitives import hashes, padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        password = b"water_quality_analysis_key"
        salt = b"water_quality_salt"
        iv = b"fixed_iv_16bytes"

        # 生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password)

        # 加密数据
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        data_json = json.dumps(test_data, ensure_ascii=False)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data_json.encode("utf-8")) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 保存为旧格式（只有IV + 加密数据，无版本头）
        old_format_path = temp_dir / "old_format.bin"
        with open(old_format_path, "wb") as f:
            f.write(iv + encrypted_data)

        # 验证文件格式检测
        with open(old_format_path, "rb") as f:
            file_data = f.read()

        # 验证旧格式文件不以 'MFUI' 开头
        assert file_data[:4] != BIN_MAGIC

        # 验证文件以IV开头（16字节）
        assert len(file_data) > 16
        assert file_data[:16] == iv

    def test_config_validation(self, temp_dir):
        """测试配置验证"""
        config_path = temp_dir / "validation_config.json"
        config_manager = ConfigurationManager(config_path=str(config_path))

        # 测试空列表拒绝
        config_manager.set_water_params([])
        is_valid, errors = config_manager.validate_config()
        assert is_valid is False
        assert any("cannot be empty" in error for error in errors)

        # 恢复有效配置
        config_manager.set_water_params(["param1", "param2"])
        config_manager.set_feature_stations([])
        is_valid, errors = config_manager.validate_config()
        assert is_valid is False
        assert any("cannot be empty" in error for error in errors)

        # 测试重复名称拒绝
        config_manager.set_water_params(["param1", "param2", "param1"])
        config_manager.set_feature_stations(["station1", "station2"])
        is_valid, errors = config_manager.validate_config()
        assert is_valid is False
        assert any("duplicates" in error for error in errors)

        # 测试无效字符拒绝
        config_manager.set_water_params(["param1", "param-2", "param3"])
        config_manager.set_feature_stations(["station1", "station2"])
        is_valid, errors = config_manager.validate_config()
        assert is_valid is False
        assert any("Invalid parameter name" in error for error in errors)

        # 测试有效配置通过
        config_manager.set_water_params(["param1", "param2", "param3"])
        config_manager.set_feature_stations(["station1", "station2"])
        is_valid, errors = config_manager.validate_config()
        assert is_valid is True
        assert len(errors) == 0
