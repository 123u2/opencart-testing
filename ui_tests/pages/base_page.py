"""
BasePage — 所有 Page Object 的基类
面试可讲：
  1. 为什么要基类？→ 统一等待策略、封装通用操作、避免 driver 直接暴露
  2. 显式等待 vs 隐式等待 → 显式等待更精确，不浪费等待时间
  3. 失败自动截图 → 不需要每个测试用例单独写 try/except
"""
import logging
import os
import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class BasePage:
    """所有 Page Object 的基类

    封装了：
    - 显式等待策略
    - 元素查找/点击/输入
    - 失败自动截图
    - 页面导航
    """

    # 截图保存目录
    SCREENSHOT_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "reports", "screenshots",
    )

    def __init__(self, driver, base_url: str = ""):
        """
        Args:
            driver: WebDriver 实例
            base_url: OpenCart 根地址
        """
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, timeout=10)

    # ── 导航方法 ──────────────────────────────────────────

    def open(self, path: str = ""):
        """打开页面

        Args:
            path: URL 路径，如 "/index.php?route=product/category&path=20"
        """
        url = f"{self.base_url}{path}"
        logger.info(f"导航到: {url}")
        self.driver.get(url)
        return self

    def get_title(self) -> str:
        """获取页面标题"""
        return self.driver.title

    def get_current_url(self) -> str:
        """获取当前 URL"""
        return self.driver.current_url

    # ── 元素查找（带显式等待）─────────────────────────────

    def find(self, locator: tuple, timeout: int = None):
        """查找单个元素（带显式等待）

        Args:
            locator: (By.ID, "xxx") 或 (By.CSS_SELECTOR, ".class")
            timeout: 自定义等待秒数

        Returns:
            WebElement
        """
        wait = WebDriverWait(self.driver, timeout or 10)
        return wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator: tuple, timeout: int = None):
        """查找所有匹配的元素"""
        wait = WebDriverWait(self.driver, timeout or 10)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def find_visible(self, locator: tuple, timeout: int = None):
        """查找可见元素"""
        wait = WebDriverWait(self.driver, timeout or 10)
        return wait.until(EC.visibility_of_element_located(locator))

    # ── 元素操作 ──────────────────────────────────────────

    def click(self, locator: tuple, timeout: int = None):
        """点击元素（等待可点击后点击）"""
        wait = WebDriverWait(self.driver, timeout or 10)
        element = wait.until(EC.element_to_be_clickable(locator))
        element.click()
        return self

    def send_keys(self, locator: tuple, text: str):
        """输入文本（先清空再输入）"""
        element = self.find(locator)
        element.clear()
        element.send_keys(text)
        return self

    def get_text(self, locator: tuple) -> str:
        """获取元素文本"""
        return self.find(locator).text

    def get_attribute(self, locator: tuple, attr: str) -> str:
        """获取元素属性值"""
        return self.find(locator).get_attribute(attr)

    def is_displayed(self, locator: tuple) -> bool:
        """判断元素是否可见"""
        try:
            return self.find(locator).is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    # ── 截图 ──────────────────────────────────────────────

    def screenshot(self, name: str):
        """保存截图"""
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)
        filepath = os.path.join(self.SCREENSHOT_DIR, f"{name}.png")
        self.driver.save_screenshot(filepath)
        logger.info(f"截图已保存: {filepath}")

        try:
            allure.attach.file(filepath, name, allure.attachment_type.PNG)
        except Exception:
            pass
        return self

    # ── JavaScript 操作 ────────────────────────────────────

    def execute_js(self, script: str, *args):
        """执行 JavaScript 脚本"""
        return self.driver.execute_script(script, *args)

    def scroll_to(self, locator: tuple):
        """滚动页面使元素可见"""
        element = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element)
        return self

    # ── 等待条件 ──────────────────────────────────────────

    def wait_for_url_contains(self, text: str, timeout: int = 10):
        """等待 URL 包含指定文本"""
        WebDriverWait(self.driver, timeout).until(EC.url_contains(text))

    def wait_for_text_present(self, locator: tuple, text: str, timeout: int = 10):
        """等待元素文本包含指定内容"""
        WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element(locator, text)
        )
