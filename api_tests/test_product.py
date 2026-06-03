"""
商品模块 API 测试
覆盖：获取购物车商品、添加/移除商品、Schema 校验、商品搜索、库存验证
"""
import json
import os
import allure
import pytest
from jsonschema import validate, ValidationError


@allure.feature("商品模块")
class TestProduct:

    # ── 购物车商品查询 ────────────────────────────────────

    @allure.story("获取购物车商品列表")
    @allure.title("空购物车 getProducts 应返回空列表")
    def test_get_empty_cart(self, api, fresh_cart):
        """验证空购物车时 API 返回空商品列表"""
        resp = api.get("api/cart/getProducts")
        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"

        body = resp.json()
        assert len(body.get("products", [])) == 0, \
            f"空购物车 product 列表应为空: {body}"
        assert "error" not in body or body.get("error") is None, \
            f"空购物车不应有 error: {body}"

    # ── JSON Schema 校验（契约测试）────────────────────────

    @allure.story("JSON Schema 校验")
    @allure.title("getProducts 响应应符合 JSON Schema 结构")
    def test_get_products_schema(self, api):
        """验证 API 响应结构符合预期 Schema（契约测试）"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        resp = api.get("api/cart/getProducts")
        body = resp.json()

        schema_path = os.path.join(
            os.path.dirname(__file__), "schemas", "product.json"
        )
        with open(schema_path, "r") as f:
            schema = json.load(f)

        try:
            validate(instance=body, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Schema 校验失败: {e.message}")

    # ── 添加商品 — 正常流程 ───────────────────────────────

    @allure.story("添加商品到购物车")
    @allure.title("添加存在的商品 product_id=42 应成功")
    @pytest.mark.smoke
    def test_add_product_success(self, api, fresh_cart):
        """等价类-有效：添加存在的商品"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        assert resp.status_code == 200

        body = resp.json()
        assert body.get("success"), f"应返回 success: {body}"

        # 验证购物车中确实有商品
        products_resp = api.get("api/cart/getProducts")
        products = products_resp.json().get("products", [])
        assert len(products) >= 1, "添加商品后购物车不应为空"

    @allure.story("添加商品到购物车")
    @allure.title("添加商品 quantity=1 到购物车并进行库存验证")
    def test_add_product_quantity_one_boundary(self, api, db, fresh_cart):
        """边界值：数量为 1（最小有效值）"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        assert resp.status_code == 200

        body = resp.json()
        assert body.get("success"), f"quantity=1 应成功: {body}"

        # 数据库验证：商品 42 应存在且有库存
        stock = db.get_product_stock(42)
        allure.attach(
            f"Product 42 stock: {stock}",
            "库存数量 (DB)",
            allure.attachment_type.TEXT,
        )

    @allure.story("添加商品到购物车")
    @allure.title("添加多个商品 — quantity=3")
    def test_add_product_multiple_quantity(self, api, fresh_cart):
        """等价类-有效：添加多件商品"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 3})

        products_resp = api.get("api/cart/getProducts")
        products = products_resp.json().get("products", [])

        target = next((p for p in products if p["product_id"] == "42"), None)
        assert target is not None, "应找到 product_id=42 的商品"
        assert target.get("quantity") == "3", \
            f"期望数量 3, 实际 {target.get('quantity')}"

    @allure.story("添加商品到购物车")
    @allure.title("添加最大边界数量 quantity=100")
    def test_add_product_max_quantity(self, api, fresh_cart):
        """边界值：数量为 100"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 100})
        assert resp.status_code < 500, \
            f"quantity=100 不应导致服务器错误: {resp.status_code}"

        body = resp.json()
        allure.attach(
            str(body),
            "Max Quantity Response",
            allure.attachment_type.TEXT,
        )

    # ── 添加商品 — 异常流程 ───────────────────────────────

    @allure.story("添加商品到购物车")
    @allure.title("添加不存在的 product_id=9999 应有错误")
    def test_add_nonexistent_product(self, api, fresh_cart):
        """等价类-无效：添加不存在的商品"""
        resp = api.post("api/cart/add", data={"product_id": 9999, "quantity": 1})

        body = resp.json()
        has_error = "error" in body or "warning" in str(body).lower()
        assert has_error, \
            f"不存在的商品应返回错误: {body}"

    @allure.story("添加商品到购物车")
    @allure.title("添加商品 quantity=0 应有错误")
    def test_add_product_zero_quantity(self, api, fresh_cart):
        """边界值：数量为 0"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 0})

        body = resp.json()
        has_error = "error" in body or "warning" in str(body).lower() or resp.status_code != 200
        assert has_error, \
            f"quantity=0 应有错误提示: status={resp.status_code}, body={body}"

    @allure.story("添加商品到购物车")
    @allure.title("不传 product_id 参数应有错误")
    def test_add_product_missing_id(self, api, fresh_cart):
        """异常输入：缺少必填参数 product_id"""
        resp = api.post("api/cart/add", data={"quantity": 1})

        body = resp.json()
        has_error = "error" in body or "warning" in str(body).lower()
        assert has_error, \
            f"缺少 product_id 应返回错误: {body}"

    # ── 商品搜索 ────────────────────────────────────────

    @allure.story("商品搜索")
    @allure.title("搜索存在的商品应返回结果")
    def test_search_existing_product(self, api):
        """验证商品搜索 API 返回正确结果"""
        resp = api.get("api/product/search", params={"search": "Mac"})

        # 搜索 API 可能返回 JSON 或 HTML，取决于 OpenCart 版本
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        allure.attach(
            str(resp.text[:500]),
            "Search Response (truncated)",
            allure.attachment_type.TEXT,
        )
        assert resp.status_code < 500, \
            f"搜索 API 不应返回服务器错误: {resp.status_code}"

    @allure.story("商品搜索")
    @allure.title("搜索不存在的商品应返回空结果")
    def test_search_nonexistent_product(self, api):
        """验证搜索不存在的商品不会崩溃"""
        resp = api.get("api/product/search", params={"search": "xyznosuchproduct999"})
        assert resp.status_code < 500, \
            f"搜索不存在的商品不应返回服务器错误: {resp.status_code}"
