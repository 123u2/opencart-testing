"""
全局配置文件
面试可讲：使用独立的 config 文件管理环境配置，
切换环境只需修改 BASE_URL 或通过环境变量覆盖
"""
import os


class Config:
    """基础配置"""
    # OpenCart 地址 — Docker 启动后默认 8080 端口
    BASE_URL = os.getenv("OPENCART_BASE_URL", "http://localhost:8080")

    # 测试账号（OpenCart 安装时自动生成的 demo 数据中的用户）
    TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password")

    # 后台管理账号
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # 数据库配置（用于数据断言 — 面试加分项）
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "opencart")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "opencart")
    DB_NAME = os.getenv("DB_NAME", "opencart")

    # 超时设置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    UI_TIMEOUT = int(os.getenv("UI_TIMEOUT", "10"))
