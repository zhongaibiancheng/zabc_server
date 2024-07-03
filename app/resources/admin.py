import base64
import json

import psycopg2
from app.database.db_helper import db_helper

from flask import Flask, request,Blueprint,make_response
from flask_restful import Resource, Api
from flask import json,g,jsonify

from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename

import time
import requests
from app import app
import xlsxwriter
from io import BytesIO
import os
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
from app.resources.auth import token_auth

admin_bp = Blueprint('admin_api', __name__)
admin_api = Api(admin_bp)

from app.utils.logging import get_logger
logger = get_logger()

import app.common.common as common
import uuid

@app.errorhandler(Exception)
def handle_exception(e):
    '''
    api 异常处理通用函数
    '''
    logger.error(f"未处理异常: {e}")
    response = {
        "message": "服务器内部错误",
        "details": str(e)
    }
    
    return jsonify(response), 500


class RegistrationGenerateResource(Resource):
    '''
        下载报名信息
        报名名单和填写的详细信息
    '''
    @cross_origin()
    @token_auth.login_required
    def get(self,registration_id):
        pass

###### url mapping
# admin_api.add_resource(UsersResource,"/login","/user",methods=['POST','GET'])
