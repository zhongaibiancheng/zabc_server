#-*- encoding: utf-8 -*-


import psycopg2
import psycopg2.extras
# 数据库连接参数
## dbname: the database name
## database: the database name (only as keyword argument)
## user: user name used to authenticate
## password: password used to authenticate
## host: database host address (defaults to UNIX socket if not provided)
## port: connection port number (defaults to 5432 if not provided)

conn = psycopg2.connect(database="zhong_ai_bian_cheng",
                        user="zhong_ai_bian_cheng_user01", 
                        password="Caonima1",
                        host="1.14.181.35", port="8050")
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)