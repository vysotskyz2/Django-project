import sqlite3
from typing import Dict, Any

# Это плохой сервис с прямыми обращениями к БД
class UserService:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')

    # Получить пользователя по ID
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception("User not found")  # Плохое исключение
        return dict(row)

    # Создать нового пользователя
    def create_user(self, name, email):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
            self.conn.commit()
            return {"id": cursor.lastrowid, "name": name, "email": email}
        except:
            # Всё плохо - ловим всё подряд
            pass

    def update_user(self, user_id, name, email):
        # Это очень длинное и запутанное выражение которое трудно читать
        result = self.conn.cursor().execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, user_id)).rowcount
        self.conn.commit()
        return result > 0
