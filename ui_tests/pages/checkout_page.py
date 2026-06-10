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
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
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

    OpenCart 4.0.2.3 结账流程说明：
      - 注册用户：各步骤独立 Section 加载（Step 2 账单/Step 3 配送/Step 4 货运/Step 5 支付/Step 6 确认）
      - 游客模式：账单地址字段嵌入在 #form-register 中，一次性提交整张注册表单
    """

    # === Step 1: 结账选项 ===
    # OpenCart 4.0.2.3: guest radio id="input-guest" value="0", register radio id="input-register" value="1"
    GUEST_RADIO = (By.ID, "input-guest")
    REGISTER_RADIO = (By.ID, "input-register")
    LOGIN_EMAIL = (By.ID, "input-login-email")
    LOGIN_PASSWORD = (By.ID, "input-login-password")
    LOGIN_BTN = (By.ID, "button-login")
    # OpenCart 4.0.2.3: the account continue button in register.twig is id="button-register"
    CHECKOUT_CONTINUE_BTN = (By.ID, "button-register")

    # --- register.twig 表单字段（游客模式核心）---
    # 游客结账时账单地址字段嵌入在注册表单中，name 使用 payment_ 前缀
    REGISTER_FIRSTNAME = (By.ID, "input-firstname")
    REGISTER_LASTNAME = (By.ID, "input-lastname")
    REGISTER_EMAIL = (By.ID, "input-email")
    REGISTER_TELEPHONE = (By.ID, "input-telephone")
    # 地址匹配复选框：默认勾选 → 配送地址与账单地址相同
    ADDRESS_MATCH = (By.ID, "input-address-match")

    # === Step 2: 账单地址 ===
    # 注册用户：AJAX 加载到 #checkout-payment-address 容器
    # 游客：字段在 #form-register 内，name 以 payment_ 开头，ID 为 input-payment-xxx
    PAYMENT_ADDRESS_CONTAINER = (By.ID, "checkout-payment-address")
    # 注册用户账单地址字段（payment_address.twig，无前缀）
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
        # 等待支付地址区域 AJAX 加载完成（OpenCart 4.x 动态加载各区域）
        # 先确认容器可见（AJAX 完成），再等表单字段可见
        try:
            self.wait.until(EC.visibility_of_element_located(self.PAYMENT_ADDRESS_CONTAINER))
            # 确保容器内已渲染表单内容（不只是空 div）
            self.wait.until(
                lambda d: len(d.find_element(*self.PAYMENT_ADDRESS_CONTAINER).text.strip()) > 0,
                "账单地址区域未在 AJAX 加载后填充内容"
            )
        except TimeoutException:
            logging.warning("支付地址区域未能加载，尝试继续填写")
        self.wait.until(EC.visibility_of_element_located(self.BILLING_FIRST_NAME))
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
    # 游客结账 — 注册表单字段填充
    # =======================================================

    def fill_guest_register_form(self,
                                 first_name: str,
                                 last_name: str,
                                 email: str,
                                 address: str,
                                 city: str,
                                 postcode: str,
                                 telephone: str = ""):
        """填充游客结账注册表单（OpenCart 4.0.2.3 游客模式核心）

        OpenCart 4.0.2.3 的游客结账流程：
        1. 账户信息字段总是存在于 #form-register 中
        2. 地址字段行为取决于 config_checkout_payment_address 设置：
           - 启用时：支付地址字段（#input-payment-*）已渲染，发运地址通过 checkbox 隐藏
           - 禁用时：不显示支付地址字段，改为显示发运地址字段（#input-shipping-*）
        """
        # 账户信息（总是在注册表单中）
        self.send_keys(self.REGISTER_FIRSTNAME, first_name)
        self.send_keys(self.REGISTER_LASTNAME, last_name)
        self.send_keys(self.REGISTER_EMAIL, email)
        if telephone:
            self.send_keys(self.REGISTER_TELEPHONE, telephone)

        # 根据 config_checkout_payment_address 设置选择支付地址或发运地址字段
        try:
            # 快速检查：支付地址字段是否存在？（缺省超时 2 秒，避免长时间等待不存在的元素）
            self.driver.find_element(*self.BILLING_ADDRESS1)
            use_payment = True
        except NoSuchElementException:
            use_payment = False

        if use_payment:
            # 支付地址已启用 → 填写支付地址字段
            self.send_keys(self.BILLING_ADDRESS1, address)
            self.send_keys(self.BILLING_CITY, city)
            self.send_keys(self.BILLING_POSTCODE, postcode)
            self._select_option(self.BILLING_COUNTRY, "")
            try:
                self.wait.until(
                    lambda d: len(Select(d.find_element(*self.BILLING_ZONE)).options) > 1,
                    "账单地址 Zone 选项未在 AJAX 加载后出现"
                )
            except TimeoutException:
                pass
            self._select_option(self.BILLING_ZONE, "")
        else:
            # 支付地址已禁用 → 填写可见的发运地址字段
            self.send_keys(self.DELIVERY_ADDRESS1, address)
            self.send_keys(self.DELIVERY_CITY, city)
            self.send_keys(self.DELIVERY_POSTCODE, postcode)
            self._select_option(self.DELIVERY_COUNTRY, "")
            try:
                self.wait.until(
                    lambda d: len(Select(d.find_element(*self.DELIVERY_ZONE)).options) > 1,
                    "发运地址 Zone 选项未在 AJAX 加载后出现"
                )
            except TimeoutException:
                pass
            self._select_option(self.DELIVERY_ZONE, "")

        return self

    # =======================================================
    # 快捷组合方法
    # =======================================================

    def complete_checkout_as_guest(self,
                                   first_name: str = "Test",
                                   last_name: str = "User",
                                   email: str = "guest@example.com",
                                   address: str = "123 Test Street",
                                   city: str = "Test City",
                                   postcode: str = "12345",
                                   ) -> bool:
        """游客模式完整结账快捷方法（一站到底）

        OpenCart 4.0.2.3 游客结账流程：
          1. 选择 Guest radio
          2. 填充 #form-register 内嵌的账户+账单地址字段
          3. 点击 Continue 一次性提交，服务器返回 JSON success
          4. JS 重新加载 #checkout-confirm + 重置货运/支付方式
          5. 选择货运方式 → 选择支付方式 → 确认下单

        Returns:
            bool: 下单是否成功
        """
        self.select_guest_checkout()

        # 游客模式：必须先填充注册表单中的地址字段，再点击 Continue
        # （OC 4.0.2.3 在 register.save 中一次性校验全部字段）
        self.fill_guest_register_form(first_name, last_name, email, address, city, postcode)

        # 提交注册表单
        self.continue_from_checkout_options()

        # 等待 AJAX 完成：success/error alert 出现 或 confirm 区域重新加载
        # OpenCart 4.x JS 成功回调：$('#alert').prepend(...) + $('#checkout-confirm').load(...)
        try:
            self.wait.until(
                lambda d: (
                    d.find_element(By.ID, "checkout-confirm").is_displayed()
                    and len(d.find_element(By.ID, "checkout-confirm").text.strip()) > 30
                ),
                "结账确认区域未在 AJAX 后加载"
            )
        except TimeoutException:
            logging.warning("确认区域未能加载，尝试继续")

        # 后续步骤（货运方式/支付方式在页面初始化时已渲染，提交后被 JS 重置）
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
