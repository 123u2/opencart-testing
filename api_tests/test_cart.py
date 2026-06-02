"""
购物车模块 API 测试
覆盖：添加商品、修改数量、删除商品、获取总计
"""
import allure
import pytest


@allure.feature("购物车模块")
class TestCart:

    # ── 添加商品 ──────────────────────────────────────────

    @allure.story("添加商品到购物车")
    @allure.title("默认 quantity=1 添加商品")
    def test_add_single_product(self, api, fresh_cart):
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        body = resp.json()
        assert "success" in body, f"添加商品应成功: {body}"

    @allure.story("添加商品到购物车")
    @allure.title("连续添加两件不同商品")
    def test_add_two_different_products(self, api, fresh_cart):
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        api.post("api/cart/add", data={"product_id": 28, "quantity": 1})

        products = api.get("api/cart/getProducts").json()["products"]
        product_ids = [p["product_id"] for p in products]
        assert "42" in product_ids, f"应包含 product_id=42: {product_ids}"
        assert "28" in product_ids, f"应包含 product_id=28: {product_ids}"
        assert len(products) == 2, f"应有 2 件商品: {len(products)}"

    # ── 修改数量 ──────────────────────────────────────────

    @allure.story("修改购物车数量")
    @allure.title("修改商品数量 1→5")
    def test_update_quantity(self, api, fresh_cart):
        # 先添加
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        # 修改数量：重新 add 相同 product_id 会覆盖
        api.post("api/cart/add", data={"product_id": 42, "quantity": 5})

        products = api.get("api/cart/getProducts").json()["products"]
        target = next((p for p in products if p["product_id"] == "42"), None)
        assert target is not None
        assert target["quantity"] == "5", \
            f"期望 quantity=5, 实际 {target['quantity']}"

    # ── 获取总计 ──────────────────────────────────────────

    @allure.story("获取购物车汇总")
    @allure.title("getTotals 应返回商品总数和总金额")
    def test_get_totals(self, api, fresh_cart):
        api.post("api/cart/add", data={"product_id": 42, "quantity": 2})

        resp = api.get("api/cart/getTotals")
        body = resp.json()

        assert "totals" in body, f"应包含 totals: {body}"
        assert len(body["totals"]) > 0, "totals 不应为空"

        # totals 包含 Sub-Total, Total 等行
        labels = [t["title"] for t in body["totals"]]
        assert any("Sub-Total" in l for l in labels), f"应包含 Sub-Total: {labels}"
        assert any("Total" in l for l in labels), f"应包含 Total: {labels}"

    # ── 数据验证 ──────────────────────────────────────────

    @allure.story("购物车数据验证")
    @allure.title("商品列表中的 total 应等于 price × quantity")
    def test_product_total_calculation(self, api, fresh_cart):
        """验证前端显示的小计计算正确性"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 3})

        products = api.get("api/cart/getProducts").json()["products"]
        target = products[0]

        price = float(target["price"].replace("$", "").replace(",", ""))
        total = float(target["total"].replace("$", "").replace(",", ""))
        qty = int(target["quantity"])

        expected_total = round(price * qty, 2)
        assert abs(total - expected_total) < 0.02, \
            f"小计计算错误: price={price} × qty={qty} = {expected_total}, 实际 total={total}"
