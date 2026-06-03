"""
API 客户端封装
面试可讲：
  1. 为什么封装？→ 统一管理 base_url、token、session、日志
  2. 为什么用 requests.Session()？→ 自动管理 Cookie，保持登录态
  3. OpenCart 4.x API 认证：username + API Key → api_token → OCSESSID cookie

OpenCart 4.x 适配要点：
  - 认证：POST api/account/login {username, key} → {api_token}
  - Token 作为 OCSESSID cookie 传递（不是 Authorization header）
  - 路由方法分隔符：| (如 api/sale/cart|add)
"""
import json
import logging
import allure
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class OpenCartAPI:
    """OpenCart API 客户端

    封装了 Session 管理、API Key 认证、请求日志、异常处理。
    所有 API 测试通过此类与被测系统交互。

    适用于 OpenCart 4.x 的 API 认证机制：
      1. 用 API username + key 调用 api/account/login 获取 api_token
      2. 将 api_token 设置为 OCSESSID cookie
      3. 后续请求自动携带此 cookie 完成认证
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
            "User-Agent": "OpenCart-Test-Framework/2.0",
            "Accept": "application/json, text/html, */*",
        })
        self.api_token = None
        self.api_username = None

    # ── 认证相关 ──────────────────────────────────────────

    def login(self, username: str, key: str) -> requests.Response:
        """API 登录获取 api_token（OpenCart 4.x 认证机制）

        对应 OpenCart 4.x API:
          POST index.php?route=api/account/login
          参数: username (API 用户名), key (API Key)

        Args:
            username: API 用户名（在后台 System → Users → API 中创建）
            key: API Key

        Returns:
            请求响应对象，成功时 response.json() 包含 {"success": "...", "api_token": "..."}
        """
        url = f"{self.base_url}/index.php?route=api/account/login"
        logger.info(f"API 登录: username={username}")

        # 登录前先清除旧的认证状态
        self.api_token = None
        self.api_username = None
        self.session.cookies.clear()

        resp = self.session.post(
            url,
            data={"username": username, "key": key},
            timeout=self.timeout,
        )

        if resp.status_code == 200:
            try:
                body = resp.json()
                if "api_token" in body:
                    self.api_token = body["api_token"]
                    self.api_username = username
                    # OpenCart 4.x 使用 OCSESSID cookie 传递 API session
                    # 关键：必须清除旧 cookie 只保留 api_token，
                    # 否则 login 响应的 OCSESSID 会与 api_token 冲突
                    self.session.cookies.clear()
                    self.session.cookies.set("OCSESSID", self.api_token)
                    logger.info(
                        f"API 登录成功, api_token: {self.api_token[:8]}..."
                    )
                elif "error" in body:
                    logger.warning(f"API 登录失败: {body['error']}")
                    # 登录失败时确保 token 为 None
                    self.api_token = None
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析登录响应失败: {e}")
                self.api_token = None

        return resp

    def logout(self):
        """登出 — 清除 api_token 和 session cookie"""
        self.api_token = None
        self.api_username = None
        self.session.cookies.clear()
        logger.info("API 已登出")

    # ── 通用请求方法 ──────────────────────────────────────

    def request(self, method: str, route: str, **kwargs) -> requests.Response:
        """统一请求入口

        Args:
            method: HTTP 方法 (get/post/put/delete)
            route: OpenCart 路由，如 'api/sale/cart|add'
                   （OpenCart 4.x 使用 | 作为控制器方法分隔符）
            **kwargs: 传给 requests 的额外参数 (data, json, params, headers...)

        Returns:
            请求响应对象
        """
        # OpenCart 4.x 路由中 | 会被自动 URL 编码为 %7C
        # PHP 端会将其解码并转换为内部 . 分隔符
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

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.api_token is not None

    def get_token(self) -> str | None:
        """获取当前 API token（用于调试）"""
        return self.api_token

    def close(self):
        """关闭 session"""
        self.session.close()
