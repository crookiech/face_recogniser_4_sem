import cv2
import os
import psycopg2
from psycopg2 import sql
import data

path = os.path.dirname(os.path.abspath(__file__))

classifier_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
if not os.path.exists(classifier_path):
    print("Ошибка: файл классификатора не найден!")
    exit()
detector = cv2.CascadeClassifier(classifier_path)
i = 0
offset = 50

video = cv2.VideoCapture(0)
if not video.isOpened():
    print("Ошибка: не удалось открыть камеру!")
    exit()

def get_max_user_id():
    try:
        conn = data.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(user_id), 0) FROM users;")
            max_id = cur.fetchone()[0]
        conn.close()
        return max_id
    except Exception as e:
        print(f"Ошибка при получении максимального ID: {e}")
        exit()

def add_user(user_id, name):
    try:
        conn = data.get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("INSERT INTO users (user_id, name) VALUES (%s, %s);"),
                (user_id, name)
            )
        conn.commit()
        conn.close()
        print(f"Пользователь {user_id} ({name}) добавлен в базу данных")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
        exit()

user_id = get_max_user_id() + 1

if not os.path.exists('dataSet'):
    os.makedirs('dataSet')

import sys

try:
    # name = input(f"Введите имя для пользователя {user_id}: ")
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        print("Ошибка: имя не передано!")
        exit()
except Exception as e:
    print(f"Ошибка при вводе имени: {e}")
    exit()

add_user(user_id, name)

while True:
    ret, im = video.read()
    if not ret:
        print("Не удалось получить изображение с камеры.")
        break
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
    for (x, y, w, h) in faces:
        i = i + 1
        face_img = gray[y-offset:y+h+offset, x-offset:x+w+offset]
        filename = f"dataSet/face-{user_id}.{i}.jpg"
        cv2.imwrite(filename, face_img)
        cv2.rectangle(im, (x-offset, y-offset), (x+w+offset, y+h+offset), (225, 0, 0), 2)
        cv2.imshow('im', im[y-offset:y+h+offset, x-offset:x+w+offset])
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
    if i > 50:
        break

video.release()
cv2.destroyAllWindows()