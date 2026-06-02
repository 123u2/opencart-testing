"""
UI 自动化测试 pytest fixture 配置
面试可讲：
  - WebDriver fixture: 每个用例独立的浏览器实例，失败自动截图
  - 多浏览器支持: pytest --browser=firefox / chrome / edge
  - 自动管理 WebDriver: webdriver-manager 自动下载匹配的驱动
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config import Config


def pytest_addoption(parser):
    """添加 --browser 命令行参数"""
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox", "edge", "chrome-headless"],
        help="浏览器类型: chrome, firefox, edge, chrome-headless",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="OpenCart 地址 (覆盖 config.BASE_URL)",
    )


@pytest.fixture(scope="session")
def base_url(request):
    """基础 URL"""
    url = request.config.getoption("--base-url")
    return url or Config.BASE_URL


@pytest.fixture
def driver(request):
    """WebDriver 实例（每个用例独立的浏览器）

    自动下载匹配的 WebDriver，用例失败时自动截图到 Allure 报告。
    """
    browser = request.config.getoption("--browser")
    driver = None

    # ── 创建 WebDriver ──
    if browser == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
    elif browser == "chrome-headless":
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options,
        )
    elif browser == "edge":
        options = webdriver.EdgeOptions()
        driver = webdriver.Edge(
            service=EdgeService(EdgeChromiumDriverManager().install()),
            options=options,
        )

    driver.maximize_window()
    driver.implicitly_wait(Config.UI_TIMEOUT)

    yield driver

    # ── 用例结束时: 失败自动截图 ──
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        _take_screenshot(driver, request.node.name)

    driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """钩子：捕获测试结果，用于失败截图"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def _take_screenshot(driver, test_name):
    """保存失败截图"""
    screenshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "reports", "screenshots"
    )
    os.makedirs(screenshot_dir, exist_ok=True)

    filepath = os.path.join(screenshot_dir, f"{test_name}.png")
    driver.save_screenshot(filepath)

    # 附加到 Allure 报告
    try:
        import allure
        allure.attach.file(filepath, f"失败截图 - {test_name}",
                           allure.attachment_type.PNG)
    except ImportError:
        pass
