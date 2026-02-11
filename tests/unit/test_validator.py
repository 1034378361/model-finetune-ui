"""
DataValidator单元测试
"""

import numpy as np
import pandas as pd

from src.model_finetune_ui.utils.validator import DataValidator


class TestDataValidator:
    """DataValidator测试类"""

    def test_init(self):
        """测试初始化"""
        validator = DataValidator()
        assert validator is not None

    def test_validate_data_format_type_0_valid(
        self, sample_a_coefficient, sample_range_data
    ):
        """测试Type 0有效数据格式验证"""
        validator = DataValidator()

        processed_data = {"A": sample_a_coefficient, "Range": sample_range_data}

        result = validator.validate_data_format(processed_data, model_type=0)
        assert result is True

    def test_validate_data_format_type_1_valid(
        self,
        sample_coefficient_data,
        sample_a_coefficient,
        sample_range_data,
        sample_water_params,
        sample_feature_stations,
    ):
        """测试Type 1有效数据格式验证"""
        validator = DataValidator()

        # w/a 应为 F×P (特征×参数), sample_coefficient_data 是 P×F，需要转置
        w_data = sample_coefficient_data.T.copy()
        a_data = sample_coefficient_data.T.copy()
        # b 应为 P×F (参数×特征)
        b_data = pd.DataFrame(
            np.random.randn(len(sample_water_params), len(sample_feature_stations)),
            index=sample_water_params,
            columns=sample_feature_stations,
        )

        processed_data = {
            "w": w_data,
            "a": a_data,
            "b": b_data,
            "A": sample_a_coefficient,
            "Range": sample_range_data,
        }

        result = validator.validate_data_format(processed_data, model_type=1)
        assert result is True

    def test_validate_data_format_missing_files(self, sample_range_data):
        """测试缺少文件的情况"""
        validator = DataValidator()

        # Type 0缺少A文件
        processed_data = {"Range": sample_range_data}
        result = validator.validate_data_format(processed_data, model_type=0)
        assert result is False

        # Type 1缺少w文件
        processed_data = {"Range": sample_range_data}
        result = validator.validate_data_format(processed_data, model_type=1)
        assert result is False

    def test_validate_matrix_basic_valid(
        self, sample_coefficient_data, sample_water_params, sample_feature_stations
    ):
        """测试有效系数矩阵基本格式验证"""
        validator = DataValidator()

        b_data = pd.DataFrame(
            np.random.randn(len(sample_water_params), len(sample_feature_stations)),
            index=sample_water_params,
            columns=sample_feature_stations,
        )

        processed_data = {
            "w": sample_coefficient_data,
            "a": sample_coefficient_data.copy(),
            "b": b_data,
        }

        result = validator._validate_matrix_basic(processed_data, ["w", "a", "b"])
        assert result is True

    def test_validate_matrix_basic_empty(self):
        """测试空系数矩阵"""
        validator = DataValidator()

        processed_data = {"w": pd.DataFrame()}

        result = validator._validate_matrix_basic(processed_data, ["w"])
        assert result is False

    def test_validate_range_data_valid(self, sample_range_data):
        """测试有效Range数据验证"""
        validator = DataValidator()

        result = validator._validate_range_data(sample_range_data)
        assert result is True

    def test_validate_range_data_empty(self):
        """测试空Range数据"""
        validator = DataValidator()

        empty_data = pd.DataFrame()
        result = validator._validate_range_data(empty_data)
        assert result is False

    def test_validate_a_coefficient_valid(self, sample_a_coefficient):
        """测试有效A系数验证"""
        validator = DataValidator()

        result = validator._validate_a_coefficient(sample_a_coefficient)
        assert result is True

    def test_validate_a_coefficient_empty(self):
        """测试空A系数"""
        validator = DataValidator()

        empty_data = pd.DataFrame()
        result = validator._validate_a_coefficient(empty_data)
        assert result is False

    def test_validate_cross_file_dimensions_type1_valid(
        self, sample_water_params, sample_feature_stations
    ):
        """测试Type 1维度一致性验证 - 有效数据"""
        validator = DataValidator()
        p = len(sample_water_params)    # 参数数 = 11
        f = len(sample_feature_stations)  # 特征数 = 26

        processed_data = {
            "w": pd.DataFrame(np.random.randn(f, p)),   # F×P
            "a": pd.DataFrame(np.random.randn(f, p)),   # F×P
            "b": pd.DataFrame(np.random.randn(p, f)),   # P×F
            "A": pd.DataFrame(np.random.randn(p, 1)),   # P×1
            "Range": pd.DataFrame(np.random.randn(p, 2)),  # P×2
        }

        result = validator._validate_cross_file_dimensions(processed_data, model_type=1)
        assert result is True

    def test_validate_cross_file_dimensions_type1_arbitrary_size(self):
        """测试Type 1维度一致性验证 - 任意尺寸"""
        validator = DataValidator()
        p = 20   # 参数数
        f = 100  # 特征数

        processed_data = {
            "w": pd.DataFrame(np.random.randn(f, p)),
            "a": pd.DataFrame(np.random.randn(f, p)),
            "b": pd.DataFrame(np.random.randn(p, f)),
            "A": pd.DataFrame(np.random.randn(p, 1)),
            "Range": pd.DataFrame(np.random.randn(p, 2)),
        }

        result = validator._validate_cross_file_dimensions(processed_data, model_type=1)
        assert result is True

    def test_validate_cross_file_dimensions_type1_mismatch(self):
        """测试Type 1维度不一致"""
        validator = DataValidator()

        # w 和 a 维度不一致
        processed_data = {
            "w": pd.DataFrame(np.random.randn(26, 11)),
            "a": pd.DataFrame(np.random.randn(26, 10)),  # 列数不同
            "b": pd.DataFrame(np.random.randn(11, 26)),
            "A": pd.DataFrame(np.random.randn(11, 1)),
            "Range": pd.DataFrame(np.random.randn(11, 2)),
        }

        result = validator._validate_cross_file_dimensions(processed_data, model_type=1)
        assert result is False

    def test_validate_cross_file_dimensions_type0_valid(self):
        """测试Type 0维度一致性验证"""
        validator = DataValidator()
        p = 15  # 任意参数数

        processed_data = {
            "A": pd.DataFrame(np.random.randn(p, 1)),
            "Range": pd.DataFrame(np.random.randn(p, 2)),
        }

        result = validator._validate_cross_file_dimensions(processed_data, model_type=0)
        assert result is True

    def test_validate_cross_file_dimensions_type0_mismatch(self):
        """测试Type 0维度不一致"""
        validator = DataValidator()

        processed_data = {
            "A": pd.DataFrame(np.random.randn(11, 1)),
            "Range": pd.DataFrame(np.random.randn(9, 2)),  # 行数不同
        }

        result = validator._validate_cross_file_dimensions(processed_data, model_type=0)
        assert result is False
