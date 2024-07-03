from db import conn,cur

import logging
import sys
import xlrd

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'#配置输出日志格式
DATE_FORMAT = '%Y-%m-%d  %H:%M:%S %a ' #配置输出时间的格式，注意月份和天数不要搞乱了
logging.basicConfig(level=logging.DEBUG,
                    format=LOG_FORMAT,
                    datefmt = DATE_FORMAT ,
                    filename=r"/Users/lichenggang/WeChatProjects/EndPoint/Zhongaibiancheng/log/import.log" #有了filename参数就不会直接输出显示到控制台，而是直接写入文件
                    )


def import_from_excel(cur,conn):
    # 打开一个 Excel 文件
    file_path = '../datas/quiz.xls'
    workbook = xlrd.open_workbook(file_path)

    # 选择一个工作表
    sheet = workbook.sheet_by_index(0)  # 通过索引
    # 或者
    # sheet = workbook.sheet_by_name('Sheet1')  # 通过名字

    # 读取工作表中的所有数据
    sql = '''
        insert into quiz(
        no,
    title,
    difficulty,
    source,
    remark,
    created_at,
    updated_at)values(%s,'%s',%s,'%s','%s',now(),now())RETURNING id
    '''
    data = []

    # for row_idx in range(1,sheet.nrows):
    for row_idx in range(2,100):
        row = sheet.row_values(row_idx)
        one = [];
        for col_index in range(1,9):
            # logging.info(col_index,row[col_index])
            val = row[col_index]
            if col_index == 1 or col_index == 3:
                val = int(val)
                
            one.append(val)
            
        # logging.info(one)
        
        data.append(row)

    for s in data:
        s = sql%(one[0],one[1],one[2],one[3],one[4])
        logging.info(s)
        cur.execute(s);

        quiz_id = cur.fetchone()['id']

        logging.info(quiz_id)
        difficult = one[3].split(',')

        for f in difficult:
            _sql = '''
                    select 
                        id 
                    from 
                        master_knowledge 
                    where 
                        title = '%s'
                    '''%(f.lstrip().rstrip())
            cur.execute(_sql)
            logging.info(_sql)

            knowledges = cur.fetchone()
            if knowledges:
                id = knowledges['id']

                _sql = '''
                        insert into quiz_knowledge(
                        quiz_id,
                        knowledge_id,
                        created_at,
                        updated_at)values(%d,%d,now(),now())'''%(quiz_id,id)
                logging.info(_sql)
                cur.execute(_sql)

if __name__:
    logging.info("start importing to db ....")
    try:
        import_from_excel(cur,conn)
        conn.commit()
        logging.info("import successed!!")
    except Exception as e:
        conn.rollback()
        logging.error('Error occurred: %s', e)
        sys.exit(1)
