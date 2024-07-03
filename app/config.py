import os

class Config(object):
    SECRET_KEY = 'saduhsuaihfe332r32rfo43rtn3noiYUG9jijoNF23'

    # one week
    COOKIES_EXPIRES = 60*60*24*7

    #one day
    COOKIES_EXPIRES_ADMIN = 60*60*24

    SESSION_COOKIE_SECURE=True

#
#开发环境
#
class DevelopmentConfig(Config):
    DEBUG = True

    DB_URI='1.14.181.35'
    DB_PORT='8050'
    DB_USER='zhong_ai_bian_cheng_user01'
    DB_PASS='Caonima1'
    DB_SCHEMA='zhong_ai_bian_cheng'

    SQLALCHEMY_DATABASE_URI = "postgresql://%s:%s@%s:%s/%s"%(DB_USER,DB_PASS,DB_URI,DB_PORT,DB_SCHEMA)
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 3600

    CORS_ENABLED = True
#
#测试环境
#
class TestConfig(Config):
    DEBUG = False

    DB_URI='127.0.0.1'
    DB_PORT='8050'
    DB_USER='zhong_ai_bian_cheng_user01'
    DB_PASS='Caonima1'
    DB_SCHEMA='zhong_ai_bian_cheng'

    SQLALCHEMY_DATABASE_URI = "postgresql://%s:%s@%s:%s/%s"%(DB_USER,DB_PASS,DB_URI,DB_PORT,DB_SCHEMA)
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 3600

    CORS_ENABLED = True
#
#商用环境
#
class ProductionConfig(Config):
    DEBUG = False

    DB_URI='127.0.0.1'
    DB_PORT='8050'
    DB_USER='zhong_ai_bian_cheng_user01'
    DB_PASS='Caonima1'
    DB_SCHEMA='zhong_ai_bian_cheng'

    SQLALCHEMY_DATABASE_URI = "postgresql://%s:%s@%s:%s/%s"%(DB_USER,DB_PASS,DB_URI,DB_PORT,DB_SCHEMA)
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT = 3600

    CORS_ENABLED = True

def load_config(mode=os.environ.get('MODE')):
    """Load config."""
    try:
        if mode == 'PRODUCTION':
            return ProductionConfig

        elif mode == 'TEST':
            return TestConfig

        elif mode == 'DEVELOPMENT':
            return DevelopmentConfig
    except ImportError:
        return DevelopmentConfig

