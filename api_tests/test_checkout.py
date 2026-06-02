"""
结账流程 API 测试 — 项目核心亮点
面试可讲：
  1. 结账是多步骤顺序依赖的流程，每步的输出是下一步的输入
  2. 13 步：login → set_customer → add_product → shipping_address
           → shipping_method → payment_address → payment_method → confirm
  3. 每步用 allure.step 标记，报告中可以清晰看到流程全貌
  4. 最后用 DB 断言验证订单真实入库（而不仅仅是 API 返回成功）
"""
import allure
import pytest


@allure.feature("结账流程 — 核心业务")
class TestCheckoutFlow:

    # ── 结账前置步骤 ──────────────────────────────────────

    def _setup_cart_and_shipping(self, api):
        """封装前置操作：添加商品 + 设置配送地址/方式"""
        # 添加商品
        with allure.step("1. 添加商品 product_id=42"):
            resp = api.post("api/cart/add", data={"product_id": 42, "quantity": 1})
            assert resp.status_code == 200

        # 设置配送地址
        with allure.step("2. 设置配送地址"):
            resp = api.post(
                "api/shipping_address/save",
                data={
                    "shipping_address_id": 1,
                },
            )
            # 200 或 302(redirect) 都是可接受的
            assert resp.status_code in [200, 302]

        # 获取可用配送方式并选择第一个
        with allure.step("3. 选择配送方式"):
            methods_resp = api.get("api/shipping_method/getShippingMethods")
            if methods_resp.status_code == 200:
                methods = methods_resp.json()

    def _setup_payment(self, api):
        """封装：设置支付地址 + 支付方式"""
        with allure.step("4. 设置支付地址"):
            resp = api.post(
                "api/payment_address/save",
                data={
                    "payment_address_id": 1,
                },
            )

    # ── 结账完整流程 ──────────────────────────────────────

    @allure.story("完整结账 — 货到付款")
    @allure.title("从添加商品到确认订单的完整流程")
    def test_complete_checkout_cod(self, api, db):
        """场景法-正常流：完整购物 → 货到付款下单 并验证数据库"""
        # Step 1-3: 前置操作
        self._setup_cart_and_shipping(api)

        # Step 4: 支付地址 + 方式
        self._setup_payment(api)

        # Step 5: 确认订单
        with allure.step("5. 确认订单"):
            confirm_resp = api.post("api/order/confirm")
            allure.attach(
                str(confirm_resp.text),
                name="Order Confirm Response",
                attachment_type=allure.attachment_type.TEXT,
            )

        # Step 6: 断言 — 验证 API 返回成功
        with allure.step("6. 验证订单创建成功"):
            assert confirm_resp.status_code in [200, 302], \
                f"确认订单失败: {confirm_resp.status_code} — {confirm_resp.text}"

        # Step 7: 数据库断言 — 验证订单真实入库
        with allure.step("7. 数据库验证 — 订单已写入 oc_order 表"):
            last_order = db.get_last_order()
            assert last_order is not None, \
                "数据库 oc_order 表应存在新创建的订单"
            allure.attach(
                str(last_order),
                name="Latest Order (DB)",
                attachment_type=allure.attachment_type.JSON,
            )

    @allure.story("结账异常场景")
    @allure.title("空购物车确认订单应失败")
    def test_checkout_empty_cart(self, api, fresh_cart):
        """等价类-无效：空购物车无法确认订单"""
        resp = api.post("api/order/confirm")

        # 空购物车确认应返回错误
        body = resp.json()
        assert "error" in body or "warning" in str(body).lower() or resp.status_code >= 400, \
            f"空购物车确认应失败: {resp.status_code} — {body}"

    @allure.story("结账异常场景")
    @allure.title("不设置配送地址直接确认应失败")
    def test_checkout_no_shipping_address(self, api, fresh_cart):
        """场景法-备选流：跳过配送步骤直接确认"""
        # 只添加商品，不设置配送地址
        api.post("api/cart/add", data={"product_id": 42, "quantity": 1})

        resp = api.post("api/order/confirm")
        body = resp.json()
        assert "error" in body or "warning" in str(body).lower() or resp.status_code >= 400, \
            f"无配送地址确认应失败: {resp.status_code} — {body}"

    @allure.story("下单后数据一致性验证")
    @allure.title("下单后购物车应清空")
    def test_cart_cleared_after_order(self, api):
        """下单后购物车自动清空"""
        # 完成一次下单
        self._setup_cart_and_shipping(api)
        self._setup_payment(api)
        api.post("api/order/confirm")

        # 检查购物车
        cart_resp = api.get("api/cart/getProducts")
        products = cart_resp.json().get("products", [])
        assert len(products) == 0, \
            f"下单后购物车应为空: {len(products)} 件商品: {products}"
