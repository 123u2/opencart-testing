"""
E2E 用户购物流程测试 — 项目核心亮点
面试可讲：
  1. 一条 E2E 覆盖 5 个页面 (首页 → 搜索 → 商品详情 → 购物车 → 结账)
  2. 使用 allure.step 标记每个步骤，报告中清晰可见
  3. Page Object 模式隔离元素变化
"""
import allure
import pytest
from ui_tests.pages.home_page import HomePage
from ui_tests.pages.product_page import SearchResultPage, ProductDetailPage
from ui_tests.pages.cart_page import CartPage


@allure.feature("核心业务 — 用户购物旅程")
class TestE2EPurchase:

    @allure.story("完整购物流程 E2E")
    @allure.title("从首页搜索商品到下单成功的完整用户旅程")
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_search_to_checkout(self, driver, base_url):
        """场景法-正常流：首页 → 搜索 → 商品详情 → 加购 → 结账

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

        # ═══ Step 3: 进入商品详情 ═══
        with allure.step("3. 点击第一个搜索结果"):
            product_page = search_result.click_result(1)
            product_name = product_page.get_product_name()
            assert len(product_name) > 0, "商品名称不应为空"
            allure.attach(product_name, "商品名称", allure.attachment_type.TEXT)

        # ═══ Step 4: 加入购物车 ═══
        with allure.step("4. 设置数量=2 并加入购物车"):
            product_page.set_quantity(2)
            product_page.add_to_cart()
            # 验证成功提示出现
            assert product_page.is_displayed(product_page.SUCCESS_ALERT), \
                "加入购物车后应显示成功提示"

        # ═══ Step 5: 进入购物车 ═══
        with allure.step("5. 进入购物车验证商品"):
            cart = product_page.go_to_cart()
            assert not cart.is_empty(), "购物车不应为空"

        # ═══ Step 6: 进入结账 ═══
        with allure.step("6. 进入结账流程"):
            checkout = cart.checkout()
            # 验证已进入结账页面
            assert "checkout" in checkout.get_current_url().lower(), \
                "应跳转到结账页面"

        allure.attach(
            checkout.get_current_url(),
            "结账页 URL",
            allure.attachment_type.TEXT,
        )

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

    @allure.story("搜索功能")
    @allure.title("搜索不存在的商品应显示无结果")
    def test_search_no_results(self, driver, base_url):
        """等价类-无效：搜索不存在的商品"""
        home = HomePage(driver, base_url)
        home.open()

        with allure.step("搜索不存在的商品"):
            result = home.search("xyz_no_such_product_12345")
            assert not result.has_results(), "搜索不存在的商品应无结果"
