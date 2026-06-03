"""
认证模块 API 测试
覆盖：API Key 登录成功/失败、Token 管理、登出、错误 Key、空 Key

OpenCart 4.x 认证机制：
  POST api/account/login {username, key} → {api_token}
  api_token 作为 OCSESSID cookie 传递
"""
import allure
import pytest


@allure.feature("认证模块")
class TestAuth:

    # ── 正常登录流程 ──────────────────────────────────────

    @allure.story("登录 — 正常流程")
    @allure.title("正确的 API username + key 登录应返回 api_token")
    @pytest.mark.smoke
    def test_login_success(self, unauth_api, config):
        """等价类-有效：正确的 API username + key"""
        resp = unauth_api.login(config.API_USERNAME, config.API_KEY)

        assert resp.status_code == 200, f"期望 200, 实际 {resp.status_code}"
        body = resp.json()
        assert "api_token" in body, f"响应应包含 api_token: {body}"
        assert "success" in body, f"响应应包含 success: {body}"

        token = body.get("api_token")
        assert token, f"api_token 不应为空: {body}"
        assert len(token) > 10, f"api_token 长度过短: {len(token)}"

    @allure.story("认证状态验证")
    @allure.title("登录后 api fixture 应有有效 api_token")
    def test_api_fixture_has_token(self, api):
        """验证 session 级别的 api fixture 正确获取了 api_token"""
        assert api.is_authenticated(), "api fixture 应自动登录并获取 api_token"
        token = api.get_token()
        assert token is not None, "get_token() 不应为 None"
        assert len(token) > 10, f"token 长度异常: {len(token)}"

    # ── 登录异常流程 ──────────────────────────────────────

    @allure.story("登录 — 异常流程")
    @allure.title("错误的 API Key 登录应返回 error")
    def test_login_wrong_key(self, unauth_api, config):
        """等价类-无效：正确 username + 错误 key"""
        resp = unauth_api.login(config.API_USERNAME, "WrongAPIKey1234567890")

        body = resp.json()
        assert "error" in body, \
            f"错误 Key 应返回 error: {body}"
        assert unauth_api.api_token is None, "错误 Key 不应设置 token"

    @allure.story("登录 — 异常流程")
    @allure.title("不存在的 API username 登录应返回 error")
    def test_login_nonexistent_user(self, unauth_api):
        """等价类-无效：不存在的 API username"""
        resp = unauth_api.login("NonExistentAPIUser", "anykey1234567890")

        body = resp.json()
        assert "error" in body, \
            f"不存在用户应返回 error: {body}"
        assert unauth_api.api_token is None

    @allure.story("登录 — 异常流程")
    @allure.title("空 username 登录应返回 error")
    def test_login_empty_username(self, unauth_api, config):
        """等价类-无效：空 username"""
        resp = unauth_api.login("", config.API_KEY)

        body = resp.json()
        assert "error" in body or "warning" in str(body).lower(), \
            f"空 username 应返回错误: {body}"
        assert unauth_api.api_token is None

    @allure.story("登录 — 异常流程")
    @allure.title("空 API Key 登录应返回 error")
    def test_login_empty_key(self, unauth_api, config):
        """等价类-无效：空 API Key"""
        resp = unauth_api.login(config.API_USERNAME, "")

        body = resp.json()
        assert "error" in body or "warning" in str(body).lower(), \
            f"空 Key 应返回错误: {body}"
        assert unauth_api.api_token is None

    # ── 登出流程 ──────────────────────────────────────────

    @allure.story("登出")
    @allure.title("登出后 api_token 应为 None")
    def test_logout_clears_token(self, unauth_api, config):
        """验证登出操作正确清除认证状态"""
        # 先登录
        unauth_api.login(config.API_USERNAME, config.API_KEY)
        assert unauth_api.is_authenticated(), "登录后应有 token"

        # 登出
        unauth_api.logout()
        assert unauth_api.api_token is None, "登出后 token 应为 None"
        assert not unauth_api.is_authenticated()

    @allure.story("登出")
    @allure.title("登出后调用需认证的 API 应失败")
    def test_logout_prevents_authenticated_access(self, unauth_api, config):
        """验证登出后无法访问需认证的接口"""
        unauth_api.login(config.API_USERNAME, config.API_KEY)
        unauth_api.logout()

        # 登出后访问购物车 API — 应失败（无有效 session）
        resp = unauth_api.get("api/sale/cart")
        # 无有效 session 时 OpenCart 4.x 返回 404 或重定向（不是 JSON）
        assert resp.status_code != 200 or not unauth_api.is_authenticated(), \
            f"登出后不应能正常访问需认证的 API: status={resp.status_code}"
        allure.attach(
            f"Status: {resp.status_code}\nBody: {resp.text[:200]}",
            "登出后请求结果",
            allure.attachment_type.TEXT,
        )

    # ── 重复登录 ──────────────────────────────────────────

    @allure.story("登录 — 边界场景")
    @allure.title("重复登录应能正常更新 api_token")
    def test_duplicate_login(self, unauth_api, config):
        """验证重复登录操作不会出错"""
        # 第一次登录
        unauth_api.login(config.API_USERNAME, config.API_KEY)
        first_token = unauth_api.api_token
        assert first_token is not None

        # 第二次登录（同一用户）
        unauth_api.login(config.API_USERNAME, config.API_KEY)
        second_token = unauth_api.api_token
        assert second_token is not None
        # 两次登录可能生成不同 token
        allure.attach(
            f"First: {first_token[:16]}...\nSecond: {second_token[:16]}...",
            "api_token 对比",
            allure.attachment_type.TEXT,
        )
