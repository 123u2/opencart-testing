"""
后台管理相关 Page Object
包含：登录页、Dashboard、商品管理、订单管理
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .base_page import BasePage


class AdminLoginPage(BasePage):
    """OpenCart 后台登录页 — /admin"""

    USERNAME_INPUT = (By.ID, "input-username")
    PASSWORD_INPUT = (By.ID, "input-password")
    LOGIN_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_ALERT = (By.CSS_SELECTOR, ".alert-danger")
    FORGOTTEN_LINK = (By.LINK_TEXT, "Forgotten Password")

    def login(self, username: str, password: str):
        """登录后台"""
        self.send_keys(self.USERNAME_INPUT, username)
        self.send_keys(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BTN)
        from .admin_page import AdminDashboardPage
        return AdminDashboardPage(self.driver, self.base_url)

    def get_error_message(self) -> str:
        """获取登录错误信息"""
        try:
            return self.get_text(self.ERROR_ALERT)
        except Exception:
            return ""


class AdminDashboardPage(BasePage):
    """后台 Dashboard — /admin/index.php?route=common/dashboard"""

    PAGE_HEADER = (By.CSS_SELECTOR, ".page-header h1, .panel-heading h1, #content h1")
    NAV_CATALOG = (By.CSS_SELECTOR, "a[href*='catalog']")
    NAV_PRODUCTS = (By.CSS_SELECTOR, "a[href*='catalog/product']")
    NAV_SALE = (By.CSS_SELECTOR, "a[href*='sale']")
    NAV_ORDERS = (By.CSS_SELECTOR, "a[href*='sale/order']")
    LOGOUT_BTN = (By.CSS_SELECTOR, ".navbar-nav a[href*='logout'], #nav-logout a")

    def is_loaded(self) -> bool:
        """验证 Dashboard 已加载"""
        return "dashboard" in self.get_current_url().lower()

    def get_page_title(self) -> str:
        """获取页面标题"""
        try:
            return self.get_text(self.PAGE_HEADER)
        except Exception:
            return ""

    def navigate_to_products(self):
        """导航到商品管理页面"""
        self.open("/admin/index.php?route=catalog/product")
        return AdminProductListPage(self.driver, self.base_url)

    def navigate_to_orders(self):
        """导航到订单管理页面"""
        self.open("/admin/index.php?route=sale/order")
        return AdminOrderListPage(self.driver, self.base_url)

    def logout(self):
        """登出后台"""
        try:
            self.click(self.LOGOUT_BTN)
        except Exception:
            self.open("/admin/index.php?route=common/logout")
        return AdminLoginPage(self.driver, self.base_url)


class AdminProductListPage(BasePage):
    """商品列表页 — /admin/index.php?route=catalog/product"""

    PAGE_HEADER = (By.CSS_SELECTOR, "h1, .page-header h1")
    ADD_BTN = (By.CSS_SELECTOR, "a[href*='catalog/product/add'], a[data-original-title='Add New']")
    DELETE_BTN = (By.CSS_SELECTOR, "button[data-original-title='Delete'], button.btn-danger")
    SUCCESS_ALERT = (By.CSS_SELECTOR, ".alert-success")
    SEARCH_INPUT = (By.ID, "input-name")
    FILTER_BTN = (By.ID, "button-filter")
    TABLE_ROWS = (By.CSS_SELECTOR, "table.table tbody tr, .table-responsive tbody tr")
    CHECKBOX_ALL = (By.CSS_SELECTOR, "input[type='checkbox'][onclick*='select']")
    NO_RESULTS = (By.CSS_SELECTOR, ".table tbody td.text-center, .table-responsive tbody td")

    def is_loaded(self) -> bool:
        """验证页面已加载"""
        return "catalog/product" in self.get_current_url().lower()

    def get_product_count(self) -> int:
        """获取商品列表行数"""
        try:
            rows = self.find_all(self.TABLE_ROWS)
            return len(rows)
        except Exception:
            return 0

    def add_new_product(self):
        """点击添加新商品按钮"""
        self.click(self.ADD_BTN)
        return AdminProductFormPage(self.driver, self.base_url)

    def search_product(self, name: str):
        """搜索商品"""
        self.send_keys(self.SEARCH_INPUT, name)
        self.click(self.FILTER_BTN)
        return self

    def select_all(self):
        """全选商品"""
        try:
            checkbox = self.driver.find_element(*self.CHECKBOX_ALL)
            if not checkbox.is_selected():
                checkbox.click()
        except Exception:
            pass
        return self

    def delete_selected(self):
        """删除选中的商品"""
        self.click(self.DELETE_BTN)
        # 处理确认弹窗
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except Exception:
            pass
        return self

    def get_success_message(self) -> str:
        """获取操作成功提示"""
        try:
            return self.get_text(self.SUCCESS_ALERT)
        except Exception:
            return ""


class AdminProductFormPage(BasePage):
    """商品编辑表单页 — /admin/index.php?route=catalog/product/add|edit"""

    PRODUCT_NAME = (By.ID, "input-name-1")
    META_TITLE = (By.ID, "input-meta-title-1")
    DESCRIPTION = (By.CSS_SELECTOR, "[name='product_description[1][description]']")
    MODEL = (By.ID, "input-model")
    PRICE = (By.ID, "input-price")
    QUANTITY = (By.ID, "input-quantity")
    STATUS = (By.ID, "input-status")
    SAVE_BTN = (By.CSS_SELECTOR, "button[data-original-title='Save'], button[type='submit'].btn-primary")

    # 标签页
    DATA_TAB = (By.LINK_TEXT, "Data")
    GENERAL_TAB = (By.LINK_TEXT, "General")

    def fill_general_info(self, name: str, description: str = "", meta_title: str = ""):
        """填写基本信息"""
        self.send_keys(self.PRODUCT_NAME, name)
        if meta_title:
            self.send_keys(self.META_TITLE, meta_title)
        if description:
            self.send_keys(self.DESCRIPTION, description)
        return self

    def fill_data_info(self, model: str, price: str, quantity: str, status: str = "Enabled"):
        """填写数据信息"""
        # 切换到 Data 标签页
        try:
            self.click(self.DATA_TAB)
        except Exception:
            pass  # 可能已经在该标签页

        self.send_keys(self.MODEL, model)
        self.send_keys(self.PRICE, price)
        self.send_keys(self.QUANTITY, quantity)

        # 设置状态
        try:
            select = Select(self.find(self.STATUS))
            select.select_by_visible_text(status)
        except Exception:
            pass

        return self

    def save(self):
        """保存商品"""
        self.click(self.SAVE_BTN)
        return AdminProductListPage(self.driver, self.base_url)

    def is_loaded(self) -> bool:
        """验证表单已加载"""
        url = self.get_current_url().lower()
        return "catalog/product" in url and ("add" in url or "edit" in url or "product_id" in url)


class AdminOrderListPage(BasePage):
    """订单列表页 — /admin/index.php?route=sale/order"""

    PAGE_HEADER = (By.CSS_SELECTOR, "h1, .page-header h1")
    ORDER_ROWS = (By.CSS_SELECTOR, "table.table tbody tr, .table-responsive tbody tr")
    VIEW_BTN = (By.CSS_SELECTOR, "a[data-original-title='View'], a.btn-info")

    def is_loaded(self) -> bool:
        """验证页面已加载"""
        return "sale/order" in self.get_current_url().lower()

    def get_order_count(self) -> int:
        """获取订单行数"""
        try:
            rows = self.find_all(self.ORDER_ROWS)
            return len(rows)
        except Exception:
            return 0

    def get_page_title(self) -> str:
        """获取页面标题"""
        try:
            return self.get_text(self.PAGE_HEADER)
        except Exception:
            return ""
