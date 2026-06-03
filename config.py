"""
全局配置文件
面试可讲：使用独立的 config 文件管理环境配置，
切换环境只需修改 BASE_URL 或通过环境变量覆盖

OpenCart 4.x 适配要点：
  - API 认证改为 username + key（API Key），不再是 email + password
  - 路由方法分隔符从 / 改为 |（如 api/sale/cart|add）
  - 默认测试商品改为 product_id=28（无必填选项，product 42 有 9 个必填选项）
"""
import os


class Config:
    """基础配置"""
    # OpenCart 地址 — Docker 启动后默认 8080 端口
    BASE_URL = os.getenv("OPENCART_BASE_URL", "http://localhost:8080")

    # ═══ API 认证（OpenCart 4.x 使用 API Key 机制）═══
    # 在后台 System → Users → API 中创建 API 用户获取 key
    API_USERNAME = os.getenv("API_USERNAME", "Default")
    API_KEY = os.getenv(
        "API_KEY",
        "9cc8cbf8b0bf19380113e59ac6254f25b22df02e80591046a5825d5b8469568e"
        "9c856a583e0667f526e4b1a4d0bedc487e050d5907aa3d98e483f4fc4afd5295"
        "9ae2bdb21fd5fd0cd54a1ec1591f8c70fe1226fb89bd665ef95908b6ecb30cdd"
        "ef9c71a1c2c0c2e36e8f6fb1c30627553cda441aa28e4f58c173c7f8a008d722",
    )

    # 测试账号（前端用户注册测试用）
    TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password")

    # 默认测试商品 — product_id=28 无必填选项，库存充足
    DEFAULT_PRODUCT_ID = int(os.getenv("DEFAULT_PRODUCT_ID", "28"))

    # 后台管理账号
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # 数据库配置（用于数据断言 — 面试加分项）
    # 注意：Docker Compose 默认不暴露 3306，需在 compose 中添加 ports: "3306:3306"
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "13306"))
    DB_USER = os.getenv("DB_USER", "opencart")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "opencart")
    DB_NAME = os.getenv("DB_NAME", "opencart")

    # 超时设置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    UI_TIMEOUT = int(os.getenv("UI_TIMEOUT", "10"))
