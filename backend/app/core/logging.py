"""日志模块。

提供统一的 get_logger 工厂，确保 logger 带 handler 且级别可配。
"""
import logging
import sys

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_CONFIGURED_ROOTS: set[str] = set()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取带名称的 logger，首次获取时挂载 StreamHandler。

    同名 logger 仅配置一次，避免重复 handler。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if name not in _CONFIGURED_ROOTS:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False
        _CONFIGURED_ROOTS.add(name)

    return logger
