"""
API 测试的 pytest fixture 配置
面试可讲：
  - scope="session": 整个测试会话复用同一个 API 客户端（节省登录开销）
  - scope="function": 每个用例独立的数据清理
  - DB fixture: 数据库断言，验证 API 返回的数据真实落库

OpenCart 4.x 适配：
  - 认证使用 username + API Key（非 email + password）
  - api_token 通过 OCSESSID cookie 传递
  - 登录端点为 api/account/login
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

    使用 OpenCart 4.x API Key 认证：
    POST api/account/login {username, key} → 获取 api_token
    api_token 自动设置为 OCSESSID cookie
    """
    client = OpenCartAPI(base_url=config.BASE_URL, timeout=config.API_TIMEOUT)
    # 使用 API Key 登录
    resp = client.login(config.API_USERNAME, config.API_KEY)
    assert resp.status_code == 200, f"API 登录失败: {resp.status_code} — {resp.text}"

    body = resp.json()
    assert "api_token" in body, f"API 登录未返回 api_token: {body}"
    assert client.is_authenticated(), "api_token 应已设置"

    yield client
    client.close()


@pytest.fixture(scope="session")
def db(config):
    """数据库连接（session 级别）

    用于验证 API 操作后数据是否正确写入数据库。
    注意：Docker Compose 需要暴露 MariaDB 的 3306 端口才能从宿主机连接。
    """
    helper = DBHelper(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )
    try:
        helper.connect()
    except Exception as e:
        pytest.skip(f"数据库连接失败，跳过 DB 相关测试: {e}")

    yield helper
    helper.close()


@pytest.fixture(scope="session")
def unauth_api(config):
    """未登录的 API 客户端（session 级别）

    用于测试登录、登出等不需要预先认证的场景。
    """
    client = OpenCartAPI(base_url=config.BASE_URL, timeout=config.API_TIMEOUT)
    yield client
    client.close()


@pytest.fixture
def fresh_cart(api):
    """每次用例执行前后清空购物车，确保测试隔离

    OpenCart 4.x 使用 api/sale/cart|edit (key=cart_id, quantity=0)
    或 api/sale/cart|remove 来清空购物车。
    这里通过重复调用 get cart → remove all items 来实现。
    """
    # 清空前：获取所有商品并逐个移除
    resp = api.get("api/sale/cart")
    try:
        body = resp.json()
        for product in body.get("products", []):
            cart_id = product.get("cart_id")
            if cart_id:
                api.post("api/sale/cart|remove", data={"key": cart_id})
    except Exception:
        pass  # 清空失败不影响后续测试
    yield
    # 清空后：再次清理
    try:
        resp = api.get("api/sale/cart")
        body = resp.json()
        for product in body.get("products", []):
            cart_id = product.get("cart_id")
            if cart_id:
                api.post("api/sale/cart|remove", data={"key": cart_id})
    except Exception:
        pass
