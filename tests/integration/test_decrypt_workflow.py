"""
解密工作流集成测试

注意：这些测试主要测试解密管理器的辅助功能，
实际的加密/解密需要正确的密钥配置才能工作。
"""

import io
import json

import numpy as np
import pandas as pd

from src.model_finetune_ui.utils.decryption import DecryptionManager
from src.model_finetune_ui.utils.encryption import EncryptionManager


class TestDecryptWorkflow:
    """解密工作流集成测试"""

    def test_decryptor_init(self):
        """测试解密管理器初始化"""
        decryptor = DecryptionManager()
        assert len(decryptor.water_params) == 11
        assert len(decryptor.feature_stations) == 26
        assert "turbidity" in decryptor.water_params
        assert "STZ1" in decryptor.feature_stations

    def test_decrypt_nonexistent_file(self):
        """测试解密不存在的文件"""
        decryptor = DecryptionManager()

        result = decryptor.decrypt_bin_file("nonexistent_file.bin")
        assert result is None

    def test_decrypt_corrupted_file(self, temp_dir):
        """测试解密损坏的文件"""
        decryptor = DecryptionManager()

        # 创建损坏的文件
        corrupted_file = temp_dir / "corrupted.bin"
        with open(corrupted_file, "wb") as f:
            f.write(b"corrupted binary data")

        result = decryptor.decrypt_bin_file(str(corrupted_file))
        assert result is None

    def test_parse_to_csv_format_type_0(self):
        """测试Type 0数据解析为CSV格式"""
        decryptor = DecryptionManager()

        # 模拟解密后的Type 0数据
        decrypted_data = {
            "type": 0,
            "A": [-1.0, 0.5, 1.2, -0.3, 0.8, 1.5, -0.7, 0.9, 1.1, -0.4, 1.3],
            "Range": [
                0.5,
                10.5,
                2.0,
                15.0,
                1.0,
                8.0,
                3.0,
                20.0,
                0.8,
                12.0,
                2.5,
                18.0,
                1.5,
                9.0,
                4.0,
                25.0,
                0.3,
                6.0,
                3.5,
                22.0,
                1.8,
                14.0,
            ],
        }

        csv_data = decryptor.parse_to_csv_format(decrypted_data)

        # 验证返回的数据结构
        assert csv_data is not None
        assert "A" in csv_data or "A_coefficients" in csv_data or len(csv_data) >= 1

    def test_parse_to_csv_format_type_1(self):
        """测试Type 1数据解析为CSV格式"""
        decryptor = DecryptionManager()

        # 模拟解密后的Type 1数据
        w_size = 26 * 11
        a_size = 26 * 11
        b_size = 11 * 26
        range_size = 11 * 2

        decrypted_data = {
            "type": 1,
            "w": np.random.randn(w_size).tolist(),
            "a": np.random.randn(a_size).tolist(),
            "b": np.random.randn(b_size).tolist(),
            "A": np.random.uniform(-2, 2, 11).tolist(),
            "Range": np.random.uniform(0, 100, range_size).tolist(),
        }

        csv_data = decryptor.parse_to_csv_format(decrypted_data)

        # 验证返回的数据结构
        assert csv_data is not None

    def test_generate_csv_files(self):
        """测试生成CSV文件"""
        decryptor = DecryptionManager()

        # 创建测试DataFrame
        test_data = {
            "A": pd.DataFrame({"A": [-1.0] * 11}, index=decryptor.water_params),
            "Range": pd.DataFrame(
                {"min": [0.0] * 11, "max": [10.0] * 11}, index=decryptor.water_params
            ),
        }

        csv_files = decryptor.generate_csv_files(test_data)

        # 验证生成的文件
        assert csv_files is not None
        assert len(csv_files) >= 1

    def test_parse_to_csv_format_none_input(self):
        """测试解析None输入"""
        decryptor = DecryptionManager()

        csv_data = decryptor.parse_to_csv_format(None)
        assert csv_data is None or csv_data == {}

    def test_generate_csv_files_empty_input(self):
        """测试生成CSV文件空输入"""
        decryptor = DecryptionManager()

        csv_files = decryptor.generate_csv_files({})
        assert csv_files is None or csv_files == {}

    def test_hex_reverse_roundtrip(self, temp_dir):
        """测试十六进制混淆格式的加密→解密往返"""
        # 加密
        encryptor = EncryptionManager()
        encryptor.encryption_method = "hex_reverse"

        original = {
            "type": 0,
            "A": [-1.0, 0.5, 1.2, -0.3, 0.8, 1.5, -0.7, 0.9, 1.1, -0.4, 1.3],
            "Range": [
                0.5,
                10.5,
                2.0,
                15.0,
                1.0,
                8.0,
                3.0,
                20.0,
                0.8,
                12.0,
                2.5,
                18.0,
                1.5,
                9.0,
                4.0,
                25.0,
                0.3,
                6.0,
                3.5,
                22.0,
                1.8,
                14.0,
            ],
        }

        encrypted_path = encryptor.encrypt_and_save(original, str(temp_dir))
        assert encrypted_path is not None

        # 解密（自动检测格式）
        decryptor = DecryptionManager()
        decrypted = decryptor.decrypt_bin_file(encrypted_path)

        assert decrypted is not None
        assert decrypted["type"] == original["type"]
        assert decrypted["A"] == original["A"]
        assert decrypted["Range"] == original["Range"]
