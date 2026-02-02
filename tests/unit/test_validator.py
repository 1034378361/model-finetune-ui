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
        assert len(validator.expected_water_params) == 11
        assert len(validator.expected_stations) == 26
        assert "turbidity" in validator.expected_water_params
        assert "STZ1" in validator.expected_stations

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

        w_data = sample_coefficient_data.copy()
        a_data = sample_coefficient_data.copy()
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

    def test_validate_coefficient_matrices_valid(
        self, sample_coefficient_data, sample_water_params, sample_feature_stations
    ):
        """测试有效系数矩阵验证"""
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

        result = validator._validate_coefficient_matrices(processed_data)
        assert result is True

    def test_validate_coefficient_matrices_empty(self):
        """测试空系数矩阵"""
        validator = DataValidator()

        processed_data = {"w": pd.DataFrame()}

        result = validator._validate_coefficient_matrices(processed_data)
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
