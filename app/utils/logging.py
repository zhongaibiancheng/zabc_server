import logging,os
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #获取上级目录的绝对路径
# log_dir = BASE_DIR + '/log/ts.log'
log_dir = "/Users/lichenggang/WeChatProjects/EndPoint/Zhongaibiancheng/log/zabc.log"
def get_logger():
    #创建一个文件流并设置编码utf8
    fh = logging.FileHandler(log_dir,encoding='utf-8')

    #获得一个logger对象，默认是root
    logger = logging.getLogger("zabc.root")

    logging.Logger.manager.loggerDict.pop("zabc.root")
    # 将当前文件的handlers 清空 
    logger.handlers = []
    # 然后再次移除当前文件logging配置
    logger.removeHandler(logger.handlers)

    #设置最低等级debug
    logger.setLevel(logging.INFO)

    #设置日志格式
    fm = logging.Formatter(
        # '%(asctime)s %(name)s- %(thread)d- %(levelname)s- %(filename)s- %(message)s'
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
        )

    #把文件流添加进来，流向写入到文件
    logger.addHandler(fh)

    #把文件流添加写入格式
    fh.setFormatter(fm)
    
    return logger