"""
DecryptionManager单元测试
"""

import json

import pandas as pd

from src.model_finetune_ui.utils.decryption import DecryptionManager


class TestDecryptionManager:
    """DecryptionManager测试类"""

    def test_init(self):
        """测试初始化"""
        decryptor = DecryptionManager()
        assert len(decryptor.water_params) == 11
        assert len(decryptor.feature_stations) == 26
        assert "turbidity" in decryptor.water_params
        assert "STZ1" in decryptor.feature_stations

    def test_get_decryption_config(self):
        """测试获取解密配置"""
        decryptor = DecryptionManager()
        config = decryptor.get_decryption_config()

        assert isinstance(config, dict)
        assert "password" in config
        assert "salt" in config
        assert "iv" in config

    def test_simple_decrypt_valid_json(self, temp_dir):
        """测试简化解密功能（有效JSON文件）"""
        decryptor = DecryptionManager()

        # 创建测试数据
        test_data = {
            "type": 0,
            "A": [1.0, 1.5, -0.5, 0.8, 1.2, -0.3, 0.9, 1.1, 0.7, -0.2, 1.3],
            "Range": [0.0, 10.0, 5.0, 50.0, 2.0, 20.0, 1.0, 15.0, 3.0, 25.0, 0.5, 8.0, 4.0, 30.0, 1.5, 12.0, 2.5, 18.0, 0.8, 6.0, 3.5, 22.0]
        }

        # 写入临时文件
        test_file = temp_dir / "test_model.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 测试解密
        result = decryptor._simple_decrypt(str(test_file))

        assert result is not None
        assert result["type"] == 0
        assert "A" in result
        assert "Range" in result

    def test_parse_type_0_data(self):
        """测试Type 0数据解析"""
        decryptor = DecryptionManager()

        test_data = {
            "type": 0,
            "A": [1.0, 1.5, -0.5, 0.8, 1.2, -0.3, 0.9, 1.1, 0.7, -0.2, 1.3],
            "Range": [0.0, 10.0, 5.0, 50.0, 2.0, 20.0, 1.0, 15.0, 3.0, 25.0, 0.5, 8.0, 4.0, 30.0, 1.5, 12.0, 2.5, 18.0, 0.8, 6.0, 3.5, 22.0]
        }

        csv_data = decryptor._parse_type_0_data(test_data)

        assert "A_coefficients" in csv_data
        assert "range_data" in csv_data

        # 检查A系数DataFrame
        a_df = csv_data["A_coefficients"]
        assert a_df.shape == (11, 1)
        assert list(a_df.index) == decryptor.water_params
        assert list(a_df.columns) == ["A"]

        # 检查Range数据DataFrame
        range_df = csv_data["range_data"]
        assert range_df.shape == (11, 2)
        assert list(range_df.index) == decryptor.water_params
        assert list(range_df.columns) == ["min", "max"]

    def test_parse_type_1_data(self):
        """测试Type 1数据解析"""
        decryptor = DecryptionManager()

        # 创建Type 1测试数据
        w_size = len(decryptor.feature_stations) * len(decryptor.water_params)
        a_size = len(decryptor.feature_stations) * len(decryptor.water_params)
        b_size = len(decryptor.water_params) * len(decryptor.feature_stations)
        range_size = len(decryptor.water_params) * 2

        test_data = {
            "type": 1,
            "w": [1.0] * w_size,
            "a": [0.5] * a_size,
            "b": [-0.2] * b_size,
            "A": [-1.0] * len(decryptor.water_params),
            "Range": list(range(range_size))  # 0, 1, 2, 3, ...
        }

        csv_data = decryptor._parse_type_1_data(test_data)

        assert "w_coefficients" in csv_data
        assert "a_coefficients" in csv_data
        assert "b_coefficients" in csv_data
        assert "A_coefficients" in csv_data
        assert "range_data" in csv_data

        # 检查各DataFrame的维度
        assert csv_data["w_coefficients"].shape == (26, 11)  # 特征x参数
        assert csv_data["a_coefficients"].shape == (26, 11)  # 特征x参数
        assert csv_data["b_coefficients"].shape == (11, 26)  # 参数x特征
        assert csv_data["A_coefficients"].shape == (11, 1)   # 参数x1
        assert csv_data["range_data"].shape == (11, 2)       # 参数x2

    def test_reshape_to_matrix(self):
        """测试矩阵重塑功能"""
        decryptor = DecryptionManager()

        # 测试正确的数据长度
        flat_list = list(range(12))  # [0, 1, 2, 3, ..., 11]
        matrix = decryptor._reshape_to_matrix(flat_list, 3, 4)

        expected = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
        assert matrix == expected

        # 测试错误的数据长度
        wrong_list = list(range(10))  # 长度不匹配
        matrix = decryptor._reshape_to_matrix(wrong_list, 3, 4)
        assert matrix == []  # 应该返回空列表

    def test_generate_csv_files(self):
        """测试CSV文件生成"""
        decryptor = DecryptionManager()

        # 创建测试DataFrame
        test_data = {
            "A_coefficients": pd.DataFrame(
                {"A": [-1.0] * 11},
                index=decryptor.water_params
            ),
            "range_data": pd.DataFrame(
                {"min": [0.0] * 11, "max": [10.0] * 11},
                index=decryptor.water_params
            )
        }

        csv_files = decryptor.generate_csv_files(test_data)

        assert len(csv_files) == 2
        assert "A_coefficients.csv" in csv_files
        assert "range_data.csv" in csv_files

        # 检查CSV内容
        for filename, content in csv_files.items():
            assert isinstance(content, bytes)
            assert len(content) > 0

            # 验证CSV能正确解析
            csv_str = content.decode('utf-8')
            lines = csv_str.strip().split('\n')
            assert len(lines) > 1  # 至少有头部和数据行

    def test_parse_to_csv_format_invalid_type(self):
        """测试不支持的模型类型"""
        decryptor = DecryptionManager()

        invalid_data = {"type": 99}
        result = decryptor.parse_to_csv_format(invalid_data)

        assert result == {}

    def test_parse_range_data_wrong_size(self):
        """测试Range数据大小不匹配"""
        decryptor = DecryptionManager()

        # Range数据大小不正确
        wrong_data = {"Range": [1.0, 2.0, 3.0]}  # 太少的数据
        result = decryptor._parse_range_data(wrong_data)

        assert result == {}  # 应该返回空字典
