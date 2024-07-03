from flask_httpauth import HTTPTokenAuth
from flask import request

token_auth = HTTPTokenAuth()
import jwt

from app.utils.logging import get_logger
from flask import g

from app.database.db_helper import db_helper
from app import app
import psycopg2

logger = get_logger()

@token_auth.verify_token
def verify_token(username_or_token):
    logger.debug(username_or_token)
    data = jwt.decode(username_or_token, app.config['SECRET_KEY'],
                              algorithms=['HS256'])

    logger.debug(data)
    if data['role'] == 0:#student
        sql = '''
            select 
                * 
            from 
                users 
            where 
                id= %d
        '''%(int(data['id']))
    elif data['role'] == 1:#admin
        sql = '''
            select 
                * 
            from 
                admin_users 
            where 
                id= %d
        '''%(int(data['id']))
    
    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        try:
            logger.debug(sql)
            cur.execute(sql)
            user = cur.fetchone()
            g.user = user

            return True
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error('Db access error user_id=%d str=%s'%(user.id,str(error)))
            raise error
    
    return False

@token_auth.error_handler
def error_handler():
    headers = [('WWW-Authenticate', '')]

    return ({
                'code': 401,
                'status':'401'
            },
            200,
            headers)
