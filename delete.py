import os
import psycopg2
from psycopg2 import sql
import data

path = os.path.dirname(os.path.abspath(__file__))
dataSet_dir = os.path.join(path, 'dataSet')  # Папка для данных пользователей

def delete_user(name):
    try:
        conn = data.get_db_connection()
        with conn.cursor() as cur:
            # Получаем ID пользователя
            cur.execute(
                sql.SQL("SELECT user_id FROM users WHERE name = %s;"),
                (name,)
            )
            user_row = cur.fetchone()
            if not user_row:
                return False, f"Пользователь с именем '{name}' не найден."
            
            user_id = user_row[0]
            
            # Удаляем пользователя
            cur.execute(
                sql.SQL("DELETE FROM users WHERE name = %s;"),
                (name,)
            )
            
            # Удаление изображений пользователя
            user_files = [f for f in os.listdir(dataSet_dir) 
                         if f.startswith(f"face-{user_id}.")]
            for file in user_files:
                try:
                    os.remove(os.path.join(dataSet_dir, file))
                except Exception as e:
                    print(f"Ошибка удаления {file}: {e}")
        
        conn.commit()
        return True, f"Пользователь {name} (ID: {user_id}) успешно удалён"
        
    except Exception as e:
        return False, f"Ошибка при удалении пользователя: {e}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python delete.py <имя_пользователя>")
        sys.exit(1)
    
    name = sys.argv[1]
    success, message = delete_user(name)
    if success:
        print(message)
    else:
        print(f"Ошибка: {message}")
        sys.exit(1)