"""
解密工作流集成测试
"""

import json

import numpy as np
import pandas as pd

from src.model_finetune_ui.utils.decryption import DecryptionManager


class TestDecryptWorkflow:
    """解密工作流集成测试"""

    def test_full_decrypt_workflow_type_0(self, temp_dir):
        """测试Type 0完整解密工作流"""
        decryptor = DecryptionManager()

        # 创建Type 0测试数据
        test_data = {
            "type": 0,
            "A": [-1.0, 0.5, 1.2, -0.3, 0.8, 1.5, -0.7, 0.9, 1.1, -0.4, 1.3],
            "Range": [
                0.5, 10.5, 2.0, 15.0, 1.0, 8.0, 3.0, 20.0, 0.8, 12.0,
                2.5, 18.0, 1.5, 9.0, 4.0, 25.0, 0.3, 6.0, 3.5, 22.0,
                1.8, 14.0
            ]
        }

        # 创建临时bin文件（JSON格式用于测试）
        bin_file = temp_dir / "test_model_type0.bin"
        with open(bin_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 执行完整工作流
        # 1. 解密文件
        decrypted_data = decryptor.decrypt_bin_file(str(bin_file))
        assert decrypted_data is not None
        assert decrypted_data["type"] == 0

        # 2. 解析为CSV格式
        csv_data = decryptor.parse_to_csv_format(decrypted_data)
        assert len(csv_data) == 2  # A_coefficients 和 range_data

        # 3. 生成CSV文件
        csv_files = decryptor.generate_csv_files(csv_data)
        assert len(csv_files) == 2

        # 验证生成的CSV文件内容
        assert "A_coefficients.csv" in csv_files
        assert "range_data.csv" in csv_files

        # 验证A系数CSV
        a_csv = pd.read_csv(io.BytesIO(csv_files["A_coefficients.csv"]), index_col=0)
        assert a_csv.shape == (11, 1)
        assert list(a_csv.index) == decryptor.water_params
        assert a_csv.iloc[0, 0] == -1.0  # 第一个A系数

        # 验证Range数据CSV
        range_csv = pd.read_csv(io.BytesIO(csv_files["range_data.csv"]), index_col=0)
        assert range_csv.shape == (11, 2)
        assert list(range_csv.columns) == ["min", "max"]

    def test_full_decrypt_workflow_type_1(self, temp_dir):
        """测试Type 1完整解密工作流"""
        decryptor = DecryptionManager()

        # 创建Type 1测试数据
        w_size = 26 * 11  # 特征 × 参数
        a_size = 26 * 11  # 特征 × 参数
        b_size = 11 * 26  # 参数 × 特征
        range_size = 11 * 2  # 参数 × 2

        test_data = {
            "type": 1,
            "w": np.random.randn(w_size).tolist(),
            "a": np.random.randn(a_size).tolist(),
            "b": np.random.randn(b_size).tolist(),
            "A": np.random.uniform(-2, 2, 11).tolist(),
            "Range": np.random.uniform(0, 100, range_size).tolist()
        }

        # 创建临时bin文件
        bin_file = temp_dir / "test_model_type1.bin"
        with open(bin_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 执行完整工作流
        # 1. 解密文件
        decrypted_data = decryptor.decrypt_bin_file(str(bin_file))
        assert decrypted_data is not None
        assert decrypted_data["type"] == 1

        # 2. 解析为CSV格式
        csv_data = decryptor.parse_to_csv_format(decrypted_data)
        assert len(csv_data) == 5  # w, a, b, A, range

        # 3. 生成CSV文件
        csv_files = decryptor.generate_csv_files(csv_data)
        assert len(csv_files) == 5

        # 验证所有文件都存在
        expected_files = [
            "w_coefficients.csv",
            "a_coefficients.csv",
            "b_coefficients.csv",
            "A_coefficients.csv",
            "range_data.csv"
        ]
        for filename in expected_files:
            assert filename in csv_files

        # 验证各CSV文件的维度
        w_csv = pd.read_csv(io.BytesIO(csv_files["w_coefficients.csv"]), index_col=0)
        assert w_csv.shape == (26, 11)  # 特征 × 参数

        a_csv = pd.read_csv(io.BytesIO(csv_files["a_coefficients.csv"]), index_col=0)
        assert a_csv.shape == (26, 11)  # 特征 × 参数

        b_csv = pd.read_csv(io.BytesIO(csv_files["b_coefficients.csv"]), index_col=0)
        assert b_csv.shape == (11, 26)  # 参数 × 特征

        A_csv = pd.read_csv(io.BytesIO(csv_files["A_coefficients.csv"]), index_col=0)
        assert A_csv.shape == (11, 1)   # 参数 × 1

        range_csv = pd.read_csv(io.BytesIO(csv_files["range_data.csv"]), index_col=0)
        assert range_csv.shape == (11, 2)  # 参数 × 2

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
        with open(corrupted_file, 'wb') as f:
            f.write(b"corrupted binary data")

        result = decryptor.decrypt_bin_file(str(corrupted_file))
        # 简化解密也应该失败
        assert result is None

    def test_decrypt_invalid_json_structure(self, temp_dir):
        """测试解密无效JSON结构的文件"""
        decryptor = DecryptionManager()

        # 创建无效结构的JSON文件
        invalid_data = {"invalid": "structure"}

        invalid_file = temp_dir / "invalid.bin"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)

        # 解密应该失败，因为数据验证不通过
        decrypted_data = decryptor.decrypt_bin_file(str(invalid_file))
        assert decrypted_data is None  # 验证失败，返回None

    def test_roundtrip_workflow_simulation(self, temp_dir):
        """测试完整往返工作流模拟（加密→解密）"""
        decryptor = DecryptionManager()

        # 模拟从加密模式生成的数据结构
        original_data = {
            "type": 0,
            "A": [-1.0] * 11,  # A系数默认为-1
            "Range": []
        }

        # 添加Range数据（min/max交替）
        for i in range(11):
            original_data["Range"].extend([float(i), float(i + 10)])

        # 保存为bin文件
        bin_file = temp_dir / "roundtrip_test.bin"
        with open(bin_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f)

        # 执行解密和解析
        decrypted_data = decryptor.decrypt_bin_file(str(bin_file))
        csv_data = decryptor.parse_to_csv_format(decrypted_data)
        csv_files = decryptor.generate_csv_files(csv_data)

        # 验证A系数文件
        a_csv = pd.read_csv(io.BytesIO(csv_files["A_coefficients.csv"]), index_col=0)
        assert (a_csv["A"] == -1.0).all()  # 所有A系数都应该是-1

        # 验证Range数据文件
        range_csv = pd.read_csv(io.BytesIO(csv_files["range_data.csv"]), index_col=0)
        # 检查min/max值的模式
        for i in range(11):
            assert range_csv.loc[decryptor.water_params[i], "min"] == float(i)
            assert range_csv.loc[decryptor.water_params[i], "max"] == float(i + 10)


# 添加io导入（修复测试代码）
import io
