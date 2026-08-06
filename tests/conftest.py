"""全局 pytest fixtures。"""
import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """每个测试前后清除 get_settings 缓存，保证环境变量改动生效。"""
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def tmp_chroma_dir(tmp_path: Path) -> Path:
    """临时 Chroma 持久化目录，测试结束自动清理。"""
    d = tmp_path / "chroma"
    d.mkdir(exist_ok=True)
    yield d
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def isolated_env(monkeypatch):
    """提供一个干净环境，便于注入测试用环境变量。"""
    # 清除可能干扰的变量
    for key in list(os.environ.keys()):
        if key.startswith(("DEEPSEEK_", "QWEN_", "EMBEDDING_", "MODEL_")):
            monkeypatch.delenv(key, raising=False)
    return monkeypatch
