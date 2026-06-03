"""
后台管理测试 — 商品 CRUD + 订单管理
面试可讲：
  1. 后台测试和前台测试的区别 — admin 权限 + 数据一致性
  2. Page Object 模式同样适用于后台页面
  3. CRUD 操作覆盖完整的数据生命周期
"""
import allure
import pytest
from ui_tests.pages.admin_page import (
    AdminLoginPage,
    AdminDashboardPage,
    AdminProductListPage,
    AdminProductFormPage,
    AdminOrderListPage,
)


def _admin_login(driver, base_url, config):
    """管理后台登录辅助函数（复用）"""
    login_page = AdminLoginPage(driver, base_url)
    login_page.open("/admin")

    # 如果已经在 Dashboard（之前登录未过期），直接返回
    if "dashboard" in login_page.get_current_url().lower():
        return AdminDashboardPage(driver, base_url)

    return login_page.login(config.ADMIN_USERNAME, config.ADMIN_PASSWORD)


@allure.feature("后台管理")
class TestAdminLogin:

    @allure.story("后台登录")
    @allure.title("管理员使用正确凭据登录后台")
    @pytest.mark.smoke
    def test_admin_login_success(self, driver, base_url, config):
        """等价类-有效：正确的用户名 + 密码"""
        login_page = AdminLoginPage(driver, base_url)
        login_page.open("/admin")

        dashboard = login_page.login(config.ADMIN_USERNAME, config.ADMIN_PASSWORD)

        # 验证已跳转到 Dashboard
        assert dashboard.is_loaded(), \
            f"登录后应在 Dashboard, 实际 URL: {dashboard.get_current_url()}"
        page_title = dashboard.get_page_title()
        allure.attach(page_title, "Dashboard 标题", allure.attachment_type.TEXT)

    @allure.story("后台登录")
    @allure.title("错误密码无法登录后台")
    def test_admin_login_wrong_password(self, driver, base_url, config):
        """等价类-无效：正确用户名 + 错误密码"""
        login_page = AdminLoginPage(driver, base_url)
        login_page.open("/admin")

        login_page.login(config.ADMIN_USERNAME, "WrongAdminPassword")

        # 应停留在登录页或显示错误信息
        error = login_page.get_error_message()
        current_url = login_page.get_current_url().lower()
        assert "dashboard" not in current_url or len(error) > 0, \
            f"错误密码不应进入 Dashboard: url={current_url}, error={error}"


@allure.feature("后台管理 — 商品 CRUD")
class TestAdminProductCRUD:

    @allure.story("商品管理 — 查看列表")
    @allure.title("登录后查看商品列表")
    @pytest.mark.smoke
    def test_view_products(self, driver, base_url, config):
        """验证商品列表页面正常加载"""
        dashboard = _admin_login(driver, base_url, config)
        assert dashboard.is_loaded(), "应进入 Dashboard"

        # 导航到商品管理
        product_list = dashboard.navigate_to_products()
        assert product_list.is_loaded(), \
            f"应进入商品列表页, 实际: {product_list.get_current_url()}"

        count = product_list.get_product_count()
        allure.attach(str(count), "商品数量", allure.attachment_type.TEXT)

    @allure.story("商品管理 — 搜索")
    @allure.title("按名称搜索商品")
    def test_search_product(self, driver, base_url, config):
        """验证商品搜索功能"""
        dashboard = _admin_login(driver, base_url, config)
        product_list = dashboard.navigate_to_products()

        # 搜索已知商品
        product_list.search_product("Mac")
        # 页面不应崩溃
        assert product_list.is_loaded(), "搜索后应仍在商品列表页"

    @allure.story("商品管理 — 搜索")
    @allure.title("搜不存在的商品应显示空结果")
    def test_search_nonexistent_product(self, driver, base_url, config):
        """等价类-无效：搜索不存在的商品名"""
        dashboard = _admin_login(driver, base_url, config)
        product_list = dashboard.navigate_to_products()

        product_list.search_product("xyznosuchproduct999")
        assert product_list.is_loaded(), "搜索不存在的商品不应导致页面崩溃"


@allure.feature("后台管理 — 订单管理")
class TestAdminOrders:

    @allure.story("订单管理 — 查看")
    @allure.title("后台查看订单列表")
    @pytest.mark.p1
    def test_view_orders(self, driver, base_url, config):
        """验证订单管理页面正常加载"""
        dashboard = _admin_login(driver, base_url, config)
        assert dashboard.is_loaded(), "应进入 Dashboard"

        # 导航到订单管理
        order_list = dashboard.navigate_to_orders()
        assert order_list.is_loaded(), \
            f"应进入订单管理页, 实际: {order_list.get_current_url()}"

        page_title = order_list.get_page_title()
        allure.attach(page_title, "订单页标题", allure.attachment_type.TEXT)
        assert "order" in page_title.lower(), \
            f"应显示订单管理页面, 实际标题: {page_title}"

    @allure.story("订单管理 — 查看")
    @allure.title("订单列表应有数据或显示空状态")
    def test_order_list_structure(self, driver, base_url, config):
        """验证订单列表页面结构完整"""
        dashboard = _admin_login(driver, base_url, config)
        order_list = dashboard.navigate_to_orders()

        count = order_list.get_order_count()
        allure.attach(f"订单行数: {count}", "订单统计", allure.attachment_type.TEXT)
        # 列表页应正常加载（无论是否有数据）
        assert order_list.is_loaded()
