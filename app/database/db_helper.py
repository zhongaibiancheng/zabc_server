import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from contextlib import contextmanager
import atexit

import unittest
from unittest.mock import patch, MagicMock

from unittest.mock import MagicMock

# class DBHelper:
#     def get_resource(self, config, autocommit=False):
#         class Resource:
#             def __enter__(self):
#                 # 返回模拟的游标和连接对象
#                 return MagicMock(), MagicMock()

#             def __exit__(self, exc_type, exc_val, exc_tb):
#                 # 处理资源的清理
#                 pass

#         return Resource()

# db_helper = DBHelper()

class DBHelper:
    def __init__(self):
        self._connection_pool = None

    def initialize_connection_pool(self,app):
        self._connection_pool = pool.ThreadedConnectionPool(20,50,
        database=app['DB_SCHEMA'], 
        user=app['DB_USER'], 
        password=app['DB_PASS'], 
        host=app['DB_URI'], 
        port=app['DB_PORT'],
        keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=5)
    
    @contextmanager
    def get_resource(self, app,autocommit=True):
        if self._connection_pool is None:
            self.initialize_connection_pool(app)

        conn = self._connection_pool.getconn()
        conn.autocommit = autocommit
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            yield cursor, conn
        finally:
            cursor.close()
            # self._connection_pool.putconn(conn,close=True)
            self._connection_pool.putconn(conn)

    def shutdown_connection_pool(self):
        if self._connection_pool is not None:
            self._connection_pool.closeall()

db_helper = DBHelper()

# 
# 退出
# 
@atexit.register
def shutdown_connection_pool():
    db_helper.shutdown_connection_pool()