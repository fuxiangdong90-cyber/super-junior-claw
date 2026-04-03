"""pytest配置"""
import pytest
import asyncio

# 配置pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )