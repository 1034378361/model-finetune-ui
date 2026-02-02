"""
ModelProcessor单元测试
"""

import numpy as np
import pandas as pd

from src.model_finetune_ui.core.processor import ModelProcessor


class TestModelProcessor:
    """ModelProcessor测试类"""

    def test_init(self):
        """测试初始化"""
        processor = ModelProcessor()
        assert len(processor.default_water_quality_params) == 11
        assert len(processor.default_feature_stations) == 26
        assert "turbidity" in processor.default_water_quality_params
        assert "STZ1" in processor.default_feature_stations
        assert "STZ26" in processor.default_feature_stations

    def test_process_user_data_type_0(self, sample_a_coefficient, sample_range_data):
        """测试Type 0模式数据处理"""
        processor = ModelProcessor()

        processed_data = {"A": sample_a_coefficient, "Range": sample_range_data}

        result = processor.process_user_data(processed_data, model_type=0)

        assert result is not None
        assert "type" in result
        assert result["type"] == 0
        assert "A" in result
        assert "Range" in result

    def test_process_user_data_type_1(
        self,
        sample_coefficient_data,
        sample_a_coefficient,
        sample_range_data,
        sample_water_params,
        sample_feature_stations,
    ):
        """测试Type 1模式数据处理"""
        processor = ModelProcessor()

        # 创建w, a, b系数矩阵
        w_data = sample_coefficient_data.copy()
        a_data = sample_coefficient_data.copy()

        # b系数矩阵
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

        result = processor.process_user_data(processed_data, model_type=1)

        assert result is not None
        assert "type" in result
        assert result["type"] == 1
        assert "w" in result
        assert "a" in result
        assert "b" in result
        assert "A" in result
        assert "Range" in result

    def test_process_user_data_invalid_type(
        self, sample_a_coefficient, sample_range_data
    ):
        """测试无效model_type"""
        processor = ModelProcessor()

        processed_data = {"A": sample_a_coefficient, "Range": sample_range_data}

        result = processor.process_user_data(processed_data, model_type=99)
        assert result is None

    def test_validate_data_dimensions(self, sample_coefficient_data):
        """测试数据维度验证"""
        processor = ModelProcessor()

        # 测试有效数据
        result = processor.validate_data_dimensions(sample_coefficient_data)
        assert result is True

        # 测试指定形状
        result = processor.validate_data_dimensions(
            sample_coefficient_data, expected_shape=sample_coefficient_data.shape
        )
        assert result is True

        # 测试错误形状
        result = processor.validate_data_dimensions(
            sample_coefficient_data, expected_shape=(5, 5)
        )
        assert result is False
