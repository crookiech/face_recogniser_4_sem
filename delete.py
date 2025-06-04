from psycopg2 import sql
import data

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
