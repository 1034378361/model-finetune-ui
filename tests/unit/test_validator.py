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

    def test_validate_data_format_type_0_valid(self, sample_a_coefficient, sample_range_data):
        """测试Type 0有效数据格式验证"""
        validator = DataValidator()

        processed_data = {
            "A": sample_a_coefficient,
            "Range": sample_range_data
        }

        result = validator.validate_data_format(processed_data, model_type=0)
        assert result is True

    def test_validate_data_format_type_1_valid(
        self,
        sample_coefficient_data,
        sample_range_data,
        sample_water_params,
        sample_feature_stations
    ):
        """测试Type 1有效数据格式验证"""
        validator = DataValidator()

        w_data = sample_coefficient_data.copy()
        a_data = sample_coefficient_data.copy()
        b_data = pd.DataFrame(
            np.random.randn(len(sample_water_params), len(sample_feature_stations)),
            index=sample_water_params,
            columns=sample_feature_stations
        )

        processed_data = {
            "w": w_data,
            "a": a_data,
            "b": b_data,
            "Range": sample_range_data
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

    def test_validate_coefficient_matrix_valid(self, sample_coefficient_data):
        """测试有效系数矩阵验证"""
        validator = DataValidator()

        result = validator._validate_coefficient_matrix(
            sample_coefficient_data,
            "test_matrix",
            expected_rows=validator.expected_water_params,
            expected_cols=validator.expected_stations
        )
        assert result is True

    def test_validate_coefficient_matrix_wrong_dimensions(self):
        """测试错误维度的系数矩阵"""
        validator = DataValidator()

        # 错误的行数
        wrong_data = pd.DataFrame(
            np.random.randn(5, 26),
            index=[f"param{i}" for i in range(5)],
            columns=[f"STZ{i}" for i in range(1, 27)]
        )

        result = validator._validate_coefficient_matrix(
            wrong_data,
            "test_matrix",
            expected_rows=validator.expected_water_params,
            expected_cols=validator.expected_stations
        )
        assert result is False

    def test_validate_range_data_valid(self, sample_range_data):
        """测试有效Range数据验证"""
        validator = DataValidator()

        result = validator._validate_range_data(sample_range_data)
        assert result is True

    def test_validate_range_data_missing_columns(self, sample_water_params):
        """测试Range数据缺少列的情况"""
        validator = DataValidator()

        # 缺少max列
        incomplete_data = pd.DataFrame(
            {"min": np.random.uniform(0, 10, len(sample_water_params))},
            index=sample_water_params
        )

        result = validator._validate_range_data(incomplete_data)
        assert result is False

    def test_validate_range_data_invalid_values(self, sample_water_params):
        """测试Range数据无效值的情况"""
        validator = DataValidator()

        # min > max的情况
        invalid_data = pd.DataFrame(
            {
                "min": np.random.uniform(50, 100, len(sample_water_params)),
                "max": np.random.uniform(0, 50, len(sample_water_params))
            },
            index=sample_water_params
        )

        result = validator._validate_range_data(invalid_data)
        assert result is False
