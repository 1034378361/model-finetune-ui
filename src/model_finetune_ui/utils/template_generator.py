"""
模板文件生成器

用于生成各种因子文件的空白CSV模板，包含正确的行列名称。
"""

import io

import pandas as pd

from ..config import UIConfig


class TemplateGenerator:
    """CSV模板文件生成器，为不同配置类型生成标准格式的CSV模板文件。

    支持生成W、A、B、校准因子矩阵模板和Range数据模板，
    所有模板都包含正确的行列标题和默认值。
    """

    def __init__(self):
        self.water_params = UIConfig.WATER_QUALITY_PARAMS
        self.stations = UIConfig.FEATURE_STATIONS

    def generate_coefficient_template(self, coeff_type: str) -> bytes:
        """
        生成因子文件模板

        Args:
            coeff_type: 因子类型 ('w', 'a', 'b', 'A')

        Returns:
            bytes: CSV文件内容
        """
        if coeff_type in ['w', 'a']:
            # 影响因子w、影响因子a：特征 × 水质参数 (需要转置)
            df = pd.DataFrame(
                0.0, index=self.stations, columns=self.water_params  # 填充默认值0
            )
        elif coeff_type == 'b':
            # 调节因子b：水质参数 × 特征 (不需要转置)
            df = pd.DataFrame(
                0.0, index=self.water_params, columns=self.stations  # 填充默认值0
            )
        elif coeff_type == 'A':
            # 校准因子A：水质参数 × 校准值 (不需要转置)
            df = pd.DataFrame(
                -1.0, index=self.water_params, columns=['A']  # 填充默认值-1
            )
        else:
            raise ValueError(f"不支持的因子类型: {coeff_type}")

        # 转换为CSV字节流
        output = io.StringIO()
        df.to_csv(output, index=True, encoding='utf-8')
        return output.getvalue().encode('utf-8')

    def generate_range_template(self, sample_size: int = 10) -> bytes:
        """
        生成Range数据文件模板

        Args:
            sample_size: 保留参数兼容性，但Range数据是固定格式

        Returns:
            bytes: CSV文件内容
        """
        # Range数据格式：水质参数 × min/max
        df = pd.DataFrame(
            0.0,  # 填充默认值0
            index=self.water_params,
            columns=["min", "max"],  # 最小值和最大值
        )

        # 转换为CSV字节流
        output = io.StringIO()
        df.to_csv(output, index=True, encoding='utf-8')
        return output.getvalue().encode('utf-8')

    def get_template_info(self) -> dict[str, dict]:
        """
        获取所有模板文件信息

        Returns:
            Dict: 模板文件信息
        """
        return {
            'w': {
                'name': '影响因子w模板',
                'filename': 'factors_w_template.csv',
                'description': '影响因子w矩阵模板，行为特征编号，列为水质参数',
            },
            'a': {
                'name': '影响因子a模板',
                'filename': 'factors_a_template.csv',
                'description': '影响因子a矩阵模板，行为特征编号，列为水质参数',
            },
            'b': {
                'name': '调节因子b模板',
                'filename': 'factors_b_template.csv',
                'description': '调节因子b矩阵模板，行为水质参数，列为特征编号',
            },
            'A': {
                'name': '校准因子A模板',
                'filename': 'factors_A_template.csv',
                'description': '校准因子A矩阵模板，行为水质参数，列为校准值',
            },
            'Range': {
                'name': 'Range数据模板',
                'filename': 'range_data_template.csv',
                'description': 'Range数据模板，行为水质参数名称，列为min和max',
            },
        }

    def get_required_templates(self, model_type: int) -> list[str]:
        """
        获取指定配置类型需要的模板文件

        Args:
            model_type: 配置类型 (0 或 1)

        Returns:
            List[str]: 需要的模板文件类型列表
        """
        if model_type == 0:
            # Type 0 快速配置模式
            return ['A', 'Range']
        elif model_type == 1:
            # Type 1 完整配置模式
            return ['w', 'a', 'b', 'A', 'Range']
        else:
            raise ValueError(f"不支持的配置类型: {model_type}")
