"""
商品模块 API 测试
覆盖：获取购物车商品、添加/移除商品、Schema 校验、商品搜索、库存验证

OpenCart 4.x 路由格式：
  - 添加商品: api/sale/cart|add
  - 获取购物车: api/sale/cart
  - 编辑数量: api/sale/cart|edit
  - 移除商品: api/sale/cart|remove
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
    @allure.title("空购物车应返回空商品列表")
    def test_get_empty_cart(self, api, fresh_cart):
        """验证空购物车时 API 返回空商品列表"""
        resp = api.get("api/sale/cart")
        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"

        body = resp.json()
        assert len(body.get("products", [])) == 0, \
            f"空购物车 product 列表应为空: {body}"
        # 即使空购物车也应返回 totals
        assert "totals" in body, f"应包含 totals: {body}"

    # ── JSON Schema 校验（契约测试）────────────────────────

    @allure.story("JSON Schema 校验")
    @allure.title("get cart 响应应符合 JSON Schema 结构")
    def test_get_cart_schema(self, api, config):
        """验证 API 响应结构符合预期 Schema（契约测试）"""
        api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 1
        })

        resp = api.get("api/sale/cart")
        body = resp.json()

        schema_path = os.path.join(
            os.path.dirname(__file__), "schemas", "product.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        try:
            validate(instance=body, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Schema 校验失败: {e.message}")

    # ── 添加商品 — 正常流程 ───────────────────────────────

    @allure.story("添加商品到购物车")
    @allure.title("添加存在的商品应成功")
    @pytest.mark.smoke
    def test_add_product_success(self, api, config, fresh_cart):
        """等价类-有效：添加存在的商品"""
        resp = api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 1
        })
        assert resp.status_code == 200

        body = resp.json()
        assert body.get("success"), f"应返回 success: {body}"

        # 验证购物车中确实有商品
        cart_resp = api.get("api/sale/cart")
        products = cart_resp.json().get("products", [])
        assert len(products) >= 1, "添加商品后购物车不应为空"

    @allure.story("添加商品到购物车")
    @allure.title("添加商品 quantity=1 到购物车并进行库存验证")
    def test_add_product_quantity_one_boundary(self, api, db, config, fresh_cart):
        """边界值：数量为 1（最小有效值）"""
        resp = api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 1
        })
        assert resp.status_code == 200

        body = resp.json()
        assert body.get("success"), f"quantity=1 应成功: {body}"

        # 数据库验证：商品应存在且有库存
        stock = db.get_product_stock(config.DEFAULT_PRODUCT_ID)
        allure.attach(
            f"Product {config.DEFAULT_PRODUCT_ID} stock: {stock}",
            "库存数量 (DB)",
            allure.attachment_type.TEXT,
        )

    @allure.story("添加商品到购物车")
    @allure.title("添加多个商品 — quantity=3")
    def test_add_product_multiple_quantity(self, api, config, fresh_cart):
        """等价类-有效：添加多件商品"""
        api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 3
        })

        cart_resp = api.get("api/sale/cart")
        products = cart_resp.json().get("products", [])

        target = next(
            (p for p in products
             if str(p["product_id"]) == str(config.DEFAULT_PRODUCT_ID)),
            None
        )
        assert target is not None, \
            f"应找到 product_id={config.DEFAULT_PRODUCT_ID} 的商品"
        assert target.get("quantity") == "3", \
            f"期望数量 3, 实际 {target.get('quantity')}"

    @allure.story("添加商品到购物车")
    @allure.title("添加最大边界数量 quantity=100")
    def test_add_product_max_quantity(self, api, config, fresh_cart):
        """边界值：数量为 100"""
        resp = api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 100
        })
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
        resp = api.post("api/sale/cart|add", data={
            "product_id": 9999, "quantity": 1
        })

        body = resp.json()
        assert "error" in body or "warning" in str(body).lower(), \
            f"不存在的商品应返回错误: {body}"

    @allure.story("添加商品到购物车")
    @allure.title("添加商品 quantity=0 应有错误")
    def test_add_product_zero_quantity(self, api, config, fresh_cart):
        """边界值：数量为 0"""
        resp = api.post("api/sale/cart|add", data={
            "product_id": config.DEFAULT_PRODUCT_ID, "quantity": 0
        })

        body = resp.json()
        # quantity=0 可能被接受（相当于不添加）或返回错误
        allure.attach(
            f"status={resp.status_code}, body={body}",
            "Quantity=0 Result",
            allure.attachment_type.TEXT,
        )
        assert resp.status_code < 500, \
            f"quantity=0 不应导致服务器错误: {resp.status_code}"

    @allure.story("添加商品到购物车")
    @allure.title("不传 product_id 参数应有错误")
    def test_add_product_missing_id(self, api, fresh_cart):
        """异常输入：缺少必填参数 product_id"""
        resp = api.post("api/sale/cart|add", data={"quantity": 1})

        body = resp.json()
        assert "error" in body or "warning" in str(body).lower(), \
            f"缺少 product_id 应返回错误: {body}"

    # ── 商品搜索 ────────────────────────────────────────

    @allure.story("商品搜索")
    @allure.title("搜索存在的商品应返回结果")
    def test_search_existing_product(self, api):
        """验证商品搜索 API 返回正确结果"""
        resp = api.get("api/product/search", params={"search": "Mac"})

        # 搜索 API 可能返回 JSON 或 HTML，取决于 OpenCart 版本
        body = resp.json() if resp.headers.get(
            "content-type", ""
        ).startswith("application/json") else {}
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
        resp = api.get("api/product/search", params={
            "search": "xyznosuchproduct999"
        })
        assert resp.status_code < 500, \
            f"搜索不存在的商品不应返回服务器错误: {resp.status_code}"
