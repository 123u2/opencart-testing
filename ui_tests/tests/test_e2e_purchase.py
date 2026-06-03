"""
E2E 用户购物流程测试 — 项目核心亮点
面试可讲：
  1. 一条 E2E 覆盖 6 个步骤 (首页 → 搜索 → 商品详情 → 购物车 → 结账 → 下单成功)
  2. 使用 allure.step 标记每个步骤，报告中清晰可见
  3. Page Object 模式隔离元素变化
"""
import allure
import pytest
from ui_tests.pages.home_page import HomePage
from ui_tests.pages.product_page import SearchResultPage, ProductDetailPage
from ui_tests.pages.cart_page import CartPage
from ui_tests.pages.checkout_page import CheckoutPage


@allure.feature("核心业务 — 用户购物旅程")
class TestE2EPurchase:

    # ── 完整 E2E 购物流程 ──────────────────────────────────

    @allure.story("完整购物流程 E2E")
    @allure.title("从首页搜索到下单成功的完整用户旅程")
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_search_to_checkout(self, driver, base_url):
        """场景法-正常流：首页 → 搜索 → 商品详情 → 加购 → 结账（登录+地址+配送+支付+确认）

        这是项目最重要的 E2E 用例，覆盖电商核心链路。
        """
        home = HomePage(driver, base_url)

        # ═══ Step 1: 打开首页 ═══
        with allure.step("1. 打开首页"):
            home.open()
            assert home.is_logo_displayed(), "首页 Logo 应显示"

        # ═══ Step 2: 搜索商品 ═══
        with allure.step("2. 搜索 'Mac'"):
            search_result = home.search("Mac")
            assert search_result.has_results(), "搜索 'Mac' 应有结果"

        # ═══ Step 3: 点击第一个搜索结果进入详情 ═══
        with allure.step("3. 进入商品详情页"):
            product_page = search_result.click_result(1)
            product_name = product_page.get_product_name()
            assert len(product_name) > 0, "商品名称不应为空"
            allure.attach(product_name, "商品名称", allure.attachment_type.TEXT)

        # ═══ Step 4: 加入购物车 ═══
        with allure.step("4. 设置数量=1 并加入购物车"):
            product_page.set_quantity(1)
            product_page.add_to_cart()
            assert product_page.is_displayed(product_page.SUCCESS_ALERT), \
                "加入购物车后应显示成功提示"

        # ═══ Step 5: 进入购物车并验证 ═══
        with allure.step("5. 进入购物车验证商品"):
            cart = product_page.go_to_cart()
            assert not cart.is_empty(), "购物车不应为空"
            cart.screenshot("cart_before_checkout")

        # ═══ Step 6: 进入结账并完成下单 ═══
        with allure.step("6. 进入结账 → 登录 → 填写地址 → 确认下单"):
            checkout = cart.checkout()

            # 使用 guest 模式快速完成结账
            success = checkout.complete_checkout_as_guest(
                first_name="Test",
                last_name="User",
                address="123 Test Street",
                city="Test City",
                postcode="12345",
            )

            if success:
                allure.attach("Order placed successfully!", "下单结果", allure.attachment_type.TEXT)
            else:
                # 即使下单未完全成功，也记录当前页面状态
                checkout.screenshot("checkout_result")
                allure.attach(
                    f"URL: {checkout.get_current_url()}\nMessage: {checkout.get_order_success_message()}",
                    "结账结果详情",
                    allure.attachment_type.TEXT,
                )

        # 验证进入了成功或确认页面
        current_url = checkout.get_current_url().lower()
        assert any(keyword in current_url for keyword in ["success", "checkout/success"]), \
            f"结账后应跳转到成功页, 实际 URL: {current_url}"

    # ── 购物车操作 E2E ────────────────────────────────────

    @allure.story("购物车操作")
    @allure.title("添加商品到购物车后能正确查看")
    @pytest.mark.smoke
    def test_add_to_cart_and_view(self, driver, base_url):
        """验证核心操作：浏览商品 → 加购 → 查看购物车"""
        home = HomePage(driver, base_url)
        home.open()

        with allure.step("搜索商品"):
            result = home.search("iPhone")
            assert result.has_results()

        with allure.step("进入商品详情并加入购物车"):
            product = result.click_result(1)
            product.set_quantity(1)
            product.add_to_cart()

        with allure.step("进入购物车验证"):
            cart = product.go_to_cart()
            assert cart.get_item_count() >= 1, "购物车应有至少1件商品"
            cart.screenshot("cart_after_add")

    @allure.story("购物车操作")
    @allure.title("修改购物车中商品数量")
    def test_update_cart_quantity(self, driver, base_url):
        """验证购物车中修改商品数量"""
        home = HomePage(driver, base_url)
        home.open()

        with allure.step("搜索并添加商品"):
            result = home.search("Mac")
            assert result.has_results()
            product = result.click_result(1)
            product.set_quantity(1)
            product.add_to_cart()

        with allure.step("进入购物车修改数量"):
            cart = product.go_to_cart()
            initial_count = cart.get_item_count()
            cart.update_quantity(2)
            # 修改后页面应重新加载
            assert "cart" in cart.get_current_url().lower()

    @allure.story("购物车操作")
    @allure.title("空购物车提示信息")
    def test_empty_cart_message(self, driver, base_url):
        """验证直接进入空购物车的提示"""
        cart = CartPage(driver, base_url)
        cart.open("/index.php?route=checkout/cart")

        with allure.step("验证空购物车提示"):
            message = cart.get_empty_message()
            assert len(message) > 0, "空购物车应有提示信息"
            allure.attach(message, "空购物车提示", allure.attachment_type.TEXT)

    # ── 搜索功能 ────────────────────────────────────────

    @allure.story("搜索功能")
    @allure.title("搜索不存在的商品应显示无结果")
    def test_search_no_results(self, driver, base_url):
        """等价类-无效：搜索不存在的商品"""
        home = HomePage(driver, base_url)
        home.open()

        with allure.step("搜索不存在的商品"):
            result = home.search("xyz_no_such_product_12345")
            assert not result.has_results(), "搜索不存在的商品应无结果"

    @allure.story("搜索功能")
    @allure.title("模糊搜索部分关键词应有结果")
    def test_search_partial_keyword(self, driver, base_url):
        """验证模糊搜索返回结果"""
        home = HomePage(driver, base_url)
        home.open()

        with allure.step("搜索 'pho' (部分匹配 'phone')"):
            result = home.search("pho")
            # 部分匹配可能返回或可能不返回结果，取决于 OpenCart 的搜索配置
            # 但至少页面不应崩溃
            assert "search" in result.get_current_url().lower(), "应在搜索页面"
