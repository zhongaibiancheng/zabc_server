import base64
import psycopg2
import time
import requests

import xlsxwriter
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from flask import Flask, request,Blueprint,make_response,json,g,jsonify
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename

from app import app
from app.database.db_helper import db_helper
import app.common.common as common
from app.resources.auth import token_auth

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

student_bp = Blueprint('student_api', __name__)
student_api = Api(student_bp)

from app.utils.logging import get_logger
logger = get_logger()

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


class UsersResource(Resource):
    @cross_origin()
    @token_auth.login_required
    def get(self,registration_id):
        pass

class UsersQuizResource(Resource):
    @cross_origin()
    @token_auth.login_required
    def get(self,id):
        logger.debug("quiz id = " + id)
        sql = '''
            select 
                id,
                no,
                title,
                difficulty,
                source,
                remark
            from 
                quiz
            where 
                id = %d and delete_flg = 0
            order by
                id asc
        '''%(id)

        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                logger.debug(sql)
                cur.execute(sql)
                quizs = cur.fetchall()

                for quiz in quizs:
                    _sql = '''
                        select
                            master_knowledge.title
                        from
                            master_knowledge,
                            quiz_knowledge
                        where
                            quiz_knowledge.quiz_id = %d and 
                            master_knowledge.id = quiz_knowledge.knowledge_id
                            and quiz_knowledge.delete_flg = 0
                            and master_knowledge.delete_flg = 0
                        order by
                            master_knowledge.id asc
                    '''
                    logger.debug(_sql)

                    cur.execute(_sql)
                    knowledges = cur.fetchall()

                    knows = []
                    for konwledge in knowledges:
                        knows.append(konwledge['title'])
                    quiz['knowledges'] = ','.join(knows)

                response = app.response_class(
                    response=json.dumps({
                        'quizs': quizs,
                        'status':'success'
                        }),
                    status=200,
                    mimetype='application/json'
                )
                return response
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                conn.rollback()

###### url mapping
student_api.add_resource(UsersResource,"/login","/user",methods=['POST','GET'])
student_api.add_resource(UsersQuizResource,"/quizs","/quiz/<int:id>","/quiz",methods=['POST','GET'])
