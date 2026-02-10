"""Unit tests for hex-reverse encryption/decryption."""

import json
import os

import pytest

from src.model_finetune_ui.utils.decryption import DecryptionManager
from src.model_finetune_ui.utils.encryption import EncryptionManager


class TestHexReverseEncryption:
    """HexReverseEncryption tests"""

    def test_hex_reverse_encrypt_type_0(self, temp_dir):
        """Test hex-reverse encryption for Type 0 model data"""
        # Arrange
        encryptor = EncryptionManager()
        encryptor.encryption_method = "hex_reverse"
        model_data = {
            "type": 0,
            "A": [-1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }

        # Act
        result_path = encryptor.encrypt_and_save(model_data, temp_dir)

        # Assert
        assert result_path is not None
        assert os.path.exists(result_path)

        # Verify file content is pure hex text
        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert all(c in "0123456789abcdef\n" for c in content.lower())

    def test_hex_reverse_encrypt_type_1(self, temp_dir):
        """Test hex-reverse encryption for Type 1 model data"""
        # Arrange
        encryptor = EncryptionManager()
        encryptor.encryption_method = "hex_reverse"
        model_data = {
            "type": 1,
            "w": [1.0] * 26,
            "a": [0.5] * 11,
            "b": [0.1] * 11,
            "A": [-1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }

        # Act
        result_path = encryptor.encrypt_and_save(model_data, temp_dir)

        # Assert
        assert result_path is not None
        assert os.path.exists(result_path)

    def test_default_encryption_method_is_aes(self):
        """Test that default encryption method is AES"""
        # Arrange & Act
        encryptor = EncryptionManager()

        # Assert
        assert encryptor.encryption_method == "aes"


class TestHexReverseDecryption:
    """HexReverseDecryption tests"""

    def test_detect_hex_reverse_format(self):
        """Test detection of hex-reverse format"""
        # Arrange
        hex_data = b"48656c6c6f"  # Pure hex characters

        # Act
        detected_format = DecryptionManager._detect_bin_format(hex_data)

        # Assert
        assert detected_format == "hex_reverse"

    def test_detect_aes_format(self):
        """Test detection of AES format"""
        # Arrange
        binary_data = b"\x00\x01\x02\xff\xfe"  # Non-hex bytes

        # Act
        detected_format = DecryptionManager._detect_bin_format(binary_data)

        # Assert
        assert detected_format == "aes"

    def test_decrypt_hex_reverse_file(self, temp_dir):
        """Test decryption of hex-reverse BIN file"""
        # Arrange
        # Use correct data format: 11 A coefficients, 22 Range values (11 min/max pairs)
        original_data = {
            "type": 0,
            "A": [1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }

        # Manually create hex-reverse BIN file
        json_str = json.dumps(original_data, ensure_ascii=False)
        utf8_bytes = json_str.encode("utf-8")
        hex_str = utf8_bytes.hex()
        reversed_hex = hex_str[::-1]

        bin_path = temp_dir / "test_hex_reverse.bin"
        with open(bin_path, "w", encoding="utf-8") as f:
            f.write(reversed_hex)

        # Act
        decryptor = DecryptionManager()
        result = decryptor.decrypt_bin_file(bin_path)

        # Assert
        assert result is not None
        assert result["type"] == original_data["type"]
        assert result["A"] == original_data["A"]
        assert result["Range"] == original_data["Range"]
