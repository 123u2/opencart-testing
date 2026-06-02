"""
数据库操作助手
面试可讲：
  1. 为什么 API 测试还要查 DB？→ API 返回成功不代表数据真的落库了
  2. 典型场景：下单后查订单表、注册后查用户表
  3. 只用 SELECT，不做写入 — 测试数据由 API 或 seed 脚本管理
"""
import logging
from contextlib import contextmanager
import pymysql

logger = logging.getLogger(__name__)


class DBHelper:
    """MySQL 数据库操作助手（只读查询）"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }
        self.conn = None

    def connect(self):
        """建立数据库连接"""
        self.conn = pymysql.connect(**self.config)
        logger.info(f"已连接数据库: {self.config['host']}:{self.config['port']}/{self.config['database']}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def query_one(self, sql: str, params: tuple = None) -> dict | None:
        """执行查询并返回单行结果

        Args:
            sql: SQL 查询语句（仅支持 SELECT）
            params: 参数化查询参数

        Returns:
            字典格式的行数据，无结果时返回 None
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def query_all(self, sql: str, params: tuple = None) -> list[dict]:
        """执行查询并返回所有行"""
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def count(self, table: str, where: str = "1=1", params: tuple = None) -> int:
        """查询表行数

        Args:
            table: 表名
            where: WHERE 条件（不含 WHERE 关键字）
            params: 参数化查询参数

        Returns:
            行数
        """
        sql = f"SELECT COUNT(*) AS cnt FROM {table} WHERE {where}"
        row = self.query_one(sql, params)
        return row["cnt"] if row else 0

    # ── 业务查询快捷方法（面试可讲：封装常用查询减少重复代码）──

    def get_last_order(self) -> dict | None:
        """获取最新创建的订单"""
        return self.query_one(
            "SELECT * FROM oc_order ORDER BY order_id DESC LIMIT 1"
        )

    def get_customer_by_email(self, email: str) -> dict | None:
        """根据邮箱查询用户"""
        return self.query_one(
            "SELECT * FROM oc_customer WHERE email = %s",
            (email,),
        )

    def get_product_stock(self, product_id: int) -> int | None:
        """查询商品库存"""
        row = self.query_one(
            "SELECT quantity FROM oc_product WHERE product_id = %s",
            (product_id,),
        )
        return row["quantity"] if row else None

    def order_exists(self, order_id: int) -> bool:
        """检查订单是否存在"""
        return self.count("oc_order", "order_id = %s", (order_id,)) > 0
