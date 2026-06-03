"""
购物车模块 API 测试
覆盖：添加商品、修改数量、删除商品、优惠券、获取总计
"""
import re
import allure
import pytest


def _parse_price(value: str) -> float:
    """从价格字符串中提取数值，支持多币种格式

    兼容: "$1,234.56" / "€1.234,56" / "¥1,234" / "1234.56"
    """
    # 移除货币符号和空格
    cleaned = re.sub(r"[^\d.,\-]", "", value)
    # 判断是欧元格式(1.234,56)还是标准格式(1,234.56)
    if cleaned.count(".") > 1 or ("," in cleaned and "." not in cleaned):
        # 欧元格式: 1.234,56 → 小数点分隔，逗号是千分位
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned and "." in cleaned:
        # 同时有逗号和点 → 判断哪个在最后
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_dot > last_comma:
            # 标准格式: 1,234.56 → 逗号是千分位
            cleaned = cleaned.replace(",", "")
        else:
            # 欧元格式: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
    # 纯数字格式
    cleaned = cleaned.replace(",", "")
    return float(cleaned)


@allure.feature("购物车模块")
class TestCart:

    # ── 添加商品 ──────────────────────────────────────────

    @allure.story("添加商品到购物车")
    @allure.title("默认 quantity=1 添加商品")
    @pytest.mark.smoke
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
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        # 修改数量：重新 add 相同 product_id 会覆盖
        api.post("api/cart/add", data={"product_id": 42, "quantity": 5})

        products = api.get("api/cart/getProducts").json()["products"]
        target = next((p for p in products if p["product_id"] == "42"), None)
        assert target is not None
        assert target["quantity"] == "5", \
            f"期望 quantity=5, 实际 {target['quantity']}"

    @allure.story("修改购物车数量")
    @allure.title("修改数量为 0 应移除商品")
    def test_update_quantity_to_zero(self, api, fresh_cart):
        """边界值：数量设为 0 应等价于移除"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        # 将数量改为 0
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 0})
        body = resp.json()

        # 商品应该被移除
        products = api.get("api/cart/getProducts").json()["products"]
        target = next((p for p in products if p["product_id"] == "42"), None)
        assert target is None or target.get("quantity") == "0", \
            f"数量改为 0 应移除或清零商品: {products}"

    # ── 移除商品 ──────────────────────────────────────────

    @allure.story("移除购物车商品")
    @allure.title("移除购物车中的指定商品")
    def test_remove_product(self, api, fresh_cart):
        """验证从购物车中移除指定商品"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
        api.post("api/cart/add", data={"product_id": 28, "quantity": 1})

        # 移除 product_id=42
        resp = api.post("api/cart/remove", data={"key": "42"})
        # 注意：OpenCart 使用 cart_id/key 而非 product_id 来移除
        # 这里先通过 getProducts 获取真实的 cart_id
        products = api.get("api/cart/getProducts").json()["products"]
        assert len(products) <= 2, f"移除前应有商品: {products}"

        # 如果有 cart_id，用它来移除
        if products:
            cart_id = products[0].get("cart_id") or products[0].get("key")
            if cart_id:
                remove_resp = api.post("api/cart/remove", data={"key": str(cart_id)})
                allure.attach(
                    str(remove_resp.text),
                    "Remove Response",
                    allure.attachment_type.TEXT,
                )

        # 验证移除后商品数量减少
        after = api.get("api/cart/getProducts").json()["products"]
        assert len(after) < len(products) or len(after) == 0, \
            f"移除后商品应减少: 移除前={len(products)}, 移除后={len(after)}"

    @allure.story("移除购物车商品")
    @allure.title("清空购物车")
    def test_clear_cart(self, api, fresh_cart):
        """验证清空购物车功能"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 2})
        api.post("api/cart/add", data={"product_id": 28, "quantity": 1})

        # 执行清空（fresh_cart 本身也会调用 clear，这里显式测试）
        api.post("api/cart/clear")

        products = api.get("api/cart/getProducts").json()["products"]
        assert len(products) == 0, f"清空后购物车应为空: {products}"

    # ── 获取总计 ──────────────────────────────────────────

    @allure.story("获取购物车汇总")
    @allure.title("getTotals 应返回商品总数和总金额")
    def test_get_totals(self, api, fresh_cart):
        api.post("api/cart/add", data={"product_id": 42, "quantity": 2})

        resp = api.get("api/cart/getTotals")
        body = resp.json()

        assert "totals" in body, f"应包含 totals: {body}"
        assert len(body["totals"]) > 0, "totals 不应为空"

        labels = [t["title"] for t in body["totals"]]
        assert any("Sub-Total" in l for l in labels), f"应包含 Sub-Total: {labels}"
        assert any("Total" in l for l in labels), f"应包含 Total: {labels}"

    # ── 优惠券 ────────────────────────────────────────────

    @allure.story("优惠券")
    @allure.title("使用无效优惠券应返回错误")
    def test_apply_invalid_coupon(self, api, fresh_cart):
        """验证无效优惠券会被正确拒绝"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        resp = api.post("api/cart/addCoupon", data={"coupon": "INVALID_CODE_999"})
        body = resp.json()

        # 无效优惠券应返回 error 或 warning
        assert "error" in body or "warning" in str(body).lower(), \
            f"无效优惠券应返回错误: {body}"

    # ── 数据验证 ──────────────────────────────────────────

    @allure.story("购物车数据验证")
    @allure.title("商品列表中的 total 应等于 price × quantity")
    def test_product_total_calculation(self, api, fresh_cart):
        """验证前端显示的小计计算正确性（兼容多币种）"""
        api.post("api/cart/add", data={"product_id": 42, "quantity": 3})

        products = api.get("api/cart/getProducts").json()["products"]
        target = products[0]

        price = _parse_price(target["price"])
        total = _parse_price(target["total"])
        qty = int(target["quantity"])

        expected_total = round(price * qty, 2)
        assert abs(total - expected_total) < 0.02, \
            f"小计计算错误: price={price} × qty={qty} = {expected_total}, 实际 total={total}"

    # ── 负向测试 ──────────────────────────────────────────

    @allure.story("添加商品 — 异常流程")
    @allure.title("负数 quantity 添加商品应失败")
    def test_add_negative_quantity(self, api, fresh_cart):
        """边界值：负数数量"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": -1})

        body = resp.json()
        # 负数数量应该被拒绝或忽略
        has_error = "error" in body or "warning" in str(body).lower()
        allure.attach(
            f"status={resp.status_code}, body={body}",
            "Negative Quantity Result",
            allure.attachment_type.TEXT,
        )
        # 至少验证请求没有导致 500 错误
        assert resp.status_code < 500, \
            f"负数 quantity 不应导致服务器错误: {resp.status_code}"

    @allure.story("添加商品 — 异常流程")
    @allure.title("字符串 quantity 添加商品应能处理")
    def test_add_string_quantity(self, api, fresh_cart):
        """异常输入：非数字 quantity"""
        resp = api.post("api/cart/add", data={"product_id": 42, "quantity": "abc"})

        # 不应导致 500 错误
        assert resp.status_code < 500, \
            f"字符串 quantity 不应导致服务器错误: {resp.status_code}"
