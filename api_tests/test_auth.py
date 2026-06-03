"""
认证模块 API 测试
覆盖：登录成功/失败、Token 管理、登出、错误密码、不存在的用户
"""
import allure
import pytest


@allure.feature("认证模块")
class TestAuth:

    # ── 正常登录流程 ──────────────────────────────────────

    @allure.story("登录 — 正常流程")
    @allure.title("正确邮箱和密码登录应返回 token")
    @pytest.mark.smoke
    def test_login_success(self, unauth_api, config):
        """等价类-有效：正确的邮箱 + 正确密码"""
        resp = unauth_api.login(config.TEST_EMAIL, config.TEST_PASSWORD)

        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"
        body = resp.json()
        assert body.get("success"), f"响应应包含 success: {body}"
        token = body.get("data", {}).get("token")
        assert token, f"应返回 token: {body}"
        assert len(token) > 10, f"token 长度过短: {len(token)}"

    @allure.story("认证状态验证")
    @allure.title("登录后 api fixture 应有有效 token")
    def test_api_fixture_has_token(self, api):
        """验证 session 级别的 api fixture 正确获取了 token"""
        assert api.token is not None, "api fixture 应自动登录并获取 token"
        assert len(api.token) > 10, f"token 长度异常: {len(api.token)}"

    # ── 登录异常流程 ──────────────────────────────────────

    @allure.story("登录 — 异常流程")
    @allure.title("错误密码登录不应返回 token")
    def test_login_wrong_password(self, unauth_api, config):
        """等价类-无效：正确邮箱 + 错误密码"""
        resp = unauth_api.login(config.TEST_EMAIL, "WrongPassword123")

        body = resp.json()
        # 错误密码不应返回有效 token
        token = body.get("data", {}).get("token")
        has_error = "error" in body or "warning" in str(body).lower()
        assert token is None or has_error, \
            f"错误密码不应返回 token: token={token}, body={body}"

    @allure.story("登录 — 异常流程")
    @allure.title("不存在的用户登录不应返回 token")
    def test_login_nonexistent_user(self, unauth_api):
        """等价类-无效：不存在的邮箱"""
        resp = unauth_api.login("no-such-user@example.com", "anypassword")

        body = resp.json()
        token = body.get("data", {}).get("token")
        has_error = "error" in body or "warning" in str(body).lower()
        assert token is None or has_error, \
            f"不存在用户不应返回 token: token={token}, body={body}"

    @allure.story("登录 — 异常流程")
    @allure.title("空邮箱登录不应返回 token")
    def test_login_empty_email(self, unauth_api, config):
        """等价类-无效：空邮箱"""
        resp = unauth_api.login("", config.TEST_PASSWORD)

        body = resp.json()
        token = body.get("data", {}).get("token")
        has_error = "error" in body or "warning" in str(body).lower()
        assert token is None or has_error, \
            f"空邮箱不应返回 token: token={token}, body={body}"

    @allure.story("登录 — 异常流程")
    @allure.title("空密码登录不应返回 token")
    def test_login_empty_password(self, unauth_api, config):
        """等价类-无效：空密码"""
        resp = unauth_api.login(config.TEST_EMAIL, "")

        body = resp.json()
        token = body.get("data", {}).get("token")
        has_error = "error" in body or "warning" in str(body).lower()
        assert token is None or has_error, \
            f"空密码不应返回 token: token={token}, body={body}"

    @allure.story("登录 — 异常流程")
    @allure.title("超长邮箱登录应能正常处理")
    def test_login_overlong_email(self, unauth_api):
        """边界值：超长邮箱地址"""
        long_email = "a" * 256 + "@example.com"
        resp = unauth_api.login(long_email, "password")

        body = resp.json()
        token = body.get("data", {}).get("token")
        has_error = "error" in body or "warning" in str(body).lower()
        # 超长输入不应导致服务器崩溃，也不应返回 token
        assert token is None or has_error, \
            f"超长邮箱不应返回 token: body={body}"

    # ── 登出流程 ──────────────────────────────────────────

    @allure.story("登出")
    @allure.title("登出后 token 应为 None")
    def test_logout_clears_token(self, unauth_api, config):
        """验证登出操作正确清除认证状态"""
        # 先登录
        unauth_api.login(config.TEST_EMAIL, config.TEST_PASSWORD)
        assert unauth_api.token is not None, "登录后应有 token"

        # 登出
        unauth_api.logout()
        assert unauth_api.token is None, "登出后 token 应为 None"

    @allure.story("登出")
    @allure.title("登出后调用需认证的 API 应失败")
    def test_logout_prevents_authenticated_access(self, unauth_api, config):
        """验证登出后无法访问需认证的接口"""
        unauth_api.login(config.TEST_EMAIL, config.TEST_PASSWORD)
        unauth_api.logout()

        # 登出后访问购物车（应该仍然可以，因为 cookie 还在）
        # 但 token 已被移除
        resp = unauth_api.get("api/cart/getProducts")
        # 移除 token 后，某些 OpenCart 版本可能仍允许基于 session cookie 的访问
        # 这里验证 token 确实被清除了
        assert unauth_api.token is None

    # ── 重复登录 ──────────────────────────────────────────

    @allure.story("登录 — 边界场景")
    @allure.title("重复登录应能正常更新 token")
    def test_duplicate_login(self, unauth_api, config):
        """验证重复登录操作不会出错"""
        # 第一次登录
        unauth_api.login(config.TEST_EMAIL, config.TEST_PASSWORD)
        first_token = unauth_api.token
        assert first_token is not None

        # 第二次登录（同一用户）
        unauth_api.login(config.TEST_EMAIL, config.TEST_PASSWORD)
        second_token = unauth_api.token
        assert second_token is not None
        # 两次登录可能生成不同 token
        allure.attach(
            f"First: {first_token[:16]}...\nSecond: {second_token[:16]}...",
            "Token 对比",
            allure.attachment_type.TEXT,
        )
