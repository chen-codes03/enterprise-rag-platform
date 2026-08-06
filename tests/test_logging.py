"""T0.5 RED: 日志模块测试。

验证 get_logger 返回带名称的 logger，并可设置级别。
"""
import logging


def test_get_logger_returns_logger_with_name():
    from app.core.logging import get_logger

    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_get_logger_has_handler():
    """配置后 logger 应至少有一个 handler，避免日志丢失。"""
    from app.core.logging import get_logger

    logger = get_logger("handler_check")
    assert len(logger.handlers) >= 1


def test_get_logger_level_configurable():
    """get_logger 应能设置日志级别。"""
    from app.core.logging import get_logger

    logger = get_logger("level_check", level=logging.DEBUG)
    assert logger.level == logging.DEBUG
