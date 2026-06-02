"""
购物车页面 Page Object
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class CartPage(BasePage):
    """购物车页面 — /index.php?route=checkout/cart"""

    # 元素定位
    PAGE_TITLE = (By.CSS_SELECTOR, "h1")
    CART_TABLE = (By.CSS_SELECTOR, ".table-responsive table, .table")
    CART_ROWS = (By.CSS_SELECTOR, ".table-responsive tbody tr, .table tbody tr")
    QUANTITY_INPUT = (By.NAME, "quantity")
    UPDATE_BTN = (By.CSS_SELECTOR, "button[data-original-title='Update'], .btn-primary[type='submit']")
    REMOVE_BTN = (By.CSS_SELECTOR, "button[data-original-title='Remove'], .btn-danger")
    CHECKOUT_BTN = (By.CSS_SELECTOR, "a.btn-primary, a[href*='checkout/checkout']")
    COUPON_INPUT = (By.ID, "input-coupon")
    COUPON_BTN = (By.ID, "button-coupon")
    EMPTY_MESSAGE = (By.CSS_SELECTOR, "#content p")

    def get_item_count(self) -> int:
        """获取购物车中商品种类数"""
        try:
            rows = self.find_all(self.CART_ROWS)
            return len(rows)
        except Exception:
            return 0

    def is_empty(self) -> bool:
        """购物车是否为空"""
        return self.get_item_count() == 0

    def update_quantity(self, qty: int):
        """修改商品数量并更新"""
        self.send_keys(self.QUANTITY_INPUT, str(qty))
        self.click(self.UPDATE_BTN)
        return self

    def apply_coupon(self, coupon_code: str):
        """输入优惠券"""
        self.send_keys(self.COUPON_INPUT, coupon_code)
        self.click(self.COUPON_BTN)
        return self

    def checkout(self):
        """点击 Checkout 进入结账页面"""
        self.click(self.CHECKOUT_BTN)
        from .checkout_page import CheckoutPage
        return CheckoutPage(self.driver, self.base_url)

    def get_empty_message(self) -> str:
        """获取空购物车提示"""
        return self.get_text(self.EMPTY_MESSAGE)
