import logging
from collections import deque
from datetime import datetime


# ==================== 日志处理器 ====================
class StreamlitLogHandler(logging.Handler):
    """将日志捕获到内存中供Streamlit显示"""

    _instance = None
    _logs: deque = deque(maxlen=500)  # 最多保留500条日志

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            level = record.levelname
            self._logs.append({"time": timestamp, "level": level, "msg": msg})
        except Exception:
            pass

    @classmethod
    def get_logs(cls) -> list[dict]:
        """获取所有日志"""
        return list(cls._logs)

    @classmethod
    def clear_logs(cls):
        """清空日志"""
        cls._logs.clear()

    @classmethod
    def get_logs_by_level(cls, level: str | None = None) -> list[dict]:
        """按级别过滤日志"""
        if level is None or level == "ALL":
            return list(cls._logs)
        return [log for log in cls._logs if log["level"] == level]


def setup_logging():
    """配置日志系统，捕获所有相关模块的日志"""
    # 创建处理器
    handler = StreamlitLogHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)s - %(message)s")
    handler.setFormatter(formatter)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 移除已存在的StreamlitLogHandler（避免重复）
    # 注意：由于Streamlit的重载机制，这里可能会有来自旧模块的handler实例
    # 我们通过类名判断来移除它们，以保持单例行为
    handlers_to_remove = []
    for h in root_logger.handlers:
        if h.__class__.__name__ == "StreamlitLogHandler":
            handlers_to_remove.append(h)

    for h in handlers_to_remove:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)

    # 配置项目相关的日志器
    loggers_to_capture = [
        "src.model_finetune_ui",
        "model_finetune_ui",
        "__main__",
    ]
    for logger_name in loggers_to_capture:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        # 确保日志向上传播到根日志器
        logger.propagate = True
