"""
API 客户端封装
面试可讲：
  1. 为什么封装？→ 统一管理 base_url、token、session、日志
  2. 为什么用 requests.Session()？→ 自动管理 Cookie，保持登录态
  3. 自动 Token 管理 → 登录后自动注入 Authorization header
"""
import json
import logging
import allure
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class OpenCartAPI:
    """OpenCart API 客户端

    封装了 Session 管理、Token 自动注入、请求日志、异常处理。
    所有 API 测试通过此类与被测系统交互。
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Args:
            base_url: OpenCart 地址，如 http://localhost:8080
            timeout: 请求超时秒数
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        # 模拟浏览器 User-Agent
        self.session.headers.update({
            "User-Agent": "OpenCart-Test-Framework/1.0",
            "Accept": "application/json, text/html, */*",
        })
        self.token = None
        self.customer_id = None

    # ── 认证相关 ──────────────────────────────────────────

    def login(self, email: str, password: str) -> requests.Response:
        """API 登录获取 token

        对应 OpenCart API: POST index.php?route=api/account/login
        """
        url = f"{self.base_url}/index.php?route=api/account/login"
        logger.info(f"API 登录: {email}")

        resp = self.session.post(
            url,
            data={"email": email, "password": password},
            timeout=self.timeout,
        )

        if resp.status_code == 200:
            try:
                body = resp.json()
                # OpenCart 返回结构: {"success":"Success: API session created!","data":{"token":"..."}}
                if "data" in body and "token" in body["data"]:
                    self.token = body["data"]["token"]
                    # 可选：将 token 放入 header 供后续请求
                    self.session.headers.update(
                        {"Authorization": f"Bearer {self.token}"}
                    )
                    logger.info(f"登录成功, token: {self.token[:8]}...")
            except (json.JSONDecodeError, KeyError):
                logger.warning("登录响应中未找到 token")

        return resp

    def logout(self):
        """登出"""
        self.token = None
        self.session.headers.pop("Authorization", None)
        logger.info("已登出")

    # ── 通用请求方法 ──────────────────────────────────────

    def request(self, method: str, route: str, **kwargs) -> requests.Response:
        """统一请求入口

        Args:
            method: HTTP 方法 (get/post/put/delete)
            route: OpenCart 路由，如 'api/cart/add'
            **kwargs: 传给 requests 的额外参数 (data, json, params, headers...)

        Returns:
            请求响应对象
        """
        url = f"{self.base_url}/index.php?route={route}"
        kwargs.setdefault("timeout", self.timeout)

        logger.info(f"{method.upper()} {route}")
        try:
            resp = self.session.request(method, url, **kwargs)
        except Timeout:
            logger.error(f"请求超时: {method.upper()} {route}")
            raise
        except RequestException as e:
            logger.error(f"请求失败: {method.upper()} {route} — {e}")
            raise

        # Allure 附件：请求和响应内容
        self._attach_to_allure(method, route, resp)

        logger.info(f"响应: {resp.status_code} ({len(resp.text)} bytes)")
        return resp

    def get(self, route: str, **kwargs) -> requests.Response:
        return self.request("GET", route, **kwargs)

    def post(self, route: str, **kwargs) -> requests.Response:
        return self.request("POST", route, **kwargs)

    def put(self, route: str, **kwargs) -> requests.Response:
        return self.request("PUT", route, **kwargs)

    def delete(self, route: str, **kwargs) -> requests.Response:
        return self.request("DELETE", route, **kwargs)

    # ── Allure 集成 ───────────────────────────────────────

    def _attach_to_allure(self, method: str, route: str, resp: requests.Response):
        """将请求/响应内容附加到 Allure 报告"""
        try:
            allure.attach(
                f"{method.upper()} {route}\nStatus: {resp.status_code}\n\n{resp.text[:2000]}",
                name=f"{method.upper()} {route}",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass  # 无 Allure 环境时忽略

    # ── 便捷方法 ──────────────────────────────────────────

    def api_token(self) -> str | None:
        """获取当前 API token（用于 DB 查询等场景）"""
        return self.token

    def close(self):
        """关闭 session"""
        self.session.close()
