"""
后台管理测试 — 商品 CRUD (仅示例，需后台登录后执行)
面试可讲：
  后台测试和前台测试的区别 — 后台需要 admin 权限，更关注数据一致性
"""
import allure
import pytest


@allure.feature("后台管理")
class TestAdminProduct:

    ADMIN_PATH = "/admin"

    @allure.story("后台登录")
    @allure.title("管理员登录后台")
    @pytest.mark.smoke
    def test_admin_login(self, driver, base_url, config):
        """后台登录功能验证"""
        driver.get(f"{base_url}{self.ADMIN_PATH}")

        # 检查是否已经到达后台（可能重定向到登录页）
        current_url = driver.current_url

        # 如果在登录页，执行登录
        if "login" in current_url.lower():
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            wait = WebDriverWait(driver, 10)

            # 填写用户名
            username_input = wait.until(
                EC.presence_of_element_located((By.ID, "input-username"))
            )
            username_input.clear()
            username_input.send_keys(config.ADMIN_USERNAME)

            # 填写密码
            password_input = driver.find_element(By.ID, "input-password")
            password_input.clear()
            password_input.send_keys(config.ADMIN_PASSWORD)

            # 点击登录
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()

            # 等待跳转到 Dashboard
            wait.until(EC.url_contains("common/dashboard"))

        # 验证已在后台
        assert "admin" in driver.current_url.lower(), \
            "登录后应在后台"
        assert "dashboard" in driver.current_url.lower(), \
            "应跳转到 Dashboard"

    @allure.story("订单管理")
    @allure.title("后台查看订单列表")
    @pytest.mark.p1
    def test_view_orders(self, driver, base_url, config):
        """后台订单列表查看"""
        # 先登录
        driver.get(f"{base_url}{self.ADMIN_PATH}")
        current_url = driver.current_url

        if "login" in current_url.lower():
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            wait = WebDriverWait(driver, 10)
            username = wait.until(EC.presence_of_element_located((By.ID, "input-username")))
            username.clear()
            username.send_keys(config.ADMIN_USERNAME)

            password = driver.find_element(By.ID, "input-password")
            password.clear()
            password.send_keys(config.ADMIN_PASSWORD)

            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            wait.until(EC.url_contains("common/dashboard"))

        # 导航到订单列表
        driver.get(f"{base_url}{self.ADMIN_PATH}/index.php?route=sale/order")

        # 验证订单页面加载
        from selenium.webdriver.common.by import By
        page_title = driver.find_element(By.CSS_SELECTOR, "h1, .page-header h1").text
        assert "order" in page_title.lower(), \
            f"应显示订单管理页面, 实际标题: {page_title}"

        allure.attach(page_title, "后台页面标题", allure.attachment_type.TEXT)
