import cv2
import os
import numpy as np
from PIL import Image
import psycopg2
from psycopg2 import sql
import tempfile
import data

def save_face_model(user_id, model):
    temp_filename = os.path.join(tempfile.gettempdir(), f"face_model_{user_id}_{os.getpid()}.yml")
    try:
        model.save(temp_filename)
        with open(temp_filename, 'rb') as f:
            model_data = f.read()
        conn = data.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM face_models WHERE user_id = %s;",
                    (user_id,)
                )
                cur.execute(
                    "INSERT INTO face_models (user_id, model_data) VALUES (%s, %s);",
                    (user_id, psycopg2.Binary(model_data))
                )
            conn.commit()
            print(f"Модель лица для пользователя {user_id} сохранена в базу данных")
        except Exception as e:
            print(f"Ошибка при сохранении модели: {e}")
        finally:
            conn.close()
    finally:
        if os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as e:
                print(f"Не удалось удалить временный файл: {e}")

path = os.path.dirname(os.path.abspath(__file__))
recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
data_path = os.path.join(path, 'dataSet')
image_paths = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith('.jpg')]
images = []
labels = []
for image_path in image_paths:
    try:
        image_pil = Image.open(image_path).convert('L')
        image = np.array(image_pil, 'uint8')
        user_id = int(os.path.split(image_path)[1].split(".")[0].replace("face-", ""))
        faces = face_cascade.detectMultiScale(image)
        for (x, y, w, h) in faces:
            images.append(image[y: y + h, x: x + w])
            labels.append(user_id)
            cv2.imshow("Обучение модели...", image[y: y + h, x: x + w])
            cv2.waitKey(50)
    except Exception as e:
        print(f"Ошибка обработки {image_path}: {e}")
if not images:
    print("Нет изображений для обучения!")
unique_user_ids = list(set(labels))
for user_id in unique_user_ids:
    user_images = [img for img, lbl in zip(images, labels) if lbl == user_id]
    user_labels = [lbl for lbl in labels if lbl == user_id]
    user_recognizer = cv2.face.LBPHFaceRecognizer_create()
    user_recognizer.train(user_images, np.array(user_labels))
    save_face_model(user_id, user_recognizer)

cv2.destroyAllWindows()
print("Обучение завершено. Модели сохранены в базу данных.")

