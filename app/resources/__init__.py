from flask_cors import CORS
from app import app
from flask import request
import os

def after_request(resp):
    mode = os.environ.get('MODE')
    if mode == 'PRODUCTION':
        allow_origin_list = ['http://localhost:8080']
    else:
        allow_origin_list = ['http://localhost:3000','http://localhost:8080','http://172.20.10.4:8080']

    if 'HTTP_ORIGIN' in request.environ and request.environ['HTTP_ORIGIN']  in allow_origin_list:
        resp.headers['Access-Control-Allow-Origin'] = request.environ['HTTP_ORIGIN']

    resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    resp.headers.add('Access-Control-Allow-Credentials', 'true')
    resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    return resp

def before_request():
    pass

app.after_request(after_request)
app.before_request(before_request)
