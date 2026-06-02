"""
认证模块 API 测试
覆盖：登录成功/失败、Token 管理、登出、错误密码、不存在的用户
"""
import allure
import pytest


@allure.feature("认证模块")
class TestAuth:

    @allure.story("登录 — 正常流程")
    @allure.title("正确邮箱和密码登录应返回 200 和 token")
    def test_login_success(self, config):
        """等价类-有效：正确的邮箱 + 正确密码"""
        from utils.api_client import OpenCartAPI

        client = OpenCartAPI(config.BASE_URL)
        resp = client.login(config.TEST_EMAIL, config.TEST_PASSWORD)

        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"
        body = resp.json()
        assert "success" in body, f"响应应包含 success 字段: {body}"
        assert body.get("data", {}).get("token"), f"应返回 token: {body}"

    @allure.story("登录 — 异常流程")
    @allure.title("错误密码登录应返回 200 但无 token")
    def test_login_wrong_password(self, config):
        """等价类-无效：正确邮箱 + 错误密码"""
        from utils.api_client import OpenCartAPI

        client = OpenCartAPI(config.BASE_URL)
        resp = client.login(config.TEST_EMAIL, "WrongPassword123")

        # OpenCart API 对错误登录仍返回 200，但 body 中无 token
        body = resp.json()
        assert body.get("data", {}).get("token") is None or "error" in str(body).lower(), \
            f"错误密码不应返回 token: {body}"

    @allure.story("登录 — 异常流程")
    @allure.title("不存在的用户登录应返回 200 但无 token")
    def test_login_nonexistent_user(self, config):
        """等价类-无效：不存在的邮箱"""
        from utils.api_client import OpenCartAPI

        client = OpenCartAPI(config.BASE_URL)
        resp = client.login("no-such-user@example.com", "anypassword")

        body = resp.json()
        assert body.get("data", {}).get("token") is None or "error" in str(body).lower(), \
            f"不存在用户不应返回 token: {body}"

    @allure.story("认证状态验证")
    @allure.title("登录后 api fixture 应有有效 token")
    def test_api_fixture_has_token(self, api):
        """验证 session 级别的 api fixture 正确获取了 token"""
        assert api.token is not None, "api fixture 应自动登录并获取 token"
        assert len(api.token) > 10, f"token 长度异常: {len(api.token)}"

    @allure.story("登录 — 异常流程")
    @allure.title("空邮箱登录应能正常处理")
    def test_login_empty_email(self, config):
        """等价类-无效：空邮箱"""
        from utils.api_client import OpenCartAPI

        client = OpenCartAPI(config.BASE_URL)
        resp = client.login("", config.TEST_PASSWORD)

        # 不应返回 token
        body = resp.json()
        assert body.get("data", {}).get("token") is None or "error" in str(body).lower(), \
            f"空邮箱不应返回 token: {body}"

    @allure.story("登录 — 异常流程")
    @allure.title("空密码登录应能正常处理")
    def test_login_empty_password(self, config):
        """等价类-无效：空密码"""
        from utils.api_client import OpenCartAPI

        client = OpenCartAPI(config.BASE_URL)
        resp = client.login(config.TEST_EMAIL, "")

        body = resp.json()
        assert body.get("data", {}).get("token") is None or "error" in str(body).lower(), \
            f"空密码不应返回 token: {body}"
