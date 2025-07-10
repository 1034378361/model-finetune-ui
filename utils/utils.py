#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用工具模块
提供编码检测、文件处理等通用功能
"""

import chardet
import logging
import os
import time
import pandas as pd
from typing import List, Optional, Union, Tuple, Callable
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控装饰器和工具"""
    
    @staticmethod
    def timing_logger(func_name: str = None):
        """函数执行时间监控装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or f"{func.__module__}.{func.__name__}"
                start_time = time.time()
                
                try:
                    logger.info(f"[性能监控] 开始执行: {name}")
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info(f"[性能监控] 执行完成: {name}, 耗时: {execution_time:.3f}秒")
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"[性能监控] 执行失败: {name}, 耗时: {execution_time:.3f}秒, 错误: {str(e)}")
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def memory_usage(func_name: str = None):
        """内存使用监控装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or f"{func.__module__}.{func.__name__}"
                
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    memory_before = process.memory_info().rss / 1024 / 1024  # MB
                    
                    logger.debug(f"[内存监控] 开始执行: {name}, 内存使用: {memory_before:.2f}MB")
                    result = func(*args, **kwargs)
                    
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_diff = memory_after - memory_before
                    logger.debug(f"[内存监控] 执行完成: {name}, 内存变化: {memory_diff:+.2f}MB, 当前: {memory_after:.2f}MB")
                    
                    return result
                except ImportError:
                    logger.warning("psutil未安装，跳过内存监控")
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"[内存监控] 监控异常: {name}, 错误: {str(e)}")
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class EnhancedLogger:
    """增强的日志工具"""
    
    @staticmethod
    def log_data_summary(data: pd.DataFrame, name: str = "数据", logger_instance: logging.Logger = None):
        """记录数据摘要信息"""
        if logger_instance is None:
            logger_instance = logger
            
        if data is None or data.empty:
            logger_instance.warning(f"[数据摘要] {name}: 数据为空")
            return
        
        logger_instance.info(f"[数据摘要] {name}: {len(data)}行 x {len(data.columns)}列")
        logger_instance.debug(f"[数据摘要] {name} 列名: {list(data.columns)}")
        logger_instance.debug(f"[数据摘要] {name} 内存使用: {data.memory_usage(deep=True).sum() / 1024 / 1024:.2f}MB")
        
        # 检查缺失值
        null_counts = data.isnull().sum()
        if null_counts.any():
            null_info = null_counts[null_counts > 0]
            logger_instance.info(f"[数据摘要] {name} 缺失值: {dict(null_info)}")
    
    @staticmethod
    def log_operation_context(operation: str, **context):
        """记录操作上下文信息"""
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        logger.info(f"[操作上下文] {operation}: {context_str}")
    
    @staticmethod
    def log_file_info(file_path: Union[str, Path], operation: str = "处理"):
        """记录文件信息"""
        try:
            path = Path(file_path)
            if path.exists():
                size_mb = path.stat().st_size / 1024 / 1024
                logger.info(f"[文件信息] {operation} {path.name}: 大小 {size_mb:.2f}MB, 路径 {path}")
            else:
                logger.warning(f"[文件信息] 文件不存在: {path}")
        except Exception as e:
            logger.warning(f"[文件信息] 获取文件信息失败: {str(e)}")


# 性能监控和日志的便捷装饰器
performance_monitor = PerformanceMonitor.timing_logger
memory_monitor = PerformanceMonitor.memory_usage


class EncodingDetector:
    """统一的文件编码检测和处理工具"""
    
    DEFAULT_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
    @classmethod
    def detect_file_encoding(cls, file_path: Union[str, Path], 
                           max_bytes: int = 8192) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            max_bytes: 最大读取字节数
            
        Returns:
            检测到的编码，默认为utf-8
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(max_bytes)
                if not raw_data:
                    return 'utf-8'
                    
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # 如果置信度太低，使用默认编码
                if confidence < 0.7:
                    logger.debug(f"编码检测置信度低 ({confidence:.2f})，使用默认编码: {file_path}")
                    encoding = 'utf-8'
                    
                return encoding or 'utf-8'
                
        except Exception as e:
            logger.warning(f"编码检测失败: {str(e)}")
            return 'utf-8'
    
    @classmethod
    def read_text_file(cls, file_path: Union[str, Path], 
                      encodings: Optional[List[str]] = None) -> Optional[str]:
        """
        尝试多种编码读取文本文件
        
        Args:
            file_path: 文件路径
            encodings: 尝试的编码列表
            
        Returns:
            文件内容，失败返回None
        """
        encodings = encodings or cls.DEFAULT_ENCODINGS
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                logger.debug(f"使用编码 {encoding} 成功读取文件: {file_path}")
                return content
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.debug(f"使用编码 {encoding} 读取文件失败: {str(e)}")
                continue
        
        logger.error(f"无法读取文件: {file_path}")
        return None
    
    @classmethod
    def read_csv_file(cls, file_path: Union[str, Path], 
                     encodings: Optional[List[str]] = None,
                     **kwargs) -> Optional[pd.DataFrame]:
        """
        尝试多种编码读取CSV文件
        
        Args:
            file_path: 文件路径
            encodings: 尝试的编码列表
            **kwargs: pandas.read_csv的其他参数
            
        Returns:
            DataFrame，失败返回None
        """
        encodings = encodings or cls.DEFAULT_ENCODINGS
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                logger.debug(f"使用编码 {encoding} 成功读取CSV文件: {file_path}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.debug(f"使用编码 {encoding} 读取CSV失败: {str(e)}")
                continue
        
        logger.error(f"无法读取CSV文件: {file_path}")
        return None


class DataValidator:
    """数据验证工具"""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
        """
        验证地理坐标
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查数据类型
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return False, f"坐标必须是数值类型，获得: lat={type(lat)}, lon={type(lon)}"
        
        # 检查是否为NaN或无穷大
        import math
        if math.isnan(lat) or math.isnan(lon):
            return False, "坐标不能为NaN"
        
        if math.isinf(lat) or math.isinf(lon):
            return False, "坐标不能为无穷大"
        
        # 检查范围
        if not (-90 <= lat <= 90):
            return False, f"纬度超出范围 [-90, 90]: {lat}"
        
        if not (-180 <= lon <= 180):
            return False, f"经度超出范围 [-180, 180]: {lon}"
        
        # 检查是否为极端边界值（可能的数据错误）
        if lat == 0 and lon == 0:
            return False, "坐标为(0,0)，可能是数据错误"
        
        return True, ""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None, 
                          min_rows: int = 1, name: str = "数据") -> Tuple[bool, str]:
        """验证DataFrame的基本要求"""
        if df is None:
            return False, f"{name}为None"
        
        if df.empty:
            return False, f"{name}为空"
        
        if len(df) < min_rows:
            return False, f"{name}行数不足，要求最少{min_rows}行，实际{len(df)}行"
        
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                return False, f"{name}缺少必需列: {list(missing_columns)}"
        
        # 检查是否有完全重复的行
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            logger.warning(f"[数据验证] {name}包含{duplicate_count}行完全重复的数据")
        
        return True, ""
    
    @staticmethod
    def validate_water_quality_indicator(value: float, indicator: str) -> Tuple[bool, str]:
        """验证水质指标值的合理性"""
        if pd.isna(value):
            return True, ""  # NaN值是允许的
        
        if not isinstance(value, (int, float)):
            return False, f"指标值必须是数值类型: {type(value)}"
        
        import math
        if math.isinf(value):
            return False, f"指标值不能为无穷大"
        
        # 定义各指标的合理范围
        reasonable_ranges = {
            'turbidity': (0, 1000), 'ss': (0, 500), 'do': (0, 20),
            'nh3n': (0, 50), 'tn': (0, 100), 'tp': (0, 10),
            'cod': (0, 1000), 'cod_mn': (0, 100), 'ph': (0, 14),
            'chla': (0, 1000), 'bga': (0, 100000),
        }
        
        # 标准化指标名称
        indicator_lower = indicator.lower().replace('-', '_')
        
        if indicator_lower in reasonable_ranges:
            min_val, max_val = reasonable_ranges[indicator_lower]
            if not (min_val <= value <= max_val):
                return False, f"指标{indicator}值超出合理范围[{min_val}, {max_val}]: {value}"
        
        # 负数检查
        if value < 0 and indicator_lower != 'ph':
            return False, f"指标{indicator}不应为负数: {value}"
        
        return True, ""
    
    @staticmethod
    def validate_positive_numeric(value, name: str) -> Tuple[bool, str]:
        """
        验证正数值
        
        Args:
            value: 要验证的值
            name: 字段名称
            
        Returns:
            (是否有效, 错误信息)
        """
        if pd.isna(value):
            return False, f"{name} 为空值"
            
        try:
            num_value = float(value)
            if num_value < 0:
                return False, f"{name} 不能为负数: {num_value}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{name} 不是有效的数值: {value}"


class FileUtils:
    """文件操作工具"""
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> None:
        """确保目录存在"""
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_size_mb(file_path: Union[str, Path]) -> float:
        """获取文件大小（MB）"""
        try:
            size_bytes = Path(file_path).stat().st_size
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """清理文件名中的非法字符"""
        import re
        # 移除或替换非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        cleaned = re.sub(illegal_chars, '_', filename)
        return cleaned.strip()


class ConfigManager:
    """配置管理器"""
    
    # 水质指标映射配置
    INDICATOR_MAPPING = {
        '浊度': 'turbidity',
        '浊度(NTU)': 'turbidity',
        'turbidity': 'turbidity',
        '悬浮物': 'ss',
        '悬浮物(mg/L)': 'ss',
        'SS': 'ss',
        'ss': 'ss',
        '溶解氧': 'do',
        '溶解氧(mg/L)': 'do',
        'DO': 'do',
        'do': 'do',
        '氨氮': 'nh3n',
        '氨氮(mg/L)': 'nh3n',
        'NH3-N': 'nh3n',
        'nh3n': 'nh3n',
        '总氮': 'tn',
        '总氮(mg/L)': 'tn',
        'TN': 'tn',
        'tn': 'tn',
        '总磷': 'tp',
        '总磷(mg/L)': 'tp',
        'TP': 'tp',
        'tp': 'tp',
        'COD': 'cod',
        'cod': 'cod',
        '高锰酸盐指数': 'cod_mn',
        'CODMn': 'cod_mn',
        'cod_mn': 'cod_mn',
        'pH': 'ph',
        'ph': 'ph',
    }
    
    # 数据清洗配置
    CLEANING_CONFIG = {
        'iqr_multiplier': 3.0,  # IQR异常值检测倍数
        'outlier_ratio_threshold': 0.2,  # 异常值比例阈值
        'min_valid_samples': 5,  # 最小有效样本数
    }
    
    # 地理匹配配置
    GEO_MATCHING_CONFIG = {
        'max_distance_km': 10.0,  # 最大匹配距离（公里）
        'earth_radius_km': 6371.0,  # 地球半径（公里）
    }
    
    # 安全配置 - 环境变量名映射
    SECURITY_CONFIG = {
        'encryption_key_env': 'WATER_QUALITY_ENCRYPTION_KEY',
        'salt_env': 'WATER_QUALITY_SALT', 
        'iv_env': 'WATER_QUALITY_IV',
        'config_file_env': 'WATER_QUALITY_CONFIG_FILE',  # 配置文件路径环境变量
        'key_file_env': 'WATER_QUALITY_KEY_FILE',  # 密钥文件路径环境变量
    }
    
    @classmethod
    def get_indicator_mapping(cls) -> dict:
        """获取指标映射配置"""
        return cls.INDICATOR_MAPPING.copy()
    
    @classmethod
    def get_encryption_config(cls) -> dict:
        """安全获取加密配置 - 多层次配置策略"""
        import os
        import json
        import secrets
        from pathlib import Path
        
        # 加载.env文件
        cls._load_env_file()
        
        config = cls.SECURITY_CONFIG
        
        # 策略1: 优先从环境变量获取
        encryption_key = os.getenv(config['encryption_key_env'])
        salt = os.getenv(config['salt_env'])
        iv = os.getenv(config['iv_env'])
        
        # 策略2: 从配置文件获取
        if not all([encryption_key, salt, iv]):
            config_file = os.getenv(config['config_file_env'])
            if config_file and Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        file_config = json.load(f)
                    encryption_key = encryption_key or file_config.get('encryption_key')
                    salt = salt or file_config.get('salt')
                    iv = iv or file_config.get('iv')
                    logger.info(f"从配置文件加载加密配置: {config_file}")
                except Exception as e:
                    logger.warning(f"读取配置文件失败: {e}")

        # 如果encryption_key、salt和iv任一不存在则前端提示缺失加密信息
        if not all([encryption_key, salt, iv]):
            raise ValueError("缺失加密信息，请联系管理员配置encryption_key、salt和iv。")
        
        # 确保正确的数据类型 - 保持与autowaterqualitymodeler默认参数兼容
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode('utf-8')
        if isinstance(salt, str):
            salt = salt.encode('utf-8')
        if isinstance(iv, str):
            iv = iv.encode('utf-8')
        
        return {
            'password': encryption_key,
            'salt': salt,
            'iv': iv
        }

    
    @classmethod
    def _load_env_file(cls, env_path: str = None) -> bool:
        """加载.env文件到环境变量"""
        try:
            # 确定.env文件路径
            if env_path is None:
                # 按优先级查找.env文件
                possible_paths = [
                    os.getenv('ENV_FILE_PATH'),  # 环境变量指定
                    '.env',  # 当前目录
                    '../.env',  # 上级目录
                    '../../.env',  # 再上级目录
                    os.path.expanduser('~/.water_quality/.env'),  # 用户目录
                ]
                
                for path in possible_paths:
                    if path and Path(path).exists():
                        env_path = path
                        break
                else:
                    logger.debug("未找到.env文件")
                    return False
            
            # 读取并解析.env文件
            with open(env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # 只在环境变量不存在时设置（环境变量优先级更高）
                        if key and not os.getenv(key):
                            os.environ[key] = value
                    else:
                        logger.warning(f".env文件第{line_num}行格式错误: {line}")
            
            logger.info(f"已加载.env文件: {env_path}")
            return True
            
        except FileNotFoundError:
            logger.debug(f".env文件不存在: {env_path}")
            return False
        except Exception as e:
            logger.warning(f"加载.env文件失败: {e}")
            return False
    
    


# 自定义异常类
class DataProcessingError(Exception):
    """数据处理异常基类"""
    pass


class FileProcessingError(DataProcessingError):
    """文件处理异常"""
    pass


class DataValidationError(DataProcessingError):
    """数据验证异常"""
    pass


class GeographicMatchingError(DataProcessingError):
    """地理匹配异常"""
    pass


class EncodingError(FileProcessingError):
    """编码处理异常"""
    pass