"""
TemplateGenerator单元测试
"""

import io

import pandas as pd

from src.model_finetune_ui.utils.template_generator import TemplateGenerator


class TestTemplateGenerator:
    """TemplateGenerator测试类"""

    def test_init(self):
        """测试初始化"""
        generator = TemplateGenerator()
        assert len(generator.water_params) == 11
        assert len(generator.stations) == 26
        assert "turbidity" in generator.water_params
        assert "STZ1" in generator.stations

    def test_generate_coefficient_template_w(self):
        """测试生成w系数模板"""
        generator = TemplateGenerator()

        template_bytes = generator.generate_coefficient_template("w")
        assert isinstance(template_bytes, bytes)

        # 将bytes转换为DataFrame验证
        df = pd.read_csv(io.BytesIO(template_bytes), index_col=0)
        assert df.shape == (11, 26)
        assert list(df.index) == generator.water_params
        assert list(df.columns) == generator.stations
        assert (df == 0.0).all().all()  # 默认值应该是0

    def test_generate_coefficient_template_a(self):
        """测试生成a系数模板"""
        generator = TemplateGenerator()

        template_bytes = generator.generate_coefficient_template("a")
        df = pd.read_csv(io.BytesIO(template_bytes), index_col=0)

        assert df.shape == (11, 26)
        assert list(df.index) == generator.water_params
        assert list(df.columns) == generator.stations

    def test_generate_coefficient_template_b(self):
        """测试生成b系数模板"""
        generator = TemplateGenerator()

        template_bytes = generator.generate_coefficient_template("b")
        df = pd.read_csv(io.BytesIO(template_bytes), index_col=0)

        assert df.shape == (11, 26)
        assert list(df.index) == generator.water_params
        assert list(df.columns) == generator.stations

    def test_generate_coefficient_template_a_single_column(self):
        """测试生成A系数模板（单列）"""
        generator = TemplateGenerator()

        template_bytes = generator.generate_coefficient_template("A")
        df = pd.read_csv(io.BytesIO(template_bytes), index_col=0)

        assert df.shape == (11, 1)
        assert list(df.index) == generator.water_params
        assert list(df.columns) == ["A"]

    def test_generate_range_template(self):
        """测试生成Range模板"""
        generator = TemplateGenerator()

        template_bytes = generator.generate_range_template()
        assert isinstance(template_bytes, bytes)

        # 将bytes转换为DataFrame验证
        df = pd.read_csv(io.BytesIO(template_bytes), index_col=0)
        assert df.shape == (11, 2)
        assert list(df.index) == generator.water_params
        assert list(df.columns) == ["min", "max"]
        assert (df == 0.0).all().all()  # 默认值应该是0

    def test_get_required_templates_type_0(self):
        """测试获取Type 0所需模板"""
        generator = TemplateGenerator()
        required = generator.get_required_templates(0)

        assert "A" in required
        assert "Range" in required
        assert len(required) == 2

    def test_get_required_templates_type_1(self):
        """测试获取Type 1所需模板"""
        generator = TemplateGenerator()
        required = generator.get_required_templates(1)

        assert "w" in required
        assert "a" in required
        assert "b" in required
        assert "Range" in required
        assert len(required) == 4

    def test_get_template_info(self):
        """测试获取模板信息"""
        generator = TemplateGenerator()
        info = generator.get_template_info()

        assert "w" in info
        assert "a" in info
        assert "b" in info
        assert "A" in info
        assert "Range" in info

        # 检查每个模板信息包含必要字段
        for template_type, template_info in info.items():
            assert "name" in template_info
            assert "filename" in template_info
            assert "description" in template_info
