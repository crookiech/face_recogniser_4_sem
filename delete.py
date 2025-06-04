import cv2
import os
import psycopg2
from psycopg2 import sql
import data

path = os.path.dirname(os.path.abspath(__file__))

classifier_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def delete_user(name):
    try:
        conn = data.get_db_connection()
        with conn.cursor() as cur:
            # Проверяем, есть ли пользователь с таким именем
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM users WHERE name = %s;"),
                (name,)
            )
            count = cur.fetchone()[0]
            if count == 0:
                return False, f"Пользователь с именем '{name}' не найден."

            # Удаляем пользователя по имени
            cur.execute(
                sql.SQL("DELETE FROM users WHERE name = %s;"),
                (name,)
            )
        conn.commit()
        return True, None
    except Exception as e:
        return False, f"Ошибка при удалении пользователя: {e}"
    
if not os.path.exists('dataSet'):
    os.makedirs('dataSet')

import sys

try:
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        print("Ошибка: имя не передано!")
        exit()
except Exception as e:
    print(f"Ошибка при вводе имени: {e}")
    exit()

delete_user(name)

cv2.destroyAllWindows()
