"""
商品相关 Page Object
包含：搜索结果页、商品详情页
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class SearchResultPage(BasePage):
    """搜索结果页面"""

    # 元素定位
    RESULT_HEADING = (By.CSS_SELECTOR, "h2, h1")
    PRODUCT_LIST = (By.CSS_SELECTOR, ".product-thumb")
    PRODUCT_NAME = (By.CSS_SELECTOR, ".product-thumb .caption a, .description h4 a")
    NO_RESULTS = (By.CSS_SELECTOR, "#content p, .alert")

    def get_result_count(self) -> int:
        """获取搜索结果数量"""
        try:
            products = self.find_all(self.PRODUCT_LIST)
            return len(products)
        except Exception:
            # 可能无结果
            return 0

    def has_results(self) -> bool:
        """是否有搜索结果"""
        return self.get_result_count() > 0

    def click_result(self, index: int = 1):
        """点击第 N 个搜索结果，进入商品详情页

        Args:
            index: 从 1 开始的序号
        """
        names = self.find_all(self.PRODUCT_NAME)
        if len(names) >= index:
            target = names[index - 1]
            # 滚动到可见区域避免被 sticky 元素拦截
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior:'instant',block:'center'});",
                target
            )
            target.click()
        return ProductDetailPage(self.driver, self.base_url)

    def get_no_results_message(self) -> str:
        """获取无结果提示"""
        try:
            return self.get_text(self.NO_RESULTS)
        except Exception:
            return ""


class ProductDetailPage(BasePage):
    """商品详情页"""

    # 元素定位
    PRODUCT_NAME = (By.CSS_SELECTOR, "h1")
    PRODUCT_PRICE = (By.CSS_SELECTOR, ".price-new, .price, h2 span")
    QUANTITY_INPUT = (By.ID, "input-quantity")
    ADD_TO_CART_BTN = (By.ID, "button-cart")
    SUCCESS_ALERT = (By.CSS_SELECTOR, ".alert-success, .alert")
    DESCRIPTION_TAB = (By.LINK_TEXT, "Description")
    REVIEW_TAB = (By.LINK_TEXT, "Reviews (0)")

    def get_product_name(self) -> str:
        """获取商品名称"""
        return self.get_text(self.PRODUCT_NAME)

    def get_price_text(self) -> str:
        """获取价格文本"""
        return self.get_text(self.PRODUCT_PRICE)

    def set_quantity(self, qty: int):
        """设置购买数量"""
        self.send_keys(self.QUANTITY_INPUT, str(qty))
        return self

    def add_to_cart(self):
        """点击 Add to Cart 按钮"""
        self.click(self.ADD_TO_CART_BTN)
        # 等待成功提示出现
        self.wait.until(EC.visibility_of_element_located(self.SUCCESS_ALERT))
        return self

    def go_to_cart(self):
        """导航到购物车页面"""
        self.driver.get(f"{self.base_url}/index.php?route=checkout/cart")
        from .cart_page import CartPage
        return CartPage(self.driver, self.base_url)
