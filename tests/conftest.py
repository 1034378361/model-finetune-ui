"""
pytest配置文件

提供测试fixtures和共享配置
"""

import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from src.model_finetune_ui.utils.config_manager import ConfigurationManager


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_water_params():
    """水质参数列表fixture"""
    return [
        "turbidity",
        "ss",
        "sd",
        "do",
        "codmn",
        "codcr",
        "chla",
        "tn",
        "tp",
        "chroma",
        "nh3n",
    ]


@pytest.fixture
def sample_water_params():
    """水质参数列表fixture"""
    config_manager = ConfigurationManager()
    return config_manager.get_water_params()


@pytest.fixture
def sample_feature_stations():
    """特征站点列表fixture"""
    config_manager = ConfigurationManager()
    return config_manager.get_feature_stations()


@pytest.fixture
def sample_coefficient_data(sample_water_params, sample_feature_stations):
    """示例系数数据fixture"""
    return pd.DataFrame(
        np.random.randn(len(sample_water_params), len(sample_feature_stations)),
        index=sample_water_params,
        columns=sample_feature_stations,
    )


@pytest.fixture
def sample_range_data(sample_water_params):
    """示例Range数据fixture"""
    return pd.DataFrame(
        {
            "min": np.random.uniform(0, 10, len(sample_water_params)),
            "max": np.random.uniform(10, 100, len(sample_water_params)),
        },
        index=sample_water_params,
    )


@pytest.fixture
def sample_a_coefficient():
    """示例A系数数据fixture"""
    water_params = [
        "turbidity",
        "ss",
        "sd",
        "do",
        "codmn",
        "codcr",
        "chla",
        "tn",
        "tp",
        "chroma",
        "nh3n",
    ]
    return pd.DataFrame(
        {"A": np.random.uniform(0.5, 1.5, len(water_params))}, index=water_params
    )
