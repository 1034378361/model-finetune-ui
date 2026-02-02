"""
完整工作流集成测试
"""

import numpy as np
import pandas as pd

from src.model_finetune_ui.core.processor import ModelProcessor
from src.model_finetune_ui.utils.template_generator import TemplateGenerator
from src.model_finetune_ui.utils.validator import DataValidator


class TestFullWorkflow:
    """完整工作流集成测试"""

    def test_type_0_full_workflow(
        self, sample_a_coefficient, sample_range_data, temp_dir
    ):
        """测试Type 0完整工作流"""
        # 初始化组件
        processor = ModelProcessor()
        validator = DataValidator()

        # 准备数据
        processed_data = {"A": sample_a_coefficient, "Range": sample_range_data}

        # 验证数据格式
        assert validator.validate_data_format(processed_data, model_type=0) is True

        # 处理数据
        result = processor.process_user_data(processed_data, model_type=0)

        # 验证结果
        assert result is not None
        assert result["type"] == 0
        assert "A" in result
        assert "Range" in result

    def test_type_1_full_workflow(
        self,
        sample_coefficient_data,
        sample_a_coefficient,
        sample_range_data,
        sample_water_params,
        sample_feature_stations,
        temp_dir,
    ):
        """测试Type 1完整工作流"""
        # 初始化组件
        processor = ModelProcessor()
        validator = DataValidator()

        # 准备数据
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

        # 验证数据格式
        assert validator.validate_data_format(processed_data, model_type=1) is True

        # 处理数据
        result = processor.process_user_data(processed_data, model_type=1)

        # 验证结果
        assert result is not None
        assert result["type"] == 1
        assert "w" in result
        assert "a" in result
        assert "b" in result
        assert "A" in result
        assert "Range" in result

    def test_template_generation_workflow(self):
        """测试模板生成工作流"""
        generator = TemplateGenerator()

        # 测试Type 0模板生成
        type_0_templates = generator.get_required_templates(0)
        for template_type in type_0_templates:
            if template_type == "Range":
                template_content = generator.generate_range_template()
            else:
                template_content = generator.generate_coefficient_template(
                    template_type
                )

            assert isinstance(template_content, bytes)
            assert len(template_content) > 0

        # 测试Type 1模板生成
        type_1_templates = generator.get_required_templates(1)
        for template_type in type_1_templates:
            if template_type == "Range":
                template_content = generator.generate_range_template()
            else:
                template_content = generator.generate_coefficient_template(
                    template_type
                )

            assert isinstance(template_content, bytes)
            assert len(template_content) > 0

    def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        processor = ModelProcessor()
        validator = DataValidator()

        # 测试空数据
        empty_data = {}
        assert validator.validate_data_format(empty_data, model_type=0) is False
        result = processor.process_user_data(empty_data, model_type=0)
        assert result is None

        # 测试无效model_type
        processed_data = {"A": pd.DataFrame(), "Range": pd.DataFrame()}
        result = processor.process_user_data(processed_data, model_type=99)
        assert result is None
