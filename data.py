import cv2
import os
import psycopg2
from psycopg2 import sql
import tempfile

DB_CONFIG = {
    'dbname': 'mydatabase',
    'user': 'myuser',
    'password': '123456789',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        exit()
