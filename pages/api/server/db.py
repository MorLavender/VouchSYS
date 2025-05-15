import psycopg2
from psycopg2 import OperationalError

def get_connection():
    try:
        return psycopg2.connect(
            dbname='yourdb',
            user='youruser',
            password='yourpassword',
            host='localhost'
        )
    except OperationalError as e:
        print("Database connection error:", e)
        return None
