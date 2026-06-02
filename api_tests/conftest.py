"""
API 测试的 pytest fixture 配置
面试可讲：
  - scope="session": 整个测试会话复用同一个 API 客户端（节省登录开销）
  - scope="function": 每个用例独立的数据清理
  - DB fixture: 数据库断言，验证 API 返回的数据真实落库
"""
import pytest
import sys
import os

# 项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.api_client import OpenCartAPI
from utils.db_helper import DBHelper


@pytest.fixture(scope="session")
def config():
    """全局配置"""
    return Config


@pytest.fixture(scope="session")
def api(config):
    """API 客户端（session 级别，整个测试共用）

    启动时自动登录，后续所有用例复用已认证的 session。
    """
    client = OpenCartAPI(base_url=config.BASE_URL, timeout=config.API_TIMEOUT)
    # 使用测试账号登录
    resp = client.login(config.TEST_EMAIL, config.TEST_PASSWORD)
    assert resp.status_code == 200, f"API 登录失败: {resp.text}"
    yield client
    client.close()


@pytest.fixture(scope="session")
def db(config):
    """数据库连接（session 级别）

    用于验证 API 操作后数据是否正确写入数据库。
    """
    helper = DBHelper(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )
    helper.connect()
    yield helper
    helper.close()


@pytest.fixture
def fresh_cart(api):
    """每次用例执行前后清空购物车，确保测试隔离"""
    api.post("api/cart/clear")
    yield
    api.post("api/cart/clear")
