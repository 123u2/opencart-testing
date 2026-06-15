"""
Locust 性能测试脚本
面试可讲：
  1. 使用 @task 装饰器设置权重，模拟真实用户行为（浏览多，下单少）
  2. wait_time = between(1, 3) 模拟用户思考时间
  3. on_start 中登录，模拟已认证用户
  4. 支持环境变量配置目标地址和测试凭据
  5. OpenCart 4.x API 认证：username + key → api_token → OCSESSID cookie

OpenCart 4.x 适配要点：
  - API 认证：POST api/account/login {username, key} → {api_token}
  - Token 作为 OCSESSID cookie 传递（不是 Authorization header）
  - 路由方法分隔符：| (如 api/sale/cart|add)
"""
import json
import os
import random
import sys

# 将项目根目录加入 sys.path 以导入 config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from locust import HttpUser, task, between, events


# ── 环境变量配置 ──────────────────────────────────────────
HOST = os.getenv("TARGET_HOST", Config.BASE_URL)
API_USERNAME = Config.API_USERNAME
API_KEY = Config.API_KEY
TEST_EMAIL = Config.TEST_EMAIL
TEST_PASSWORD = Config.TEST_PASSWORD
ADMIN_USERNAME = Config.ADMIN_USERNAME
ADMIN_PASSWORD = Config.ADMIN_PASSWORD

# 测试商品池（无必填选项的商品优先）
PRODUCT_IDS = [28, 29, 30, 40, 41, 42, 43]
CATEGORY_IDS = [20, 18, 25, 17, 24]
SEARCH_KEYWORDS = ["phone", "mac", "laptop", "camera", "tablet"]


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locust 初始化时设置目标地址"""
    if hasattr(environment, "host") and not environment.host:
        environment.host = HOST


class EcommerceUser(HttpUser):
    """模拟已认证电商用户行为（通过 API Key 认证）

    权重设计思路：
      - 浏览类操作权重高 (10 + 5 + 3 = 18)
      - 写入类操作权重低 (1 + 1 + 1 = 3)
      - 结账下单权重最低 (1)
      - 符合真实电商 ~85% 浏览 / ~15% 交易的规律
    """
    wait_time = between(1, 3)

    def on_start(self):
        """API 认证登录 — OpenCart 4.x 使用 username + key 认证

        登录流程：
          1. POST api/account/login {username, key} → {api_token}
          2. 将 api_token 设置为 OCSESSID cookie
          3. 后续 API 请求自动携带此 cookie
        """
        resp = self.client.post(
            "/index.php?route=api/account/login",
            data={"username": API_USERNAME, "key": API_KEY},
            name="/api/account/login",
        )

        if resp.status_code == 200:
            try:
                body = resp.json()
                if "api_token" in body:
                    api_token = body["api_token"]
                    # 关键：必须清除登录响应设置的 PHP session OCSESSID，
                    # 然后设置 API token 作为 OCSESSID（与 api_client.py 一致）
                    self.client.cookies.clear()
                    self.client.cookies.set("OCSESSID", api_token)
                else:
                    self._fire_failure("/api/account/login (no token)", resp)
            except (json.JSONDecodeError, KeyError):
                self._fire_failure("/api/account/login (parse error)", resp)
        else:
            self._fire_failure("/api/account/login (FAILED)", resp)

    def _fire_failure(self, name, resp):
        """手动记录请求失败事件"""
        self.client.request_event.fire(
            request_type="POST",
            name=name,
            response_time=resp.elapsed.total_seconds() * 1000,
            response_length=len(resp.text),
            exception=None,
        )

    # ── 浏览类 (权重合计 18) ────────────────────────────

    @task(10)
    def browse_category(self):
        """浏览商品分类 — 权重 10 (最高频)"""
        cat_id = random.choice(CATEGORY_IDS)
        self.client.get(
            f"/index.php?route=product/category&path={cat_id}",
            name="/product/category",
        )

    @task(5)
    def search_product(self):
        """搜索商品 — 权重 5"""
        kw = random.choice(SEARCH_KEYWORDS)
        self.client.get(
            f"/index.php?route=product/search&search={kw}",
            name="/product/search",
        )

    @task(3)
    def view_product_detail(self):
        """查看商品详情 — 权重 3"""
        pid = random.choice(PRODUCT_IDS)
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )

    # ── 购物车类 (权重合计 2) ──────────────────────────

    @task(1)
    def add_to_cart(self):
        """加入购物车 — 权重 1"""
        pid = random.choice(PRODUCT_IDS)
        self.client.post(
            "/index.php?route=api/sale/cart|add",
            data={"product_id": pid, "quantity": random.randint(1, 3)},
            name="/api/sale/cart|add",
        )

    @task(1)
    def view_cart(self):
        """查看购物车 — 权重 1"""
        self.client.get("/index.php?route=checkout/cart", name="/checkout/cart")

    # ── 结账流程 (权重 1) — 最低频但最关键的写操作 ──────

    @task(1)
    def checkout_flow(self):
        """结账下单完整流程 — 权重 1 (最低频但最关键)

        模拟从设置地址到确认订单的完整链路（OpenCart 4.x API 路由）。
        这是性能测试中最能反映系统吞吐能力的场景。
        """
        # Step 1: 确保购物车有商品
        self.client.post(
            "/index.php?route=api/sale/cart|add",
            data={"product_id": 28, "quantity": 1},
            name="/api/sale/cart|add (checkout setup)",
        )

        # Step 2: 设置配送地址（使用完整 address 字段）
        self.client.post(
            "/index.php?route=api/sale/shipping_address",
            data={
                "firstname": "Test",
                "lastname": "User",
                "address_1": "123 Test Street",
                "city": "London",
                "country_id": "222",
                "zone_id": "3513",
            },
            name="/api/sale/shipping_address",
        )

        # Step 3: 获取可用的配送方式
        self.client.get(
            "/index.php?route=api/sale/shipping_method",
            name="/api/sale/shipping_method",
        )

        # Step 4: 设置配送方式
        self.client.post(
            "/index.php?route=api/sale/shipping_method|save",
            data={"shipping_method": "flat.flat"},
            name="/api/sale/shipping_method|save",
        )

        # Step 5: 设置支付地址
        self.client.post(
            "/index.php?route=api/sale/payment_address",
            data={
                "firstname": "Test",
                "lastname": "User",
                "address_1": "123 Test Street",
                "city": "London",
                "country_id": "222",
                "zone_id": "3513",
            },
            name="/api/sale/payment_address",
        )

        # Step 6: 获取可用的支付方式
        self.client.get(
            "/index.php?route=api/sale/payment_method",
            name="/api/sale/payment_method",
        )

        # Step 7: 设置支付方式
        self.client.post(
            "/index.php?route=api/sale/payment_method|save",
            data={"payment_method": "cod"},
            name="/api/sale/payment_method|save",
        )

        # Step 8: 确认订单
        self.client.post(
            "/index.php?route=api/sale/order|confirm",
            name="/api/sale/order|confirm",
        )


class GuestUser(HttpUser):
    """模拟未登录访客行为

    访客只能浏览，不执行写操作。
    """
    wait_time = between(2, 5)

    @task(10)
    def browse_homepage(self):
        """浏览首页 — 权重 10"""
        self.client.get("/", name="/ (homepage)")

    @task(5)
    def browse_category(self):
        """浏览分类 — 权重 5"""
        cat_id = random.choice(CATEGORY_IDS)
        self.client.get(
            f"/index.php?route=product/category&path={cat_id}",
            name="/product/category",
        )

    @task(2)
    def view_product(self):
        """查看商品详情 — 权重 2"""
        pid = random.choice(PRODUCT_IDS)
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )

    @task(1)
    def search_product(self):
        """搜索商品 — 权重 1"""
        kw = random.choice(SEARCH_KEYWORDS)
        self.client.get(
            f"/index.php?route=product/search&search={kw}",
            name="/product/search",
        )


class AdminUser(HttpUser):
    """模拟后台管理员行为

    管理员操作与前台用户不同，关注的是管理功能性能。
    """
    wait_time = between(3, 8)

    def on_start(self):
        """管理员通过 Web 表单登录后台"""
        self.client.post(
            "/admin/index.php?route=common/login",
            data={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
            },
            name="/admin/login",
        )

    @task(5)
    def view_dashboard(self):
        """查看 Dashboard"""
        self.client.get(
            "/admin/index.php?route=common/dashboard", name="/admin/dashboard"
        )

    @task(3)
    def view_orders(self):
        """查看订单列表 — 通常是最重的后台查询"""
        self.client.get(
            "/admin/index.php?route=sale/order", name="/admin/sale/order"
        )

    @task(2)
    def view_products(self):
        """查看商品列表"""
        self.client.get(
            "/admin/index.php?route=catalog/product", name="/admin/catalog/product"
        )
