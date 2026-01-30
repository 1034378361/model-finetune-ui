#!/usr/bin/env python
"""
配置文件

UI项目的配置管理
"""

import os
from typing import Any

from .utils.config_manager import ConfigurationManager


# 全局配置管理器实例（懒加载）
_config_manager: ConfigurationManager | None = None


def get_config_manager() -> ConfigurationManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


class UIConfig:
    """UI配置类"""

    # 应用基础配置
    APP_TITLE = "Model Finetune UI"
    APP_ICON = "🚀"

    # 支持的文件格式
    SUPPORTED_FILE_FORMATS = [".csv", ".xlsx", ".xls"]

    # 最大文件大小（MB）
    MAX_FILE_SIZE_MB = 50

    # 默认输出目录
    DEFAULT_OUTPUT_DIR = "./ui_output"

    # 水质参数配置
    WATER_QUALITY_PARAMS = [
        "turbidity",  # 浊度
        "ss",  # 悬浮物
        "sd",  # 透明度
        "do",  # 溶解氧
        "codmn",  # 高锰酸盐指数
        "codcr",  # 化学需氧量
        "chla",  # 叶绿素a
        "tn",  # 总氮
        "tp",  # 总磷
        "chroma",  # 色度
        "nh3n",  # 氨氮
    ]

    # 水质参数中文名称映射
    WATER_QUALITY_PARAMS_CN = {
        "turbidity": "浊度",
        "ss": "悬浮物",
        "sd": "透明度",
        "do": "溶解氧",
        "codmn": "高锰酸盐指数",
        "codcr": "化学需氧量",
        "chla": "叶绿素a",
        "tn": "总氮",
        "tp": "总磷",
        "chroma": "色度",
        "nh3n": "氨氮",
    }

    # 特征配置
    FEATURE_STATIONS = [f"STZ{i}" for i in range(1, 27)]

    # 模型类型配置
    MODEL_TYPES = {
        0: {
            "name": "微调模式",
            "description": "仅使用微调系数进行模型微调",
            "required_files": ["A", "Range"],
            "color": "#1f77b4",
        },
        1: {
            "name": "完整建模模式",
            "description": "使用完整的w权重、a权重、b幂系数进行建模（微调系数自动生成）",
            "required_files": ["w", "a", "b", "Range"],
            "color": "#ff7f0e",
        },
    }

    # 文件类型配置
    FILE_TYPES = {
        "w": {
            "name": "w权重系数文件",
            "description": "w权重系数矩阵，行为水质参数，列为特征",
            "example_shape": "(11, 26)",
            "data_type": "float",
            "required_for": [1],
        },
        "a": {
            "name": "a权重系数文件",
            "description": "a权重系数矩阵，行为水质参数，列为特征",
            "example_shape": "(11, 26)",
            "data_type": "float",
            "required_for": [1],
        },
        "b": {
            "name": "b幂系数文件",
            "description": "b幂系数矩阵，行为水质参数，列为特征",
            "example_shape": "(11, 26)",
            "data_type": "float",
            "required_for": [1],
        },
        "A": {
            "name": "A微调系数文件",
            "description": "微调系数矩阵，行为水质参数，列为A（Type 1模式自动生成全1矩阵）",
            "example_shape": "(11, 1)",
            "data_type": "float",
            "required_for": [0],
            "auto_generate_for": [1],
        },
        "Range": {
            "name": "Range数据文件",
            "description": "用于计算指标范围的参考数据，包含各水质参数的观测值",
            "example_shape": "(N, 11)",
            "data_type": "float",
            "required_for": [0, 1],
        },
    }

    # Streamlit页面配置
    STREAMLIT_CONFIG = {
        "page_title": APP_TITLE,
        "page_icon": APP_ICON,
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    }

    # 日志配置
    LOGGING_CONFIG = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }

    @classmethod
    def get_required_files_for_model_type(cls, model_type: int) -> list[str]:
        """获取指定模型类型需要的文件"""
        return cls.MODEL_TYPES.get(model_type, {}).get("required_files", [])

    @classmethod
    def get_file_description(cls, file_type: str) -> str:
        """获取文件类型描述"""
        return cls.FILE_TYPES.get(file_type, {}).get("description", "")

    @classmethod
    def is_file_required_for_model_type(cls, file_type: str, model_type: int) -> bool:
        """检查文件是否为指定模型类型必需"""
        required_for = cls.FILE_TYPES.get(file_type, {}).get("required_for", [])
        return model_type in required_for

    @classmethod
    def get_water_quality_param_cn_name(cls, param_en: str) -> str:
        """获取水质参数中文名称"""
        return cls.WATER_QUALITY_PARAMS_CN.get(param_en, param_en)

    @classmethod
    def get_model_type_info(cls, model_type: int) -> dict[str, Any]:
        """获取模型类型信息"""
        return cls.MODEL_TYPES.get(model_type, {})

    @classmethod
    def get_water_quality_params(cls) -> list[str]:
        """动态获取水质参数列表"""
        return get_config_manager().get_water_params()

    @classmethod
    def get_feature_stations(cls) -> list[str]:
        """动态获取特征站点列表"""
        return get_config_manager().get_feature_stations()


class EnvironmentConfig:
    """环境配置类"""

    @staticmethod
    def get_output_dir() -> str:
        """获取输出目录"""
        return os.getenv("UI_OUTPUT_DIR", UIConfig.DEFAULT_OUTPUT_DIR)

    @staticmethod
    def get_debug_mode() -> bool:
        """获取调试模式状态"""
        return os.getenv("UI_DEBUG", "false").lower() == "true"

    @staticmethod
    def get_max_file_size_mb() -> int:
        """获取最大文件大小"""
        return int(os.getenv("UI_MAX_FILE_SIZE_MB", UIConfig.MAX_FILE_SIZE_MB))

    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return os.getenv("UI_LOG_LEVEL", UIConfig.LOGGING_CONFIG["level"])


class ValidationConfig:
    """验证配置类"""

    # 数据验证阈值
    MIN_SAMPLES_FOR_RANGE = 2
    MAX_ZERO_RATIO = 0.9
    MAX_NULL_RATIO = 0.5

    # 数值范围验证
    COEFFICIENT_VALUE_RANGE = (-1000, 1000)
    A_COEFFICIENT_RANGE = (-10, 10)

    # 维度验证
    EXPECTED_WATER_PARAMS_COUNT = 11
    EXPECTED_STATION_COUNT = 26

    @classmethod
    def get_validation_thresholds(cls) -> dict[str, Any]:
        """获取验证阈值"""
        return {
            "min_samples_for_range": cls.MIN_SAMPLES_FOR_RANGE,
            "max_zero_ratio": cls.MAX_ZERO_RATIO,
            "max_null_ratio": cls.MAX_NULL_RATIO,
            "coefficient_value_range": cls.COEFFICIENT_VALUE_RANGE,
            "a_coefficient_range": cls.A_COEFFICIENT_RANGE,
        }

    @classmethod
    def get_expected_water_params_count(cls) -> int:
        """动态获取期望的水质参数数量"""
        return len(get_config_manager().get_water_params())

    @classmethod
    def get_expected_station_count(cls) -> int:
        """动态获取期望的站点数量"""
        return len(get_config_manager().get_feature_stations())


# 导出配置实例
ui_config = UIConfig()
env_config = EnvironmentConfig()
validation_config = ValidationConfig()
