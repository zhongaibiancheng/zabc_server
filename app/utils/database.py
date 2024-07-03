import psycopg2

def getConnection(app):
    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
        }
    conn = psycopg2.connect(database=app['DB_SCHEMA'], user=app['DB_USER'], password=app['DB_PASS'], host=app['DB_URI'], port=app['DB_PORT'],**keepalive_kwargs)
    return conn