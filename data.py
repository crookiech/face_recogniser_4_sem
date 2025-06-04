import cv2
import os
import psycopg2
from psycopg2 import sql
import tempfile

DB_CONFIG = {
    'dbname': 'mydatabase',
    'user': 'myuser',
    'password': '123456789',
    'host': '192.168.192.106',
    'port': '5432'

    # 'dbname': 'mydatabase',
    # 'user': 'postgres',
    # 'password': 'XXANTERIA_ISQ!-@FUNKED_UP198',
    # 'host': 'localhost',
    # 'port': '5432'
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        exit()