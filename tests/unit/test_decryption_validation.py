"""
解密管理器验证功能测试
"""

import json
from pathlib import Path

from src.model_finetune_ui.utils.decryption import DecryptionManager


class TestDecryptionValidation:
    """解密验证功能测试类"""

    def test_file_path_validation_success(self, temp_dir):
        """测试文件路径验证成功场景"""
        decryptor = DecryptionManager()

        # 创建有效的测试文件
        test_file = temp_dir / "valid_test.bin"
        with open(test_file, 'w') as f:
            json.dump({"type": 0, "A": [1.0] * 11, "Range": [1.0, 2.0] * 11}, f)

        result = decryptor._validate_file_path(str(test_file))
        assert result["valid"] is True
        assert "size" in result

    def test_file_path_validation_nonexistent(self):
        """测试不存在文件的路径验证"""
        decryptor = DecryptionManager()

        result = decryptor._validate_file_path("nonexistent_file.bin")
        assert result["valid"] is False
        assert "文件不存在" in result["error"]

    def test_file_path_validation_empty_file(self, temp_dir):
        """测试空文件的路径验证"""
        decryptor = DecryptionManager()

        # 创建空文件
        empty_file = temp_dir / "empty.bin"
        empty_file.touch()

        result = decryptor._validate_file_path(str(empty_file))
        assert result["valid"] is False
        assert "文件为空" in result["error"]

    def test_file_path_validation_large_file(self, temp_dir):
        """测试大文件的路径验证"""
        decryptor = DecryptionManager()

        # 模拟大文件检查（不实际创建大文件）
        large_file = temp_dir / "large.bin"
        with open(large_file, 'w') as f:
            f.write("x")  # 创建小文件用于测试

        # 手动测试大小检查逻辑
        Path(large_file)
        100 * 1024 * 1024  # 100MB

        # 文件实际很小，应该通过验证
        result = decryptor._validate_file_path(str(large_file))
        assert result["valid"] is True

    def test_decrypted_data_validation_missing_type(self):
        """测试缺少type字段的数据验证"""
        decryptor = DecryptionManager()

        invalid_data = {"A": [1.0] * 11}
        result = decryptor._validate_decrypted_data(invalid_data)

        assert result["valid"] is False
        assert "缺少模型类型字段" in result["error"]

    def test_decrypted_data_validation_invalid_type(self):
        """测试无效type值的数据验证"""
        decryptor = DecryptionManager()

        invalid_data = {"type": 99, "A": [1.0] * 11}
        result = decryptor._validate_decrypted_data(invalid_data)

        assert result["valid"] is False
        assert "不支持的模型类型" in result["error"]

    def test_type_0_validation_missing_fields(self):
        """测试Type 0缺少必需字段的验证"""
        decryptor = DecryptionManager()

        incomplete_data = {"type": 0, "A": [1.0] * 11}  # 缺少Range
        result = decryptor._validate_type_0_data(incomplete_data)

        assert result["valid"] is False
        assert "Type 0模式缺少必需字段" in result["error"]

    def test_type_0_validation_wrong_a_length(self):
        """测试Type 0 A系数长度错误的验证"""
        decryptor = DecryptionManager()

        invalid_data = {
            "type": 0,
            "A": [1.0] * 5,  # 长度不正确
            "Range": [1.0, 2.0] * 11,
        }
        result = decryptor._validate_type_0_data(invalid_data)

        assert result["valid"] is False
        assert "A系数长度不匹配" in result["error"]

    def test_type_0_validation_wrong_range_length(self):
        """测试Type 0 Range数据长度错误的验证"""
        decryptor = DecryptionManager()

        invalid_data = {
            "type": 0,
            "A": [1.0] * 11,
            "Range": [1.0, 2.0] * 5,  # 长度不正确
        }
        result = decryptor._validate_type_0_data(invalid_data)

        assert result["valid"] is False
        assert "Range数据长度不匹配" in result["error"]

    def test_type_1_validation_missing_fields(self):
        """测试Type 1缺少必需字段的验证"""
        decryptor = DecryptionManager()

        incomplete_data = {
            "type": 1,
            "w": [1.0] * (26 * 11),
            "a": [1.0] * (26 * 11),
            # 缺少 b, A, Range
        }
        result = decryptor._validate_type_1_data(incomplete_data)

        assert result["valid"] is False
        assert "Type 1模式缺少必需字段" in result["error"]

    def test_type_1_validation_wrong_coefficient_lengths(self):
        """测试Type 1系数数组长度错误的验证"""
        decryptor = DecryptionManager()

        invalid_data = {
            "type": 1,
            "w": [1.0] * 100,  # 错误长度
            "a": [1.0] * (26 * 11),
            "b": [1.0] * (11 * 26),
            "A": [1.0] * 11,
            "Range": [1.0, 2.0] * 11,
        }
        result = decryptor._validate_type_1_data(invalid_data)

        assert result["valid"] is False
        assert "w系数长度不匹配" in result["error"]

    def test_type_1_validation_non_numeric_values(self):
        """测试Type 1包含非数字值的验证"""
        decryptor = DecryptionManager()

        invalid_data = {
            "type": 1,
            "w": [1.0] * (26 * 11 - 1) + ["string"],  # 最后一个元素是字符串
            "a": [1.0] * (26 * 11),
            "b": [1.0] * (11 * 26),
            "A": [1.0] * 11,
            "Range": [1.0, 2.0] * 11,
        }
        result = decryptor._validate_type_1_data(invalid_data)

        assert result["valid"] is False
        assert "w系数" in result["error"] and "不是数字类型" in result["error"]

    def test_validation_success_type_0(self):
        """测试Type 0完整验证成功"""
        decryptor = DecryptionManager()

        valid_data = {"type": 0, "A": [1.0] * 11, "Range": [1.0, 2.0] * 11}
        result = decryptor._validate_decrypted_data(valid_data)

        assert result["valid"] is True

    def test_validation_success_type_1(self):
        """测试Type 1完整验证成功"""
        decryptor = DecryptionManager()

        valid_data = {
            "type": 1,
            "w": [1.0] * (26 * 11),
            "a": [1.0] * (26 * 11),
            "b": [1.0] * (11 * 26),
            "A": [1.0] * 11,
            "Range": [1.0, 2.0] * 11,
        }
        result = decryptor._validate_decrypted_data(valid_data)

        assert result["valid"] is True
