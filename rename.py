import cv2
import os
import psycopg2
from psycopg2 import sql
import data

path = os.path.dirname(os.path.abspath(__file__))

classifier_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def rename_user(oldName, newName):
    try:
        conn = data.get_db_connection()
        with conn.cursor() as cur:

            # Сначала проверяем, есть ли пользователь с oldName
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM users WHERE name = %s;"),
                (oldName,)
            )
            count = cur.fetchone()[0]
            if count == 0:
                # Пользователь не найден
                return False, f"Пользователь с именем '{oldName}' не найден."
            # Если есть, обновляем имя
            cur.execute(
                sql.SQL("UPDATE users SET name = %s WHERE name = %s;"),
                (newName, oldName)
            )
        conn.commit()
        return True, None
    except Exception as e:
        return False, f"Ошибка при переименовании пользователя: {e}"



if not os.path.exists('dataSet'):
    os.makedirs('dataSet')

import sys

try:
    if len(sys.argv) > 2:
        oldName = sys.argv[1]
        newName = sys.argv[2]
    else:
        print("Ошибка: имя не передано!")
        exit()
except Exception as e:
    print(f"Ошибка при вводе имени: {e}")
    exit()

rename_user(oldName, newName)

cv2.destroyAllWindows()