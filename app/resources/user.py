#!/usr/bin/env python

import psycopg2
from app.database.db_helper import db_helper

from flask import Flask, request,Blueprint
from flask_restful import Resource, Api
from flask import json,g

from flask_cors import CORS, cross_origin

import random, string

import time
import jwt
from app import app

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

user_bp = Blueprint('user_api', __name__)
user_api = Api(user_bp)

from app.utils.logging import get_logger
logger = get_logger()
import app.common.common as common
import requests

import os
import base64

from flask_cors import CORS, cross_origin
from app.resources.auth import token_auth

class User(Resource):
    def post(self):
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器也会提交一个空的文件名
        if file.filename == '':
            return {'message': 'No selected file'}, 400
        
        # 也可以接收其他表单数据
        other_data = request.form.to_dict()

        icon_file_path = ''

        param = other_data['code']
        role = int(other_data['role'])
        nickname = other_data['nickname']

        if role == 0:#student
            appid = app.config['APPID_STUDENT']
            appsecret = app.config['APPSECRET_STUDENT']
        else:#admin
            appid = app.config['APPID_ADMIN']
            appsecret = app.config['APPSECRET_ADMIN']

        url = "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code"
        logger.debug(url%(appid,appsecret,param))
        resp = requests.get(url%(appid,appsecret,param))
        r_json = resp.json()
        openid = r_json['openid']

        user_id = -1
        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                sql = """
                    select 
                        id,
                        openid,
                        last_access_date 
                    from 
                        users 
                    where openid='%s' and delete_flg=0 and role=%d
                """%(openid,role)
                cur.execute(sql)
                logger.debug(sql)

                user = cur.fetchone()
                if user:#update
                    icon_file_path = app.config["DATA_PATH"]+("/student/%d/"%(user['id']))+'user_icon.png'
                    logger.debug(icon_file_path)
                    file.save(icon_file_path)
                    sql = '''
                        update
                            users
                        set
                            icon = '%s',
                            nickname = '%s',
                            online = 0
                        where
                            id = %d
                    '''%(icon_file_path,nickname,user['id'])
                    
                    logger.debug(sql)
                    cur.execute(sql)

                    conn.commit()
                else:#insert
                    #插入数据库
                    sql = """
                            insert into
                                users(
                                    openid,
                                    role,
                                    last_access_date,
                                    created_at,
                                    updated_at,
                                    nickname
                                )
                            values
                            ('%s', %d, now(), now(), now(),'%s') RETURNING id
                    """%(openid,role,nickname)
                    logger.debug(sql)
                    cur.execute(sql)

                    user = cur.fetchone()

                    user_id = user['id']

                    icon_file_path = app.config["DATA_PATH"]+("/student/%d/"%(user['id']))
                    logger.debug(icon_file_path)

                    if not os.path.exists(icon_file_path):
                        os.mkdir(icon_file_path)
                    
                    icon_file_path = icon_file_path +"user_icon.png"
                    file.save(icon_file_path)

                    logger.debug(icon_file_path)
                    sql = "update users set icon='%s' where id=%d" %(icon_file_path,user['id'])
                    cur.execute(sql)

                    conn.commit()

                sql = '''select 
                        id,
                        openid,
                        last_access_date,
                        icon,
                        nickname
                    from 
                        users 
                    where id=%d''' % (user['id'])
                
                logger.debug(sql)

                cur.execute(sql)
                user = cur.fetchone()

                icon_file_path = user['icon']
                with open(icon_file_path,"rb") as f:
                    data = f.read()
                    encoded_string = base64.b64encode(data).decode('utf-8')
                    user['icon_base64'] = encoded_string

                token = common.make_token(user['id'],0)

                response = app.response_class(
                response=json.dumps({
                    'token':token,
                    'user':user,
                    'code': 200,
                    'status':'success'
                    }),
                status=200,
                mimetype='application/json')

                return response
            except (Exception, psycopg2.DatabaseError) as error:
                conn.rollback()
                print('create users failure str=%s'%(str(error)))

    def get(self):
        '''
            查看用户是否登录学生共用

            学生：用户不存在的话，直接生成一条记录，
            生成token返回给前台
        '''
        param = request.args.get('code')
        role = int(request.args.get('role'))

        if role == 0:#student
            appid = app.config['APPID_STUDENT']
            appsecret = app.config['APPSECRET_STUDENT']

        url = "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code"
        logger.debug(url%(appid,appsecret,param))
        resp = requests.get(url%(appid,appsecret,param))
        r_json = resp.json()
        openid = r_json['openid']

        user_id = -1
        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                if role == 0:#student
                    sql = '''
                        select 
                            users.id,
                            users.openid,
                            users.last_access_date,
                            users.icon,
                            users.nickname,
                            users.online
                        from 
                            users
                        where users.openid= '%s' and users.delete_flg=0 and users.role=%d
 
                    '''%(openid,role)
                cur.execute(sql)
                logger.debug(sql)

                user = cur.fetchone()

                #online 0:online 1:offline
                if user and user['online'] == 0:
                    icon_file_path = user['icon']

                    if icon_file_path:
                        with open(icon_file_path,"rb") as f:
                            data = f.read()
                            encoded_string = base64.b64encode(data).decode('utf-8')
                            user['icon_base64'] = encoded_string

                    token = common.make_token(user['id'],0)

                    response = app.response_class(
                    response=json.dumps({
                        'token':token,
                        'user':user,
                        'code': 200,
                        'status':'success'
                        }),
                    status=200,
                    mimetype='application/json')

                    return response
                elif role == 0 and not user:
                    nickname =  ''.join(random.choice(string.ascii_letters) for x in range(10))
                    
                    #插入数据库
                    sql = """
                            insert into
                                users(
                                    openid,
                                    role,
                                    last_access_date,
                                    created_at,
                                    updated_at,
                                    nickname
                                )
                            values
                            ('%s', %d, now(), now(), now(),'%s') RETURNING id
                    """%(openid,role,nickname)
                    logger.debug(sql)
                    cur.execute(sql)

                    user = cur.fetchone()

                    user_id = user['id']

                    icon_file_path = app.config["DATA_PATH"]+("/student/%d/"%(user['id']))
                    logger.debug(icon_file_path)

                    if not os.path.exists(icon_file_path):
                        os.mkdir(icon_file_path)

                    logger.debug(icon_file_path)

                    sql = '''select 
                        id,
                        openid,
                        last_access_date,
                        icon,
                        nickname
                    from 
                        users 
                    where id=%d''' % (user['id'])
                
                    logger.debug(sql)

                    cur.execute(sql)
                    user = cur.fetchone()

                    conn.commit()

                    token = common.make_token(user['id'],0)

                    response = app.response_class(
                    response=json.dumps({
                        'token':token,
                        'user':user,
                        'code': 200,
                        'status':'success'
                        }),
                    status=200,
                    mimetype='application/json')

                    return response
                else:
                    response = app.response_class(
                    response = json.dumps({
                        "error": "用户不存在",
                        "message": "用户还没有登录系统.",
                        'code': 404
                    }),
                    status=200,
                    mimetype='application/json')
                    return response
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(str(error))
                conn.rollback()
    
class UserLogout(Resource):
    @cross_origin()
    @token_auth.login_required
    def post(self):
        user_id = g.user['id']
        sql = "update users set online=1 where id=%d"%(user_id)

        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                logger.debug(sql)
                cur.execute(sql)
                
                conn.commit()

                response = app.response_class(
                response=json.dumps({
                    'code': 200,
                    'status':'success'
                    }),
                status=200,
                mimetype='application/json')

                return response
            except (Exception, psycopg2.DatabaseError) as error:
                conn.rollback()

class UserProfile(Resource):    
    @cross_origin()
    @token_auth.login_required
    def post(self):
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器也会提交一个空的文件名
        if file.filename == '':
            return {'message': 'No selected file'}, 400
        
        # 也可以接收其他表单数据
        other_data = request.form.to_dict()

        icon_file_path = ''

        role = int(other_data['role'])
        nickname = other_data['nickname']

        user = g.user
        if role == 0:
            icon_file_path = app.config["DATA_PATH"]+("/student/%d/"%(user['id']))+'user_icon.png'
        else:
            icon_file_path = app.config["DATA_PATH"]+("/admin/%d/"%(user['id']))+'user_icon.png'
        logger.debug(icon_file_path)
        file.save(icon_file_path)
        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                sql = '''
                    update
                        users
                    set
                        icon = '%s',
                        nickname = '%s',
                        online = 0
                    where
                        id = %d
                '''%(icon_file_path,nickname,user['id'])
                            
                logger.debug(sql)
                cur.execute(sql)

                conn.commit()

                sql = '''select 
                        id,
                        openid,
                        last_access_date,
                        icon,
                        nickname
                    from 
                        users 
                    where id=%d''' % (user['id'])
                
                logger.debug(sql)

                cur.execute(sql)
                user = cur.fetchone()

                icon_file_path = user['icon']
                with open(icon_file_path,"rb") as f:
                    data = f.read()
                    encoded_string = base64.b64encode(data).decode('utf-8')
                    user['icon_base64'] = encoded_string
                    
                response = app.response_class(
                response=json.dumps({
                    'user':user,
                    'code': 200,
                    'status':'success'
                    }),
                status=200,
                mimetype='application/json')

                return response
            except (Exception, psycopg2.DatabaseError) as error:
                conn.rollback()

    @cross_origin()
    @token_auth.login_required
    def put(self):
        role = int(request.json.get('role'))
        nickname = request.json.get('nickname')

        user = g.user
       
        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                sql = '''
                    update
                        users
                    set
                        nickname = '%s',
                        online = 0
                    where
                        id = %d
                '''%(nickname,user['id'])
                            
                logger.debug(sql)
                cur.execute(sql)

                conn.commit()

                sql = '''select 
                        id,
                        openid,
                        last_access_date,
                        icon,
                        nickname
                    from 
                        users 
                    where id=%d''' % (user['id'])
                
                logger.debug(sql)

                cur.execute(sql)
                user = cur.fetchone()

                icon_file_path = user['icon']
                with open(icon_file_path,"rb") as f:
                    data = f.read()
                    encoded_string = base64.b64encode(data).decode('utf-8')
                    user['icon_base64'] = encoded_string
                
                response = app.response_class(
                response=json.dumps({
                    'user':user,
                    'code': 200,
                    'status':'success'
                    }),
                status=200,
                mimetype='application/json')

                return response
            except (Exception, psycopg2.DatabaseError) as error:
                conn.rollback()

user_api.add_resource(User,"/login",methods=['POST','GET'])
user_api.add_resource(UserLogout,"/logout",methods=['POST'])
user_api.add_resource(UserProfile,"/profile",methods=['POST',"PUT"])