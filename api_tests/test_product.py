"""
商品模块 API 测试
覆盖：获取购物车中的商品、添加商品、JSON Schema 校验
"""
import json
import allure
import pytest
from jsonschema import validate, ValidationError


@allure.feature("商品模块")
class TestProduct:

    @allure.story("获取购物车商品列表")
    @allure.title("空购物车 getProducts 应返回空列表")
    def test_get_empty_cart(self, api, fresh_cart):
        """验证空购物车时 API 返回空商品列表"""
        resp = api.get("api/cart/getProducts")
        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"

        body = resp.json()
        assert len(body.get("products", [])) == 0, \
            f"空购物车 product 列表应为空: {body}"
        # 无商品时不应有 error
        assert "error" not in body or body.get("error") is None, \
            f"空购物车不应有 error: {body}"

    @allure.story("JSON Schema 校验")
    @allure.title("getProducts 响应应符合 JSON Schema 结构")
    def test_get_products_schema(self, api):
        """验证 API 响应结构符合预期 Schema（契约测试）"""
        # 先添加一个商品以确保有数据
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        resp = api.get("api/cart/getProducts")
        body = resp.json()

        # 加载 Schema 文件
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "schemas", "product.json"
        )
        with open(schema_path, "r") as f:
            schema = json.load(f)

        try:
            validate(instance=body, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Schema 校验失败: {e.message}")

    @allure.story("添加商品到购物车")
    @allure.title("添加存在的商品 product_id=42 应成功")
    def test_add_product_success(self, api, fresh_cart):
        """等价类-有效：添加存在的商品"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        assert resp.status_code == 200

        body = resp.json()
        # 成功时应有 success 字段
        assert "success" in body, f"应返回 success: {body}"

        # 验证购物车中确实有商品
        products_resp = api.get("api/cart/getProducts")
        products = products_resp.json().get("products", [])
        assert len(products) >= 1, "添加商品后购物车不应为空"

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
    @allure.title("添加不存在的 product_id=9999 应有错误")
    def test_add_nonexistent_product(self, api, fresh_cart):
        """等价类-无效：添加不存在的商品"""
        resp = api.post("api/cart/add", data={"product_id": 9999, "quantity": 1})

        body = resp.json()
        # 预期包含 error 或 warning
        assert "error" in body or "warning" in str(body).lower(), \
            f"不存在的商品应返回错误: {body}"

    @allure.story("添加商品到购物车")
    @allure.title("添加商品 quantity=0 应有错误")
    def test_add_product_zero_quantity(self, api, fresh_cart):
        """边界值：数量为 0"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 0})

        body = resp.json()
        # 预期不允许数量为 0
        assert "error" in body or "warning" in str(body).lower() or resp.status_code != 200, \
            f"quantity=0 应有错误提示: {body}"
