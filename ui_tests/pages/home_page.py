"""
首页 Page Object
面试可讲：一个 Page Object = 元素定位 + 业务操作
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class HomePage(BasePage):
    """OpenCart 首页"""

    # ── 元素定位 ──
    SEARCH_INPUT = (By.NAME, "search")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "#search button, button[type='submit']")
    MY_ACCOUNT = (By.CSS_SELECTOR, ".dropdown-toggle[title='My Account'], a[title='My Account']")
    LOGIN_LINK = (By.LINK_TEXT, "Login")
    REGISTER_LINK = (By.LINK_TEXT, "Register")
    CART_BUTTON = (By.CSS_SELECTOR, ".btn-inverse, #cart button")
    LOGO = (By.CSS_SELECTOR, "#logo a, .navbar-brand")

    # ── 页面操作 ──

    def search(self, keyword: str):
        """在搜索框输入关键词并搜索，返回搜索结果页"""
        self.send_keys(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)
        from .product_page import SearchResultPage
        return SearchResultPage(self.driver, self.base_url)

    def go_to_login(self):
        """导航到登录页"""
        # 点击 My Account → Login
        self.click(self.MY_ACCOUNT)
        self.click(self.LOGIN_LINK)
        from .checkout_page import LoginPage
        return LoginPage(self.driver, self.base_url)

    def go_to_register(self):
        """导航到注册页"""
        self.click(self.MY_ACCOUNT)
        self.click(self.REGISTER_LINK)

    def get_featured_products(self) -> int:
        """获取首页特色商品数量"""
        products = self.find_all((By.CSS_SELECTOR, ".product-thumb"))
        return len(products)

    def is_logo_displayed(self) -> bool:
        """检查 Logo 是否显示"""
        return self.is_displayed(self.LOGO)
