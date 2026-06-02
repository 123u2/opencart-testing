"""
Locust 性能测试脚本
面试可讲：
  1. 使用 @task 装饰器设置权重，模拟真实用户行为（浏览多，下单少）
  2. wait_time = between(1, 3) 模拟用户思考时间
  3. on_start 中登录，模拟已认证用户
"""
from locust import HttpUser, task, between


class EcommerceUser(HttpUser):
    """模拟电商用户行为

    权重设计思路：
      - 浏览类操作权重高 (10 + 5 + 3 = 18)
      - 写入类操作权重低 (1 + 1 = 2)
      - 符合真实电商 90% 浏览 / 10% 交易的规律
    """
    wait_time = between(1, 3)  # 用户操作间隔 1-3 秒

    def on_start(self):
        """用户登录 — 每次启动一个新用户时执行"""
        self.client.post(
            "/index.php?route=api/account/login",
            data={"email": "test@example.com", "password": "password"},
        )

    @task(10)
    def browse_category(self):
        """浏览商品分类 — 权重 10 (最高频)"""
        # 模拟浏览不同分类
        categories = [20, 18, 25, 17, 24]  # 不同分类 ID
        import random
        cat_id = random.choice(categories)
        self.client.get(
            f"/index.php?route=product/category&path={cat_id}",
            name="/product/category",
        )

    @task(5)
    def search_product(self):
        """搜索商品 — 权重 5"""
        keywords = ["phone", "mac", "laptop", "camera", "tablet"]
        import random
        kw = random.choice(keywords)
        self.client.get(
            f"/index.php?route=product/search&search={kw}",
            name="/product/search",
        )

    @task(3)
    def view_product_detail(self):
        """查看商品详情 — 权重 3"""
        product_ids = [28, 29, 30, 40, 41, 42, 43]
        import random
        pid = random.choice(product_ids)
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )

    @task(1)
    def add_to_cart(self):
        """加入购物车 — 权重 1 (低频)"""
        self.client.post(
            "/index.php?route=api/cart/add",
            data={"product_id": 42, "quantity": 1},
            name="/api/cart/add",
        )

    @task(1)
    def view_cart(self):
        """查看购物车 — 权重 1"""
        self.client.get("/index.php?route=checkout/cart", name="/checkout/cart")


class GuestUser(HttpUser):
    """模拟未登录访客行为"""
    wait_time = between(2, 5)

    @task(10)
    def browse_homepage(self):
        self.client.get("/")

    @task(5)
    def browse_category(self):
        self.client.get(
            "/index.php?route=product/category&path=20",
            name="/product/category",
        )

    @task(2)
    def view_product(self):
        import random
        pid = random.choice([28, 29, 30, 40, 41, 42, 43])
        self.client.get(
            f"/index.php?route=product/product&product_id={pid}",
            name="/product/product",
        )
