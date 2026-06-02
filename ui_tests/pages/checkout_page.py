"""
结账流程相关 Page Object
包含：登录页、结账页
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class LoginPage(BasePage):
    """登录页面 — /index.php?route=account/login"""

    # 元素定位
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
    """结账页面 — /index.php?route=checkout/checkout"""

    # 步骤1: 结账方式选择 (登录/注册/访客)
    GUEST_RADIO = (By.CSS_SELECTOR, "input[value='guest']")
    REGISTER_RADIO = (By.CSS_SELECTOR, "input[value='register']")
    CHECKOUT_CONTINUE_BTN = (By.ID, "button-account")

    # 步骤2: 账单地址
    FIRST_NAME = (By.ID, "input-payment-firstname")
    LAST_NAME = (By.ID, "input-payment-lastname")
    ADDRESS1 = (By.ID, "input-payment-address-1")
    CITY = (By.ID, "input-payment-city")
    POSTCODE = (By.ID, "input-payment-postcode")
    COUNTRY = (By.ID, "input-payment-country")
    ZONE = (By.ID, "input-payment-zone")
    BILLING_CONTINUE = (By.ID, "button-payment-address")

    # 步骤4: 配送方式
    SHIPPING_CONTINUE = (By.ID, "button-shipping-method")

    # 步骤5: 支付方式
    PAYMENT_AGREE = (By.NAME, "agree")
    PAYMENT_CONTINUE = (By.ID, "button-payment-method")

    # 步骤6: 确认
    CONFIRM_BTN = (By.ID, "button-confirm")
    ORDER_SUCCESS = (By.CSS_SELECTOR, "#content h1, .alert-success")

    def login_as(self, email: str, password: str):
        """在结账流程中登录"""
        self.send_keys((By.ID, "input-login-email"), email)
        self.send_keys((By.ID, "input-login-password"), password)
        self.click((By.ID, "button-login"))
        return self

    def fill_billing_address(self, first_name: str, last_name: str,
                             address: str, city: str, postcode: str):
        """填写账单地址"""
        self.send_keys(self.FIRST_NAME, first_name)
        self.send_keys(self.LAST_NAME, last_name)
        self.send_keys(self.ADDRESS1, address)
        self.send_keys(self.CITY, city)
        self.send_keys(self.POSTCODE, postcode)
        self.click(self.BILLING_CONTINUE)
        return self

    def select_shipping_method(self, method: str = None):
        """继续配送方式步骤（选择默认）"""
        try:
            self.click(self.SHIPPING_CONTINUE)
        except Exception:
            # 可能配送方式和账单地址相同，自动跳过
            pass
        return self

    def select_payment_method(self, method: str = "cod"):
        """选择支付方式"""
        # 尝试勾选同意条款
        try:
            agree = self.driver.find_element(*self.PAYMENT_AGREE)
            if not agree.is_selected():
                agree.click()
        except Exception:
            pass

        self.click(self.PAYMENT_CONTINUE)
        return self

    def confirm(self):
        """确认下单"""
        self.click(self.CONFIRM_BTN)
        return self

    def is_order_successful(self) -> bool:
        """判断下单是否成功"""
        try:
            self.wait_for_url_contains("success", timeout=15)
            return True
        except Exception:
            pass

        try:
            text = self.get_text(self.ORDER_SUCCESS)
            return "success" in text.lower() or "placed" in text.lower()
        except Exception:
            return False
