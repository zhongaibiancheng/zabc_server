# config.py
import os
import gevent.monkey
gevent.monkey.patch_all()

import multiprocessing

import os
mode = os.environ.get('MODE')
if mode == 'DEVELOPMENT':
    debug = True
    loglevel = 'debug'
    bind = "0.0.0.0:5003"
    capture_output = True
    
elif mode == 'TEST':
    debug = True
    loglevel = 'debug'
    bind = "0.0.0.0:8051"

elif mode == 'PRODUCTION':
    debug = True
    loglevel = 'debug'
    bind = "0.0.0.0:8051"

pidfile = "log/gunicorn.pid"
accesslog = "log/access.log"
errorlog = "log/debug.log"
daemon = True
worker_connections = 200
max_requests = 1024
# keepalive = 3
preload_app = True
# 启动的进程数
# workers = multiprocessing.cpu_count()
workers = 1
# thread = 1
worker_class = 'gevent'
# worker_class = 'gthread'

x_forwarded_for_header = 'X-FORWARDED-FOR'
