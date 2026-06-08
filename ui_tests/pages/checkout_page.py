"""
结账流程相关 Page Object
包含：登录页、结账页（完整 6 步结账流程）

OpenCart 4.x 结账步骤：
  Step 1: 结账选项（登录 / 注册 / 游客）
  Step 2: 账单地址
  Step 3: 配送地址（可选，可与账单相同）
  Step 4: 配送方式
  Step 5: 支付方式
  Step 6: 确认下单
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_page import BasePage


class LoginPage(BasePage):
    """登录页面 — /index.php?route=account/login"""

    EMAIL_INPUT = (By.ID, "input-email")
    PASSWORD_INPUT = (By.ID, "input-password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "input[value='Login'], button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".alert-danger")
    FORGOTTEN_LINK = (By.LINK_TEXT, "Forgotten Password")

    def login(self, email: str, password: str):
        """执行登录操作"""
        self.send_keys(self.EMAIL_INPUT, email)
        self.send_keys(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
        return self

    def get_error_message(self) -> str:
        """获取错误提示"""
        try:
            return self.get_text(self.ERROR_MESSAGE)
        except Exception:
            return ""


class CheckoutPage(BasePage):
    """结账页面 — /index.php?route=checkout/checkout

    封装完整 6 步结账流程，每步独立方法可自由组合。
    """

    # === Step 1: 结账选项 ===
    GUEST_RADIO = (By.CSS_SELECTOR, "input[value='guest']")
    REGISTER_RADIO = (By.CSS_SELECTOR, "input[value='register']")
    LOGIN_EMAIL = (By.ID, "input-login-email")
    LOGIN_PASSWORD = (By.ID, "input-login-password")
    LOGIN_BTN = (By.ID, "button-login")
    CHECKOUT_CONTINUE_BTN = (By.ID, "button-account")

    # === Step 2: 账单地址 ===
    BILLING_FIRST_NAME = (By.ID, "input-payment-firstname")
    BILLING_LAST_NAME = (By.ID, "input-payment-lastname")
    BILLING_COMPANY = (By.ID, "input-payment-company")
    BILLING_ADDRESS1 = (By.ID, "input-payment-address-1")
    BILLING_ADDRESS2 = (By.ID, "input-payment-address-2")
    BILLING_CITY = (By.ID, "input-payment-city")
    BILLING_POSTCODE = (By.ID, "input-payment-postcode")
    BILLING_COUNTRY = (By.ID, "input-payment-country")
    BILLING_ZONE = (By.ID, "input-payment-zone")
    BILLING_CONTINUE = (By.ID, "button-payment-address")

    # === Step 3: 配送地址 ===
    DELIVERY_FIRST_NAME = (By.ID, "input-shipping-firstname")
    DELIVERY_LAST_NAME = (By.ID, "input-shipping-lastname")
    DELIVERY_ADDRESS1 = (By.ID, "input-shipping-address-1")
    DELIVERY_CITY = (By.ID, "input-shipping-city")
    DELIVERY_POSTCODE = (By.ID, "input-shipping-postcode")
    DELIVERY_COUNTRY = (By.ID, "input-shipping-country")
    DELIVERY_ZONE = (By.ID, "input-shipping-zone")
    DELIVERY_CONTINUE = (By.ID, "button-shipping-address")

    # === Step 4: 配送方式 ===
    SHIPPING_METHOD_RADIO = (By.NAME, "shipping_method")
    SHIPPING_CONTINUE = (By.ID, "button-shipping-method")

    # === Step 5: 支付方式 ===
    PAYMENT_METHOD_RADIO = (By.NAME, "payment_method")
    PAYMENT_AGREE = (By.NAME, "agree")
    PAYMENT_CONTINUE = (By.ID, "button-payment-method")

    # === Step 6: 确认下单 ===
    CONFIRM_BTN = (By.ID, "button-confirm")
    ORDER_SUCCESS_HEADER = (By.CSS_SELECTOR, "#content h1")
    ORDER_SUCCESS_CONTENT = (By.CSS_SELECTOR, "#content")

    # =======================================================
    # Step 1: 结账选项
    # =======================================================

    def select_guest_checkout(self):
        """选择游客结账模式"""
        try:
            self.click(self.GUEST_RADIO)
        except Exception:
            pass  # 可能已选中或页面直接跳过了这一步
        return self

    def continue_from_checkout_options(self):
        """点击结账选项的 Continue"""
        try:
            self.click(self.CHECKOUT_CONTINUE_BTN)
        except Exception:
            pass
        return self

    def login_as(self, email: str, password: str):
        """在结账流程 Step 1 中登录已有账号"""
        self.send_keys(self.LOGIN_EMAIL, email)
        self.send_keys(self.LOGIN_PASSWORD, password)
        self.click(self.LOGIN_BTN)
        return self

    # =======================================================
    # Step 2: 账单地址
    # =======================================================

    def fill_billing_address(self, first_name: str, last_name: str,
                             address: str, city: str, postcode: str,
                             country: str = None, zone: str = None):
        """填写账单地址

        Args:
            first_name: 名
            last_name: 姓
            address: 地址行1
            city: 城市
            postcode: 邮编
            country: 国家（可选，默认不修改）
            zone: 省/州（可选，默认不修改）
        """
        self.send_keys(self.BILLING_FIRST_NAME, first_name)
        self.send_keys(self.BILLING_LAST_NAME, last_name)
        self.send_keys(self.BILLING_ADDRESS1, address)
        self.send_keys(self.BILLING_CITY, city)
        self.send_keys(self.BILLING_POSTCODE, postcode)

        # 选择国家（下拉框）
        if country:
            self._select_option(self.BILLING_COUNTRY, country)

        # 选择省/州（依赖国家选择，需要等待加载）
        if zone:
            self._select_option(self.BILLING_ZONE, zone)

        self.click(self.BILLING_CONTINUE)
        return self

    # =======================================================
    # Step 3: 配送地址
    # =======================================================

    def fill_delivery_address(self, first_name: str, last_name: str,
                              address: str, city: str, postcode: str,
                              country: str = None, zone: str = None):
        """填写配送地址（独立于账单地址时使用）

        如果配送地址与账单地址相同，OpenCart 可能自动跳过此步骤。
        """
        try:
            self.send_keys(self.DELIVERY_FIRST_NAME, first_name)
            self.send_keys(self.DELIVERY_LAST_NAME, last_name)
            self.send_keys(self.DELIVERY_ADDRESS1, address)
            self.send_keys(self.DELIVERY_CITY, city)
            self.send_keys(self.DELIVERY_POSTCODE, postcode)

            if country:
                self._select_option(self.DELIVERY_COUNTRY, country)
            if zone:
                self._select_option(self.DELIVERY_ZONE, zone)

            self.click(self.DELIVERY_CONTINUE)
        except (TimeoutException, NoSuchElementException):
            # 配送地址可能与账单地址相同，自动跳过
            pass
        return self

    # =======================================================
    # Step 4: 配送方式
    # =======================================================

    def select_shipping_method(self):
        """选择第一个可用的配送方式并继续"""
        try:
            # 尝试选择第一个配送方式 radio
            radios = self.driver.find_elements(*self.SHIPPING_METHOD_RADIO)
            if radios:
                if not radios[0].is_selected():
                    radios[0].click()
            # 也可能以按钮形式呈现（如 flat rate 自动选中）
            self.click(self.SHIPPING_CONTINUE)
        except (TimeoutException, NoSuchElementException):
            pass  # 可能自动跳过
        return self

    # =======================================================
    # Step 5: 支付方式
    # =======================================================

    def select_payment_method(self):
        """选择第一个可用的支付方式，勾选同意条款并继续"""
        # 选择第一个支付方式
        try:
            radios = self.driver.find_elements(*self.PAYMENT_METHOD_RADIO)
            if radios:
                if not radios[0].is_selected():
                    radios[0].click()
        except Exception:
            pass

        # 勾选同意条款（必选）
        try:
            agree = self.driver.find_element(*self.PAYMENT_AGREE)
            if not agree.is_selected():
                agree.click()
        except Exception:
            pass

        self.click(self.PAYMENT_CONTINUE)
        return self

    # =======================================================
    # Step 6: 确认下单
    # =======================================================

    def confirm(self):
        """点击确认下单按钮"""
        self.click(self.CONFIRM_BTN)
        return self

    def is_order_successful(self) -> bool:
        """判断下单是否成功"""
        # 方法1: URL 包含 success
        try:
            self.wait_for_url_contains("success", timeout=15)
            return True
        except Exception:
            pass

        # 方法2: 页面内容包含成功关键词
        try:
            header_text = self.get_text(self.ORDER_SUCCESS_HEADER)
            if any(word in header_text.lower() for word in ["success", "placed", "confirmed", "order"]):
                return True
        except Exception:
            pass

        # 方法3: 检查页面整体内容
        try:
            content_text = self.get_text(self.ORDER_SUCCESS_CONTENT)
            if any(word in content_text.lower() for word in ["success", "placed", "confirmed"]):
                return True
        except Exception:
            pass

        return False

    def get_order_success_message(self) -> str:
        """获取下单成功后的页面标题"""
        try:
            return self.get_text(self.ORDER_SUCCESS_HEADER)
        except Exception:
            return ""

    # =======================================================
    # 快捷组合方法
    # =======================================================

    def complete_checkout_as_guest(self,
                                   first_name: str = "Test",
                                   last_name: str = "User",
                                   address: str = "123 Test Street",
                                   city: str = "Test City",
                                   postcode: str = "12345",
                                   ) -> bool:
        """游客模式完整结账快捷方法（一站到底）

        适用于 E2E 测试中快速完成下单流程。

        Returns:
            bool: 下单是否成功
        """
        self.select_guest_checkout()
        self.continue_from_checkout_options()
        self.fill_billing_address(first_name, last_name, address, city, postcode)
        self.fill_delivery_address(first_name, last_name, address, city, postcode)
        self.select_shipping_method()
        self.select_payment_method()
        self.confirm()
        return self.is_order_successful()

    # =======================================================
    # 内部辅助方法
    # =======================================================

    def _select_option(self, locator: tuple, value: str):
        """选择下拉框选项（支持按可见文本或 value）"""
        try:
            element = self.find(locator)
            select = Select(element)
            # 先尝试按可见文本匹配
            try:
                select.select_by_visible_text(value)
            except Exception:
                try:
                    select.select_by_value(value)
                except Exception:
                    # 最后尝试按 index 1（跳过默认的 "--- Please Select ---"）
                    if len(select.options) > 1:
                        select.select_by_index(1)
        except Exception:
            pass
