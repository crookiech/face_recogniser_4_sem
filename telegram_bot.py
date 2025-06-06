import telebot
import psycopg2
from psycopg2 import sql
from telebot import types
import cv2
import os
import numpy as np
import tempfile
import data

bot = telebot.TeleBot('7329769633:AAEP1saNyDatm51t4WRG32nUdFGpQ3jHS_g')

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup1.add(
    types.KeyboardButton("Добавить пользователя"),
    types.KeyboardButton("Распознать пользователя по фотографии"),
    types.KeyboardButton("Распознать пользователя по видео"),
    types.KeyboardButton("Отмена")
)

current_handler = None

@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancel_handler(message):
    global current_handler
    if current_handler:
        bot.send_message(message.chat.id, "Текущая операция отменена.", reply_markup=markup1)
        current_handler = None
    else:
        bot.send_message(message.chat.id, "Нет активных операций для отмены.", reply_markup=markup1)

def load_user_names():
    """Загрузка имен пользователей из базы данных"""
    conn = data.get_db_connection()
    user_names = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, name FROM users;")
            for user_id, name in cur.fetchall():
                user_names[str(user_id)] = name
    except Exception as e:
        print(f"Ошибка загрузки пользователей: {e}")
    finally:
        conn.close()
    return user_names


def load_recognizer():
    """Загрузка модели распознавания из базы данных"""
    conn = data.get_db_connection()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    valid_models = []  # Для хранения валидных моделей
    
    try:
        with conn.cursor() as cur:
            # Получаем только непустые модели
            cur.execute("""
                SELECT user_id, model_data 
                FROM users 
                WHERE model_data IS NOT NULL AND octet_length(model_data) > 0;
            """)
            models = cur.fetchall()
            
            if not models:
                print("В базе данных нет обученных моделей!")
                return None
                
            temp_files = []
            try:
                for user_id, model_data in models:
                    # Создаем временный файл
                    temp_filename = os.path.join(tempfile.gettempdir(), f"face_model_{user_id}.yml")
                    with open(temp_filename, 'wb') as f:
                        f.write(model_data)
                    
                    # Проверяем валидность модели перед загрузкой
                    if is_valid_model_file(temp_filename):
                        temp_files.append(temp_filename)
                        recognizer.read(temp_filename)
                        valid_models.append(user_id)
                    else:
                        print(f"Невалидная модель для user_id={user_id}")
            finally:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.unlink(temp_file)
                        except Exception as e:
                            print(f"Ошибка удаления временного файла: {e}")
                
                if not valid_models:
                    print("Нет валидных моделей для загрузки!")
                    return None
                    
                print(f"Загружено {len(valid_models)} валидных моделей")
                return recognizer
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        return None
    finally:
        conn.close()

def is_valid_model_file(file_path):
    """Проверяет, является ли файл модели валидным"""
    try:
        # Попытка прочитать файл модели
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(file_path)
        
        # Дополнительная проверка наличия внутренних данных
        return hasattr(recognizer, 'getLabels') and recognizer.getLabels() is not None
    except:
        return False

def add_user_to_db(user_id, user_name):
    """Добавление нового пользователя в базу данных"""
    conn = data.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("INSERT INTO users (user_id, name, model_data) VALUES (%s, %s, %s);"),
                (user_id, user_name, psycopg2.Binary(b''))
            )
        conn.commit()
        print(f"Пользователь {user_name} (ID: {user_id}) добавлен в БД")
    except Exception as e:
        print(f"Ошибка добавления пользователя: {e}")
    finally:
        conn.close()

def save_model_to_db(recognizer, user_id):
    """Сохранение модели в базу данных"""
    # Сохраняем модель во временный файл
    temp_filename = os.path.join(tempfile.gettempdir(), f"model_{user_id}.yml")
    try:
        recognizer.save(temp_filename)
        
        # Проверяем, что файл не пустой
        if os.path.getsize(temp_filename) == 0:
            print(f"Пустой файл модели для user_id={user_id}")
            return False
            
        with open(temp_filename, 'rb') as f:
            model_data = f.read()
        
        # Обновляем запись в базе данных
        conn = data.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("UPDATE users SET model_data = %s WHERE user_id = %s;"),
                    (psycopg2.Binary(model_data), user_id)
                )
            conn.commit()
            print(f"Модель для user_id={user_id} сохранена в БД")
            return True
        except Exception as e:
            print(f"Ошибка сохранения модели: {e}")
            return False
        finally:
            conn.close()
    except Exception as e:
        print(f"Ошибка создания временного файла модели: {e}")
        return False
    finally:
        if os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as e:
                print(f"Ошибка удаления временного файла: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    keyboard = types.InlineKeyboardMarkup()
    key_1= types.InlineKeyboardButton(text='Добавить пользователя', callback_data='add_user')
    # И добавляем кнопку на экран
    keyboard.add(key_1)
    key_2 = types.InlineKeyboardButton(text='Распознать пользователя по фотографии', callback_data='recog_user')
    keyboard.add(key_2)
    key_3 = types.InlineKeyboardButton(text='Распознать пользователя по видео', callback_data='video')
    keyboard.add(key_3)
    bot.send_message(message.from_user.id, text='Привет! Я бот для распознавания лиц. \nВыберите действие:', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "Добавить пользователя")
def add_user_handler(message):
    global current_handler
    current_handler = "add_user"
    msg = bot.send_message(message.chat.id, "Введите имя пользователя:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_user_name)

def process_user_name(message):
    global current_handler
    if message.text == "Отмена":
        cancel_handler(message)
        return
    user_name = message.text
    conn = data.get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE name = %s;", (user_name,))
            if cur.fetchone():
                msg = bot.send_message(message.chat.id, f"Пользователь {user_name} уже существует. Введите другое имя:")
                bot.register_next_step_handler(msg, process_user_name)
                return
    finally:
        conn.close()
    
    msg = bot.send_message(message.chat.id, "Сколько фотографий вы хотите добавить?", reply_markup=markup1)
    bot.register_next_step_handler(msg, lambda msg: process_num_photos(user_name, msg))

def process_num_photos(user_name, message):
    global current_handler
    if message.text == "Отмена":
        cancel_handler(message)
        return
    try:
        num_photos = int(message.text)
        if num_photos <= 0:
            msg = bot.send_message(message.chat.id, "Введите положительное число:")
            bot.register_next_step_handler(msg, lambda msg: process_num_photos(user_name, msg))
            return
        conn = data.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(user_id), 0) FROM users;")
                user_id = cur.fetchone()[0] + 1
                add_user_to_db(user_id, user_name)
        finally:
            conn.close()
        msg = bot.send_message(message.chat.id, f"Отправьте {num_photos} фотографий пользователя:", reply_markup=markup1)
        bot.register_next_step_handler(msg, lambda msg: process_photo(msg, user_id, user_name, num_photos, 1))
    except ValueError:
        msg = bot.send_message(message.chat.id, "Введите число:", reply_markup=markup1)
        bot.register_next_step_handler(msg, lambda msg: process_num_photos(user_name, msg))

def process_photo(message, user_id, user_name, total_photos, current_photo):
    global current_handler
    if message.text == "Отмена":
        cancel_handler(message)
        return
    if message.content_type != 'photo':
        msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте фотографию:", reply_markup=markup1)
        bot.register_next_step_handler(msg, lambda msg: process_photo(msg, user_id, user_name, total_photos, current_photo))
        return
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    nparr = np.frombuffer(downloaded_file, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
    if len(faces) != 1:
        msg = bot.send_message(message.chat.id, "На фотографии должно быть одно лицо. Попробуйте еще раз:", reply_markup=markup1)
        bot.register_next_step_handler(msg, lambda msg: process_photo(msg, user_id, user_name, total_photos, current_photo))
        return
    os.makedirs("dataSet", exist_ok=True)
    for (x, y, w, h) in faces:
        face_img = gray[y:y+h, x:x+w]
        cv2.imwrite(f"dataSet/face-{user_id}.{current_photo}.jpg", face_img)
    if current_photo < total_photos:
        msg = bot.send_message(message.chat.id, f"Ожидается еще {total_photos - current_photo} фото:", reply_markup=markup1)
        bot.register_next_step_handler(msg, lambda msg: process_photo(msg, user_id, user_name, total_photos, current_photo + 1))
    else:
        images, labels = [], []
        for filename in os.listdir("dataSet"):
            if filename.startswith(f"face-{user_id}"):
                img = cv2.imread(f"dataSet/{filename}", cv2.IMREAD_GRAYSCALE)
                images.append(img)
                labels.append(user_id)
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        recognizer.train(images, np.array(labels))
        save_model_to_db(recognizer, user_id)
        bot.send_message(message.chat.id, f"Пользователь {user_name} успешно добавлен!", reply_markup=markup1)
    current_handler = None 

@bot.message_handler(func=lambda message: message.text == "Распознать пользователя по фотографии")
def recognize_user_handler(message):
    global current_handler
    current_handler = "recognize_photo"
    msg = bot.send_message(message.chat.id, "Отправьте фотографию для распознавания:", reply_markup=markup1)
    bot.register_next_step_handler(msg, process_recognition_photo)

def process_recognition_photo(message):
    global current_handler
    if message.text == "Отмена":
        cancel_handler(message)
        return
    if message.content_type != 'photo':
        bot.reply_to(message, "Ошибка: Отправьте фотографию.", reply_markup=markup1)
        bot.register_next_step_handler(message, process_recognition_photo)
        return
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open('received_photo.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)
    processed_image = recognize_faces(downloaded_file)
    if processed_image is None:
        msg = bot.send_message(message.chat.id, "Лица не обнаружены. Отправьте другую фотографию.", reply_markup=markup1)
        bot.register_next_step_handler(msg, process_recognition_photo)
    else:
        bot.send_photo(message.chat.id, processed_image, caption="Результат распознавания", reply_markup=markup1)
    current_handler = None 

def recognize_faces(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.2, 
            minNeighbors=5, 
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(faces) == 0:
            return None
        recognizer = load_recognizer()
        user_names = load_user_names()
        for (x, y, w, h) in faces:
            nbr_predicted, coord = recognizer.predict(gray[y:y+h, x:x+w])
            confidence_percentage = 100 * (1 - (coord / 150))
            if confidence_percentage > 85:
                name = user_names.get(str(nbr_predicted), "Unknown")
            else:
                name = "Unknown"
            cv2.rectangle(image, (x-20, y-20), (x+w+20, y+h+20), (225, 0, 0), 2)
            cv2.putText(image, f"{name} ({confidence_percentage:.1f}%)", (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        _, img_encoded = cv2.imencode('.jpg', image)
        return img_encoded.tobytes()
    except Exception as e:
        print(f"Ошибка в recognize_faces: {e}")
        return None

@bot.message_handler(func=lambda message: message.text == "Распознать пользователя по видео")
def process_num_video(message):
    msg = bot.reply_to(message, "Отправьте видео для распознавания:", reply_markup=markup1)
    bot.register_next_step_handler(msg, process_recognition_video)

def recognize_faces_video(image_bytes):
    """Распознает лица в кадре видео с использованием данных из SQL"""
    try:
        # Загружаем модель и имена пользователей из базы данных
        recognizer = load_recognizer()
        user_names = load_user_names()
        
        if recognizer is None:
            print("Модель распознавания не загружена")
            return None

        # Декодируем изображение
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            print("Ошибка: не удалось декодировать изображение")
            return None

        # Обнаруживаем лица
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Если лиц не найдено
        if len(faces) == 0:
            return None

        # Обрабатываем каждое найденное лицо
        for (x, y, w, h) in faces:
            nbr_predicted, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            confidence_percentage = 100 * (1 - confidence / 150)  # Нормализация уверенности
            
            # Определяем имя пользователя
            if confidence_percentage > 70:  # Порог уверенности 70%
                name = user_names.get(str(nbr_predicted), "Unknown")
            else:
                name = "Unknown"
                confidence_percentage = 0  # Для неизвестных лиц

            # Рисуем прямоугольник и подпись
            cv2.rectangle(image, (x-20, y-20), (x+w+20, y+h+20), (225, 0, 0), 2)
            
            # Используем PIL для корректного отображения текста
            from PIL import Image, ImageDraw, ImageFont
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((x, y+h+10), f"{name} ({confidence_percentage:.1f}%)", 
                      font=font, fill=(0, 255, 0))
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Возвращаем обработанный кадр
        _, img_encoded = cv2.imencode('.jpg', image)
        return img_encoded.tobytes()

    except Exception as e:
        print(f"Ошибка в recognize_faces_video: {e}")
        return None

def process_recognition_video(message):
    global current_handler
    if message.text == "Отмена":
        cancel_handler(message)
        return
    """Обрабатывает полученное видео"""
    if message.content_type != 'video':
        msg = bot.send_message(message.chat.id, 
                             "Пожалуйста, отправьте видео.", 
                             reply_markup=markup1)
        bot.register_next_step_handler(msg, process_recognition_video)
        return

    try:
        # Скачиваем видео
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем временный файл
        video_path = 'received_video.mp4'
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Открываем видео
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            bot.send_message(message.chat.id, 
                           "Ошибка: не удалось открыть видео.", 
                           reply_markup=markup1)
            return

        # Обрабатываем каждый кадр
        output_frames = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Обрабатываем каждый 5-й кадр для оптимизации
            if frame_count % 5 == 0:
                _, img_encoded = cv2.imencode('.jpg', frame)
                processed_frame_bytes = recognize_faces_video(img_encoded.tobytes())
                
                if processed_frame_bytes:
                    nparr = np.frombuffer(processed_frame_bytes, np.uint8)
                    processed_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    output_frames.append(processed_frame)
                else:
                    output_frames.append(frame)
            
            frame_count += 1

        cap.release()

        # Если лица не обнаружены
        if not any(recognize_faces_video(cv2.imencode('.jpg', frame)[1].tobytes()) for frame in output_frames):
            bot.send_message(message.chat.id,
                           "Лица не обнаружены. Отправьте другое видео.",
                           reply_markup=markup1)
            return

        # Сохраняем результат
        if output_frames:
            height, width, _ = output_frames[0].shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_video_path = 'processed_video.mp4'
            
            out = cv2.VideoWriter(output_video_path, fourcc, 10.0, (width, height))
            for frame in output_frames:
                out.write(frame)
            out.release()

            # Отправляем результат
            with open(output_video_path, 'rb') as video:
                bot.send_video(message.chat.id, video,
                             caption="Видео с распознанными лицами",
                             reply_markup=markup1)
            
            # Удаляем временные файлы
            os.remove(output_video_path)
        else:
            bot.send_message(message.chat.id,
                           "Не удалось обработать видео.",
                           reply_markup=markup1)

    except Exception as e:
        bot.send_message(message.chat.id,
                       f"Произошла ошибка: {str(e)}",
                       reply_markup=markup1)
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
    current_handler = None 

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    bot.polling()