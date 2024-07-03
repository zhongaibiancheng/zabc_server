import base64
import psycopg2
from app.database.db_helper import db_helper
from app import app
from flask import json,g
from app.utils.logging import get_logger
import requests
import datetime
import jwt
import os
import time

import qrcode
from flask import make_response

logger = get_logger()

def fetchFieldsInfo(registration_id,cur,conn):
    '''
    取得字段的基本信息
    跳转信息
    显示条件
    '''
    fields = []

    #报名的字段信息
    sql_fields = '''
        select
            id,
            registration_id,
            label as title,
            type,
            must_item as must_input,
            no,
            unique_key,
            check_type,
            conditions_count
        from
            fields
        where
            registration_id = %d
            and delete_flg = 0
        order by
            fields.no asc
        '''%(registration_id)

    #field 基本信息
    logger.info(sql_fields)
    cur.execute(sql_fields)
    
    fields = cur.fetchall()

    #radio/checkbox 选项信息
    sql_3_4 = '''
        select
            label
        from
            options
        where
            field_id = %d 
            and delete_flg = 0
        order by
            display_no asc
    '''
    for field in fields:
        field['display'] = True
        field['skipped'] = False
        
        type = field['type']
        #拼接选项
        if type == 3 or type == 4:
            logger.info("***** 拼接选项 ***** field['id']=%d"%(field['id']))
            sql_option = sql_3_4 % (field['id'])
            cur.execute(sql_option)
            options = cur.fetchall()
            values=[]
            for option in options:
                values.append(option['label'])
            field['options'] = values
        
        #显示信息
        if field['conditions_count'] != 0:
            sql_conditions_count = '''
                select
                    id,
                    relation
                from
                    field_show_condition
                where 
                    field_id = %d
            '''%(field['id'])
            logger.info(sql_conditions_count)
            cur.execute(sql_conditions_count)

            one = cur.fetchone()
            field_show_condition_id = one['id']
            relation = one['relation']

            sql_field_show_condition = '''
                select 
                    id,
                    unique_key,
                    no,
                    title,
                    type,
                    logic_condition,
                    checked
                from 
                    field_show_condition_item
                where 
                    field_show_condition_id = %d
                order by id asc
            '''%(field_show_condition_id)

            logger.info(sql_field_show_condition)
            cur.execute(sql_field_show_condition)

            show_conditino_items = cur.fetchall()

            for item in show_conditino_items:
                sql_field_show_condition_item_option = '''
                    select 
                    checked,
                    value,
                    label as text,
                    display_no
                from 
                    field_show_condition_item_option
                where 
                    field_show_condition_item_id =%d
                order by 
                    display_no asc
                '''%(item['id'])
                logger.info(sql_field_show_condition_item_option)
                cur.execute(sql_field_show_condition_item_option)
                options = cur.fetchall()

                item['options'] = options

            field['show_conditions'] = {
                'show_condition_fields':show_conditino_items,
                'relation':relation
            }

        else:
            field['show_conditions'] = {
                'show_condition_fields':[],
                'relation':0
            }

        #跳转设定
        skip_to_condition =  _get_skip_to_condition_info(field,cur,conn)
        field['skip_to_condition'] = skip_to_condition
        
        logger.info("跳转设定跳转设定跳转设定跳转设定 跳转设定")
    return fields

def _get_skip_to_condition_info(field,cur,conn):
    '''
    从 db 里面取得 设置的 跳转信息
    '''
    #默认返回值
    result = {
        'skip_to_options':[],
        'type':99,  
        'checkbox_setting':{},
        'radio_setting':[]
    }
    
    sql = "select id,type from skip_to_condition where field_id=%d"%(field['id'])
    logger.info(sql)
    cur.execute(sql)

    skip_to_condition = cur.fetchone()
    if skip_to_condition:
        skip_to_condition_id = skip_to_condition['id']
        skip_to_condition_type = skip_to_condition['type']

        if skip_to_condition_type == 0:#directly skip
            sql = '''
            select 
                id,
                skip_to_condition_id,
                unique_key,
                checked,
                no,
                title,
                text,
                value
            from 
                skip_to_option
            where
                skip_to_condition_id = %d
                order by id asc
            '''%(skip_to_condition_id)

            logger.info(sql)
            cur.execute(sql)
            datas = cur.fetchall()

            result = {
            'skip_to_options':datas,
            'type':0, 
            'checkbox_setting':{},
            'radio_setting':[]
            }
            return result
        elif skip_to_condition_type == 1:#按照選項跳轉
            if field['type'] == 3:#radio
                sql = '''select 
                    id,
                    skip_to_condition_id,
                    value,
                    text,
                    checked
                from
                    radio_skip_setting_item 
                where 
                    skip_to_condition_id=%d
                order by id asc    
                '''%(skip_to_condition_id)

                logger.info(sql)
                cur.execute(sql)
                radio_skip_setting_items = cur.fetchall()

                radio_skip_settings =[]
                for radio_skip_setting_item in radio_skip_setting_items:
                    sql ='''
                    select 
                        id,
                        radio_skip_setting_item_id,
                        unique_key,
                        checked,
                        no,
                        title,
                        text,
                        value 
                    from 
                        radio_skip_setting_item_to_no
                    where
                        radio_skip_setting_item_id = %d
                    order by id asc
                    '''%(radio_skip_setting_item['id'])

                    logger.info(sql)
                    cur.execute(sql)

                    radio_skip_setting_item_to_no = cur.fetchone()
                    radio_skip_setting = {
                        'option':radio_skip_setting_item,
                        'skip_to_no':radio_skip_setting_item_to_no
                    }
                    radio_skip_settings.append(radio_skip_setting)

                result = {
                'skip_to_options':[],
                'radio_setting':radio_skip_settings,
                'checkbox_setting':{},
                'type':1
                }
                return result
            elif field['type'] == 4:#checkbox
                sql = '''
                    select 
                        id,
                        field_id,
                        logic_type
                    from 
                        checkbox_skip_setting
                    where 
                        field_id=%d
                '''%(field['id'])
                logger.info(sql)

                cur.execute(sql)
                checkbox_skip_setting = cur.fetchone()

                sql = '''
                select 
                    id,
                    checkbox_skip_setting_id,
                    value,
                    text,
                    checked
                from 
                    checkbox_skip_setting_item
                 where
                    checkbox_skip_setting_id = %d
                '''%(checkbox_skip_setting['id'])
            logger.info(sql)
            cur.execute(sql)

            checkbox_skip_setting_items = cur.fetchall()

            sql = '''
                select 
                    id,
                    checkbox_skip_setting_item_id,
                    unique_key,
                    checked,
                    no,
                    title,
                    text,
                    value
                from
                    checkbox_skip_setting_item_to_no
                where
                    checkbox_skip_setting_item_id = %d
            '''%(checkbox_skip_setting['id'])
            
            logger.info(sql)
            cur.execute(sql)

            checkbox_skip_setting_item_to_no = cur.fetchone()

            checkbox_setting = {
                'logic_type':checkbox_skip_setting['logic_type'],
                'options':checkbox_skip_setting_items,
                'skip_to_no':checkbox_skip_setting_item_to_no
            }	

            result = {
                        'skip_to_options':[],
                        'type':1, 
                        'checkbox_setting':checkbox_setting,
                        'radio_setting':[],
                        }
            return result
    else:
        return result

def fetchRegistration(registration_id,user_id=None):

    # logger.info("***** fetchRegistration ***** registration_id=%d user_id=%d"%(registration_id,user_id))
    """
    根据报名id获得报名的基本信息（不是学生填写的报名信息）

    Parameters:
    registration_id (int): 报名id。
    user_id (int): 用户id （创建报名的管理者id）
                    None时，只取得报名的基本信息 客户端调用

    Returns:
        object: 报名的基本信息。
        None:报名不存在或者已经过期

    Raises:None
    """
    sql_registration = ''
    #报名基本信息
    if user_id != None:
        sql_registration = '''
            select 
                id,
                title,
                description_text,
                to_char(expired_date,'yyyy-MM-dd')as expired_date,
                type,
                payment,
                kingaku,
                qr_code_file_url,
                cover_file_url
            from 
                registration 
            where 
                id=%d and 
                created_user_id = %d'''%(registration_id,user_id)
    else:
        sql_registration = '''
            select 
                id,
                title,
                description_text,
                to_char(expired_date,'yyyy-MM-dd')as expired_date,
                type,
                payment,
                kingaku,
                qr_code_file_url,
                cover_file_url
            from 
                registration 
            where 
                id=%d and 
                to_char(expired_date,'yyyy-MM-dd') >= to_char(now(),'yyyy-MM-dd')'''%(registration_id)
    #报名的字段信息
    logger.info("报名的字段信息 sql=%s"%(sql_registration))

    data = {}
    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        try:
            logger.info(sql_registration)
            #报名基本信息
            cur.execute(sql_registration)
            row = cur.fetchone()
            logger.info(row)

            if user_id == None and row == None:
                return None

            logger.info("before setting")
            data['id'] = row['id']
            data['title'] = row['title']
            data['desc'] = row['description_text']
            data['end_date'] = row['expired_date']
            data['type'] = row['type']
            data['payment'] = row['payment']
            data['kingaku'] = row['kingaku']
            data['qr_code_file_url']= row['qr_code_file_url']
            data['cover_images']= '' if not row['cover_file_url'] else app.config['STATIC_URL']+row['cover_file_url']+"?timestamp=" + str(int(time.time()*1000))
            
            logger.info(data)
            if data['qr_code_file_url']:
                with open(data['qr_code_file_url'],"rb") as f:
                    data_ = f.read()
                    image = base64.b64encode(data_).decode('utf-8')

                    data["qr_code"] = image
                    f.close()
            #field 基本信息
            fields = fetchFieldsInfo(data['id'],cur,conn)

            logger.info(fields)

            #把字段信息放到报名里面
            if data:
                data['fields'] = fields

        except (Exception, psycopg2.DatabaseError) as error:
            logger.info(error)
            raise error

    return data

#
#学员的报名信息
#
def fetchStudentRegistration(registration_id):
    sql_registration = '''
                        select
                            title,
                            description_text,
                            to_char(expired_date, 'yyyy-MM-dd') as expired_date,
                            type,
                            payment,
                            status,
                            qr_code_file_url
                        from
                            registration
                        where
                            id = % d
    '''%(registration_id)
    sql_student_registration = '''
                                select
                                    registration.id as registration_id,
                                    student_registration.student_id,
                                    student_registration.interview_result,
                                    student_registration.interview_message,
                                    student_registration.reveive_message,
                                    to_char(student_registration.created_at,'yyyy-MM-dd HH24:MI:SS') as registrate_date, 
                                    student_registration.id as student_registration_id,
                                    CASE 
                                        WHEN student_registration_review_result.student_registration_id is not null THEN 'reviewed'
                                        ELSE 'unreviewed'
                                    END AS reviewed
                                from
                                    registration,
                                    student_registration left join student_registration_review_result on 
                                    student_registration.id = student_registration_review_result.student_registration_id
                                where
                                    registration.id = student_registration.registration_id and 
                                    registration.id = %d
                                order by student_registration.created_at asc'''%(registration_id)

    sql_student_registration_fields = '''
                    select
                        student_registration.id,
                        fields.label,
                        fields.type,
                        student_registration_fields.value,
                        student_registration_fields.field_id
                    from
                        student_registration_fields,
                        student_registration,
                        fields
                    where
                        student_registration.id = student_registration_fields.student_registration_id
                        and student_registration.registration_id = fields.registration_id
                        and student_registration_fields.field_id = fields.id
                        and student_registration.id = %d
                        and student_registration.registration_id = %d
                        order by fields.no asc
                    '''

    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        try:
            logger.info(sql_registration)
            cur.execute(sql_registration)
            registration = cur.fetchone()

            if registration['qr_code_file_url']:
                with open(registration['qr_code_file_url'],'rb') as f:
                    data = f.read()
                    encoded_string = base64.b64encode(data).decode('utf-8')
                    registration['qr_code'] = encoded_string
                    f.close()

            logger.info(sql_student_registration)
            cur.execute(sql_student_registration)
            students = cur.fetchall()

            for student in students:
                sql = sql_student_registration_fields%(student['student_registration_id'],registration_id)
                logger.info(sql)
                cur.execute(sql)
                fields = cur.fetchall()
                
                for field in fields:
                    if field['type'] == 5:#image
                        if field['value'] and field['value'] != '':
                            file_name = os.path.join(app.config['BASE_PATH_UPLOAD_STUDENT']%student['student_id'],field['value'])
                            image_url = app.config['STATIC_URL'] + file_name
                            field['image_url'] = image_url

                student['fields'] = fields
                student['show_detail'] = False
                student['checked'] = True

            registration['students'] = students
        except (Exception, psycopg2.DatabaseError) as error:
            logger.info(error)
            raise error

    return registration

def fetchSigninsByClassId(class_id):
        sql = '''
                select
                    id,
                    class_id,
                    title,
                    description_text as desc,
                    to_char(start_date, 'yyyy-MM-dd') as start_date,
                    to_char(end_date, 'yyyy-MM-dd') as end_date,
                    signin_remind_time,
                    signin_start_time,
                    signin_end_time,
                    place_signin,
                    wifi_signin
                from
                    signin
                where
                    class_id = %d and 
                    to_char(signin.start_date, 'yyyy-MM-dd') >= to_char(now(), 'yyyy-MM-dd') and 
                    to_char(signin.end_date, 'yyyy-MM-dd') <= to_char(now(), 'yyyy-MM-dd') and
                    signin_start_time <= to_char(now(),'hh24:MI') and 
                    signin_end_time >= to_char(now(),'hh24:MI')
                '''
        with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
            try:
                sql = sql %(class_id)
                logger.info(sql)
                cur.execute(sql)
                
                signins = cur.fetchall()

                return signins
            except (Exception, psycopg2.DatabaseError) as error:
                conn.rollback()
                logger.info(error)
                raise error
        return []

def _delete_field_addition_info(registration_id,cur,conn):
    '''
    删除报名信息字段的相关表
    为了更新报名信息的时候使用
    '''
    #删除选项
    delete_options="delete from options where field_id in(select id from fields where registration_id=%d)"%(registration_id)
    logger.info(delete_options)
    cur.execute(delete_options)

    sql_fields = "select id from fields where registration_id = %d" %(registration_id)
    logger.info(sql_fields)
    cur.execute(sql_fields)
    fields = cur.fetchall()

    for field in fields:
        sql = "select id from field_show_condition where field_id = %d" % field['id']
        logger.info(sql)
        cur.execute(sql)

        field_show_conditions = cur.fetchall()

        for field_show_condition in field_show_conditions:
            sql = "select id from field_show_condition_item where field_show_condition_id = %d"%(field_show_condition['id'])
            logger.info(sql)
            cur.execute(sql)

            field_show_condition_items = cur.fetchall()

            for f_s_c_i in  field_show_condition_items:
                sql = "delete from field_show_condition_item_option where field_show_condition_item_id = %d"%(f_s_c_i['id'])
                logger.info(sql)
                cur.execute(sql)

                sql = "delete from field_show_condition_item where id=%d"%(f_s_c_i['id'])
                logger.info(sql)
                cur.execute(sql)

            sql = "delete from field_show_condition where id=%d"%(field_show_condition['id'])
            logger.info(sql)
            cur.execute(sql)

        sql = "delete from fields where id =%d"%(field['id'])
        logger.info(sql)
        cur.execute(sql)

def _update_registration_to_db(registration,registration_id):
    '''
    更新报名信息的数据库更新
    '''
    user_id = g.user['id']

    title = registration.get('title')
    description_text = registration.get('desc')
    expired_date = registration.get('end_date')
    type = registration.get("type")
    fields = registration.get('fields')
    payment = registration.get('payment')
    kingaku = registration.get('kingaku')


    sql_registration = '''
        update 
            registration
        set 
            title='%s',
            description_text = '%s',
            expired_date = to_timestamp('%s','yyyy-MM-dd'),
            updated_user_id = %d,
            type = %s,
            payment=%s,
            kingaku=%s
        where
            id = %d
        '''
    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        try:
            sql = sql_registration %(title,description_text,expired_date,user_id,type,payment,kingaku,registration_id)
            logger.info(sql)
            cur.execute(sql)

            registration_id = registration['id']

            #删除既存信息
            _delete_field_addition_info(registration_id,cur,conn)

            #保存新的信息
            _save_field_to_db(fields,registration_id,cur,conn)

            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            logger.info(error)
            raise error

    return

def _save_field_to_db(fields,registration_id,cur,conn):
    sql_fields = '''insert into fields(
        registration_id,
        label,
        type,
        must_item,
        no,
        unique_key,
        check_type,
        conditions_count,
        created_at,
        updated_at)values(%d,'%s',%s,%s,%s,'%s',%s,%s,now(),now())RETURNING id'''

    #多选/单选 选项列表
    sql_options = '''insert into options(
        field_id,
        label,
        display_no,
        created_at,
        updated_at)values(%d,'%s',%d,now(),now())'''

    #显示条件
    sql_field_show_condition = '''insert into field_show_condition(field_id,relation,created_at,updated_at)values(
        %d,%s,now(),now())RETURNING id'''

    #设为显示条件的一个字段
    sql_field_show_condition_item = '''
        insert into field_show_condition_item(
            field_show_condition_id,
            unique_key ,
            no,
            title,
            type,
            checked,
            logic_condition,
            created_at,
            updated_at)values(%d,'%s',%s,'%s',%s,'%s',%s,now(),now())RETURNING id
    '''
    #设为显示条件的一个字段 的选项
    sql_field_show_condition_item_option = '''
        insert into field_show_condition_item_option(
            field_show_condition_item_id,
            checked,
            value,
            label,
            display_no,
            created_at,
            updated_at)values(
            %d,'%s',%s,'%s',%s,now(),now())RETURNING id'''
    
    try:
        for field in fields:
            sql = sql_fields % (
                registration_id,
                field['title'],
                field['type'],
                field['must_input'],
                field['no'],
                field['unique_key'],
                field['check_type'],
                field['conditions_count'] if 'conditions_count' in field else '0')
            
            logger.info(sql)
            cur.execute(sql)

            field_id = cur.fetchone()['id']
            if field['type'] == 3 or field['type'] == 4:#单选或者多选的字段
                logger.info(field)

                values = field['options']
                index_op = 0
                for value in values:
                    sql = sql_options %(field_id,value,index_op)
                    cur.execute(sql)
                    logger.info(sql)
                    index_op = index_op + 1

            show_conditions = field['show_conditions']
            if field['conditions_count'] > 0 and show_conditions and len(show_conditions['show_condition_fields'])>0:#设置了显示条件

                relation = show_conditions['relation']
                show_condition_fields = show_conditions['show_condition_fields']
                sql = sql_field_show_condition %(field_id,relation)
                cur.execute(sql)
                logger.info(sql)

                field_show_condition_id = cur.fetchone()['id']

                for field_show_condition_item in show_condition_fields:
                    logger.info(field_show_condition_item)
                    options = field_show_condition_item['options']

                    unique_key = field_show_condition_item['unique_key']
                    logic_condition = field_show_condition_item['logic_condition']
                    no = field_show_condition_item['no'] if 'no' in field_show_condition_item else -1
                    title = field_show_condition_item['title']
                    type = field_show_condition_item['type']

                    checked = field_show_condition_item['checked']
                    sql = sql_field_show_condition_item%(field_show_condition_id,
                    unique_key,no,title,type,'t' if checked else 'f',logic_condition
                    )
                    cur.execute(sql)
                    logger.info(sql)

                    field_show_condition_item_id = cur.fetchone()['id']

                    for option in options:
                        logger.info(option)
                        sql = sql_field_show_condition_item_option%(
                            field_show_condition_item_id,
                            't' if option['checked'] else 'f',
                            option['value'],
                            option['text'],
                            option['value']
                        )
                        cur.execute(sql)
                        logger.info(sql)
            if field['skip_to_condition']:#跳转条件
                _save_skip_to_info_to_db(field,field_id,cur,conn)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.info(error)
        raise error

def _save_skip_to_info_to_db(field,field_id,cur,conn):
    skip_to_condition = field['skip_to_condition']
    if int(skip_to_condition['type']) == 99:#no skip setting
        return

    elif int(skip_to_condition['type']) == 0:#skip directly
        sql_skip_to_condition = '''
        insert into skip_to_condition(
            field_id,
            type,
            created_at,
            updated_at
                )values(%d,%d,now(),now())RETURNING id
        '''
        sql = sql_skip_to_condition%(field_id,0)
        logger.info(sql)
        cur.execute(sql)
        skip_to_condition_id = cur.fetchone()['id']

        sql_skip_to_option = '''
        insert into skip_to_option(
            skip_to_condition_id,
            unique_key,
            checked,
            no,
            title,
            text,
            value,
            created_at,
            updated_at
        )values(
            %d,'%s','%s',%s,'%s','%s',%s,now(),now()
        )
        '''
        skip_to_options = skip_to_condition['skip_to_options']
        for s_t_c in skip_to_options:
            unique_key = s_t_c['unique_key']
            checked = s_t_c['checked']
            no = s_t_c['no'] if 'no' in s_t_c else -1
            title = s_t_c['title']
            text = s_t_c['text']
            value = s_t_c['value']

            sql = sql_skip_to_option%(
                skip_to_condition_id,
                unique_key,
            't' if checked else 'f',
            no,
            title,
            text,
            value)

            logger.info(sql)
            cur.execute(sql)

    elif int(skip_to_condition['type']) == 1:#skip by item selected
        logger.info(skip_to_condition)
        if field['type'] == 3 and skip_to_condition['radio_setting']:#radio
            sql_skip_to_condition = '''
            insert into skip_to_condition(
                field_id,
                type,
                created_at,
                updated_at
                )values(%d,%d,now(),now())RETURNING id
        '''
            sql = sql_skip_to_condition%(field_id,1)
            logger.info(sql)
            cur.execute(sql)
            skip_to_condition_id = cur.fetchone()['id']

            sql_radio_setting = '''
            insert into radio_skip_setting_item(
                    skip_to_condition_id,
                    value,
                    text,
                    checked,
                    created_at,
                    updated_at)values(%d,'%s','%s','%s',now(),now())RETURNING id
            '''

            sql_radio_skip_setting_item_to_no = '''
                insert into radio_skip_setting_item_to_no(
                    radio_skip_setting_item_id,
                    unique_key ,
                    checked,
                    no,
                    title,
                    text,
                    value,
                    created_at,
                    updated_at)values(%d,'%s','%s',%s,'%s','%s',%d,now(),now())
            '''
            radio_settings = skip_to_condition['radio_setting']
            index = 0

            for rs in radio_settings:
                rs_option = rs['option']
                value = rs_option['value']
                text = rs_option['text']
                checked = rs_option['checked']

                sql = sql_radio_setting %(skip_to_condition_id,value,text,'t' if skip_to_condition_id else 'f')
                cur.execute(sql)
                logger.info(sql)

                radio_skip_setting_item_id = cur.fetchone()['id']

                item_to_no = rs['skip_to_no']
                unique_key = item_to_no['unique_key']
                checked = item_to_no['checked']
                no = item_to_no['no'] if 'no' in item_to_no else '-1'
                title = item_to_no['title'] if 'title' in item_to_no else ''
                text = item_to_no['text'] if 'text' in item_to_no else ''

                value = index

                sql = sql_radio_skip_setting_item_to_no%(
                    radio_skip_setting_item_id,
                    unique_key,
                    't' if checked else 'f',
                    no,
                    title,
                    text,
                    value
                    )
                cur.execute(sql)
                logger.info(sql)
                index = index + 1


        if field['type'] == 4 and skip_to_condition['checkbox_setting']:#check box
            sql = '''insert into 
                        skip_to_condition(
                            field_id,
                            type,
                            created_at,
                            updated_at)values(%d,1,now(),now())'''%(field_id)
            logger.info(sql)
            cur.execute(sql)

            checkbox_setting = skip_to_condition['checkbox_setting']
            sql_skip_to_condition = '''
            insert into checkbox_skip_setting(
                field_id,
                logic_type,
                created_at,
                updated_at
            )values(%d,%s,now(),now())RETURNING id
        '''
            logic_type = checkbox_setting['logic_type']
            sql = sql_skip_to_condition%(field_id,logic_type)
            logger.info(sql)
            cur.execute(sql)

            checkbox_skip_setting_id = cur.fetchone()['id']
            logger.debug("step 1")

            sql_checkbox_skip_setting = '''
                insert into checkbox_skip_setting_item(
                    checkbox_skip_setting_id,
                    value,
                    text,
                    checked,
                    created_at,
                    updated_at)values(%d,%d,'%s','%s',now(),now() )RETURNING id
            '''

            logger.debug("step 2")
            sql_checkbox_skip_setting_item_to_no = '''
            insert into checkbox_skip_setting_item_to_no(
                checkbox_skip_setting_item_id,
                unique_key ,
                checked,
                no,
                title,
                text,
                value,
                created_at,
                updated_at)values(%d,'%s','%s',%s,'%s','%s',%s,now(),now())
            '''
            logger.debug("step 3")

            options = checkbox_setting['options']
            logger.info(options)
            for option in options:
                sql = sql_checkbox_skip_setting%(
                    checkbox_skip_setting_id,
                    option['value'],
                    option['text'],
                    't' if option['checked'] else 'f')
                logger.info(sql)
                cur.execute(sql)

            logger.info(checkbox_setting)
            item_to_no = checkbox_setting['skip_to_no']
            logger.info(item_to_no)
            unique_key = item_to_no['unique_key']
            checked = item_to_no['checked']
            no = item_to_no['no'] if 'no' in item_to_no else -1
            title = item_to_no['title']
            text = item_to_no['text']
            value = item_to_no['value'] if 'value' in item_to_no else '0'

            
            logger.info(no)
            sql = sql_checkbox_skip_setting_item_to_no%(
                checkbox_skip_setting_id,
                unique_key,
                't' if checked else 'f',
                no,
                title,
                text,
                value)

            cur.execute(sql)
            logger.info(sql)

def update_uploader_file(id,file_path_,cur,conn):
    try:
        sql = "select cover_file_url from registration where id=%d"%(id)
        logger.info(sql)
        cur.execute(sql)
        cover = cur.fetchone()
        if cover:
            file_path = cover['cover_file_url']
            if file_path:
                full_path = os.path.join(app.config["TMP_DATA_PATH"],file_path)

                os.remove(full_path)

                sql = "update registration set cover_file_url=null where id=%d" %(id)
                logger.info(sql)
                cur.execute(sql)

        sql = "update registration set cover_file_url='%s' where id=%d" %(file_path_,id)
        logger.info(sql)
        cur.execute(sql)

        conn.commit()
    except(Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        logger.info(error)
        raise error

def _save_to_db(registration):
    '''
    报名信息存入数据库
    '''
    user_id = g.user['id']

    logger.info(registration)

    title = registration['title']

    description_text = registration['desc']
    expired_date = registration['end_date']

    type = registration['type']
    fields = registration['fields']

    payment = registration['payment']
    kingaku = registration['kingaku']

    sql_registration = '''insert into registration(
        title,
        description_text,
        expired_date,
        status,
        created_user_id,
        created_at,
        updated_user_id,
        updated_at,
        type,
        payment,
        kingaku)values(
            '%s',
            '%s',
            to_timestamp('%s','yyyy-MM-dd'),
            0,
            %d,
            now(),
            %d,
            now(),
            %s,
            %s,
            %s)RETURNING id'''

    registration_id = -1
    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        try:
            sql = sql_registration %(
                title,
                description_text,
                expired_date,
                user_id,
                user_id,
                type,
                payment,
                kingaku)
            logger.info(sql)
            cur.execute(sql)
            
            registration_id = cur.fetchone()['id']
            _save_field_to_db(fields,registration_id,cur,conn)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            logger.info(error)
            raise error
    
    return {
        'id':registration_id
    }

#扫普通链接二维码打开小程序
def create_qrcode(data,img_file,registration_id):
    logger.info(data)
    logger.info(img_file)

    # 实例化QRCode生成qr对象
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    # 传入数据
    qr.add_data(data)
    
    qr.make(fit=True)
    
    # 生成二维码
    img = qr.make_image()
    
    # 保存二维码
    img.save(img_file)

    logger.info("保存二维码保存二维码保存二维码")
    with db_helper.get_resource(app.config,autocommit=False) as (cur,conn):
        sql = '''
                update 
                    registration 
                set 
                    status = 1,
                    qr_code_file_url='%s' 
                where 
                    id=%s'''%(img_file,registration_id)
        cur.execute(sql)
        conn.commit()

    with open(img_file,'rb') as f:
        data = f.read()
        f.close()
        encoded_string = base64.b64encode(data).decode('utf-8')

        return encoded_string

def _createRegistrationQRCode(registration_id):
    '''
    create mini program qr code 
    kui hua code
    '''
    #access token
    url = 'https://api.weixin.qq.com/cgi-bin/token'

    appid = app.config['APPID_STUDENT']
    appsecret = app.config['APPSECRET_STUDENT']

    payload = {
        'grant_type':'client_credential', 
        'appid': appid,
        'secret': appsecret}

    resp = requests.get(url, params=payload)
    r_json = resp.json()
    access_token = r_json['access_token']

    url_qr_code = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token=%s'
    data = {
        "page":'pages/registration/registration',
        "scene":registration_id,
        "width": 430,
        "auto_color": False,
        "line_color": {"r": "0", "g": "0", "b": "0"}
    }
    rep = requests.post(url_qr_code%(access_token),json=data)
    logger.info("create qr code status_code="+str(rep.status_code))

    return rep

def make_token(user_id,role):
    '''
    生成 token 客户端用来当成 cookies 使用
    user_id:
            用户 id
    role:角色 0：学生 1：管理员
    '''
    expireTime = datetime.date.today()+datetime.timedelta(days=1)
    user_info = {
        "id":user_id,
        "role":role,
        "expireTime":expireTime.strftime("%Y/%m/%d %Hh%Mm%S")
        }
    
    token = jwt.encode(
            user_info,
            app.config['SECRET_KEY'], 
            algorithm='HS256')
    
    return token

def _get_admin_user(user_id,cur):
    sql = '''
            select 
                nickname,
                icon 
            from 
                admin_users 
            where 
                id=%d''' %(user_id)

    logger.info(sql)
    cur.execute(sql)

    user = cur.fetchone()
    icon_file_path = user['icon']

    if icon_file_path:
        with open(icon_file_path,"rb") as f:
            data = f.read()
            encoded_string = base64.b64encode(data).decode('utf-8')
            user['icon_base64'] = encoded_string
    
    return user
