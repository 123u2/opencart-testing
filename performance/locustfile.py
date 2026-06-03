"""
Locust 性能测试脚本
面试可讲：
  1. 使用 @task 装饰器设置权重，模拟真实用户行为（浏览多，下单少）
  2. wait_time = between(1, 3) 模拟用户思考时间
  3. on_start 中登录，模拟已认证用户
  4. 支持环境变量配置目标地址和测试凭据
"""
import os
import random
from locust import HttpUser, task, between, events


# ── 环境变量配置 ──────────────────────────────────────────
HOST = os.getenv("TARGET_HOST", "http://localhost:8080")
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password")


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locust 初始化时设置目标地址"""
    if hasattr(environment, "host") and not environment.host:
        environment.host = HOST


class EcommerceUser(HttpUser):
    """模拟已认证电商用户行为

    权重设计思路：
      - 浏览类操作权重高 (10 + 5 + 3 = 18)
      - 写入类操作权重低 (1 + 1 + 1 = 3)
      - 结账下单权重最低 (1)
      - 符合真实电商 ~85% 浏览 / ~15% 交易的规律
    """
    wait_time = between(1, 3)

    def on_start(self):
        """用户登录 — 每个虚拟用户启动时执行一次"""
        resp = self.client.post(
            "/index.php?route=api/account/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            name="/api/account/login",
        )
        # 记录登录响应时间
        if resp.status_code != 200:
            self.client.request_event.fire(
                request_type="POST",
                name="/api/account/login (FAILED)",
                response_time=resp.elapsed.total_seconds() * 1000,
                response_length=len(resp.text),
                exception=None,
            )

    # ── 浏览类 (权重合计 18) ────────────────────────────

    @task(10)
    def browse_category(self):
        """浏览商品分类 — 权重 10 (最高频)"""
        cat_id = random.choice([20, 18, 25, 17, 24])
        self.client.get(
            f"/index.php?route=product/category&path={cat_id}",
            name="/product/category",
        )

    @task(5)
    def search_product(self):
        """搜索商品 — 权重 5"""
        kw = random.choice(["phone", "mac", "laptop", "camera", "tablet"])
        self.client.get(
            f"/index.php?route=product/search&search={kw}",
            name="/product/search",
        )

    @task(3)
    def view_product_detail(self):
        """查看商品详情 — 权重 3"""
        pid = random.choice([28, 29, 30, 40, 41, 42, 43])
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )

    # ── 购物车类 (权重合计 2) ──────────────────────────

    @task(1)
    def add_to_cart(self):
        """加入购物车 — 权重 1"""
        pid = random.choice([28, 29, 30, 40, 41, 42, 43])
        self.client.post(
            "/index.php?route=api/cart/add",
            data={"product_id": pid, "quantity": random.randint(1, 3)},
            name="/api/cart/add",
        )

    @task(1)
    def view_cart(self):
        """查看购物车 — 权重 1"""
        self.client.get("/index.php?route=checkout/cart", name="/checkout/cart")

    # ── 结账流程 (权重 1) — 最低频但最关键的写操作 ──────

    @task(1)
    def checkout_flow(self):
        """结账下单完整流程 — 权重 1 (最低频但最关键)

        模拟从设置地址到确认订单的完整链路。
        这是性能测试中最能反映系统吞吐能力的场景。
        """
        # 确保购物车有商品
        self.client.post(
            "/index.php?route=api/cart/add",
            data={"product_id": 42, "quantity": 1},
            name="/api/cart/add (checkout setup)",
        )

        # 设置配送地址
        self.client.post(
            "/index.php?route=api/shipping_address/save",
            data={"shipping_address_id": 1},
            name="/api/shipping_address/save",
        )

        # 获取配送方式
        self.client.get(
            "/index.php?route=api/shipping_method/getShippingMethods",
            name="/api/shipping_method/getShippingMethods",
        )

        # 设置支付地址
        self.client.post(
            "/index.php?route=api/payment_address/save",
            data={"payment_address_id": 1},
            name="/api/payment_address/save",
        )

        # 获取支付方式
        self.client.get(
            "/index.php?route=api/payment_method/getPaymentMethods",
            name="/api/payment_method/getPaymentMethods",
        )

        # 确认订单
        self.client.post(
            "/index.php?route=api/order/confirm",
            name="/api/order/confirm",
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
        cat_id = random.choice([20, 18, 25, 17, 24])
        self.client.get(
            f"/index.php?route=product/category&path={cat_id}",
            name="/product/category",
        )

    @task(2)
    def view_product(self):
        """查看商品详情 — 权重 2"""
        pid = random.choice([28, 29, 30, 40, 41, 42, 43])
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )

    @task(1)
    def search_product(self):
        """搜索商品 — 权重 1"""
        kw = random.choice(["phone", "mac", "laptop", "camera", "tablet"])
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
        """管理员登录"""
        self.client.post(
            "/admin/index.php?route=common/login",
            data={
                "username": os.getenv("ADMIN_USERNAME", "admin"),
                "password": os.getenv("ADMIN_PASSWORD", "admin123"),
            },
            name="/admin/login",
        )

    @task(5)
    def view_dashboard(self):
        """查看 Dashboard"""
        self.client.get("/admin/index.php?route=common/dashboard", name="/admin/dashboard")

    @task(3)
    def view_orders(self):
        """查看订单列表 — 通常是最重的后台查询"""
        self.client.get("/admin/index.php?route=sale/order", name="/admin/sale/order")

    @task(2)
    def view_products(self):
        """查看商品列表"""
        self.client.get("/admin/index.php?route=catalog/product", name="/admin/catalog/product")
