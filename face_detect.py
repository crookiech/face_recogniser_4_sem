import cv2
import os
import psycopg2
from psycopg2 import sql
import tempfile
import data

def load_face_model():
    conn = data.get_db_connection()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT model_data FROM face_models;")
            models = cur.fetchall()
            
            if not models:
                print("В базе данных нет обученных моделей!")
                return None
            temp_files = []
            try:
                for i, model_data in enumerate(models):
                    temp_filename = os.path.join(tempfile.gettempdir(), f"face_model_temp_{i}.yml")
                    with open(temp_filename, 'wb') as f:
                        f.write(model_data[0])
                    temp_files.append(temp_filename)
                    recognizer.read(temp_filename)
                return recognizer
            finally:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        return None
    finally:
        conn.close()

def get_user_names():
    conn = data.get_db_connection()
    user_names = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, name FROM users;")
            for user_id, name in cur.fetchall():
                user_names[str(user_id)] = name
    except Exception as e:
        print(f"Ошибка получения имен пользователей: {e}")
    finally:
        conn.close()
    return user_names

path = os.path.dirname(os.path.abspath(__file__))
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
font = cv2.FONT_HERSHEY_SIMPLEX
recognizer = load_face_model()
user_names = get_user_names()

if recognizer is None:
    print("Модель распознавания не загружена!")
    exit()

if not user_names:
    print("В базе данных нет пользователей!")
    exit()

cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Не удалось открыть камеру!")
    exit()

print("Распознавание лиц запущено. Нажмите 'q' для выхода.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Ошибка получения кадра с камеры!")
        continue  # Продолжаем цикл при ошибке кадра

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.2, 
        minNeighbors=5, 
        minSize=(100, 100)
    )

    for (x, y, w, h) in faces:
        try:
            nbr_predicted, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            confidence_percentage = max(0, 100 * (1 - (confidence / 150)))
            name = user_names.get(str(nbr_predicted), "Unknown") if confidence_percentage >= 50 else "Unknown"
            
            cv2.rectangle(frame, (x-20, y-20), (x+w+20, y+h+20), (225, 0, 0), 2)
            cv2.putText(frame, f"{name} ({confidence_percentage:.1f}%)", 
                        (x, y+h+30), font, 0.8, (0, 255, 0), 2)
        except Exception as e:
            print(f"Ошибка распознавания: {e}")

    cv2.imshow('Face Recognition', frame)
    
    # Единый вызов waitKey
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # 27 = ESC
        break

cam.release()
cv2.destroyAllWindows()
