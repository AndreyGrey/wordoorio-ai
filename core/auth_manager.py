#!/usr/bin/env python3
"""
🔐 Auth Manager
Управление авторизацией через Telegram Login Widget
"""

import sqlite3
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Optional
import os


class AuthManager:
    def __init__(self, db_path: str = "wordoorio.db"):
        self.db_path = db_path
        # Получаем BOT_TOKEN из .env для проверки подписи Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')

    def verify_telegram_auth(self, auth_data: Dict) -> bool:
        """
        Проверяет подпись данных от Telegram Login Widget

        Args:
            auth_data: Данные от Telegram (id, first_name, last_name, username, photo_url, auth_date, hash)

        Returns:
            True если данные валидны
        """
        # DEV MODE: пропускаем проверку подписи для разработки
        received_hash = auth_data.get('hash')
        if received_hash == 'dev_mode_no_verification':
            print("🔧 DEV MODE: пропускаем проверку подписи Telegram")
            return True

        if not self.bot_token:
            print("⚠️  BOT_TOKEN не найден в .env")
            return False

        # Извлекаем hash
        if not received_hash:
            return False

        # Создаем строку для проверки (все поля кроме hash, отсортированные по алфавиту)
        check_fields = {k: v for k, v in auth_data.items() if k != 'hash' and v is not None}
        check_string = '\n'.join(f'{k}={v}' for k, v in sorted(check_fields.items()))

        # Вычисляем secret_key = SHA256(bot_token)
        secret_key = hashlib.sha256(self.bot_token.encode()).digest()

        # Вычисляем HMAC-SHA256
        calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

        # Сравниваем хеши
        return hmac.compare_digest(calculated_hash, received_hash)

    def create_or_update_user(self, telegram_data: Dict) -> Optional[int]:
        """
        Создает или обновляет пользователя в базе

        Args:
            telegram_data: Данные от Telegram (id, first_name, last_name, username, photo_url, auth_date)

        Returns:
            user_id в нашей базе или None при ошибке
        """
        telegram_id = telegram_data.get('id')
        if not telegram_id:
            return None

        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Проверяем существует ли пользователь
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            existing = cursor.fetchone()

            if existing:
                # Обновляем данные пользователя
                user_id = existing[0]
                cursor.execute("""
                    UPDATE users SET
                        first_name = ?,
                        last_name = ?,
                        username = ?,
                        photo_url = ?,
                        auth_date = ?,
                        last_login_at = ?
                    WHERE id = ?
                """, (
                    telegram_data.get('first_name'),
                    telegram_data.get('last_name'),
                    telegram_data.get('username'),
                    telegram_data.get('photo_url'),
                    telegram_data.get('auth_date'),
                    now,
                    user_id
                ))
                print(f"✅ Пользователь {telegram_id} обновлен")
            else:
                # Создаем нового пользователя
                cursor.execute("""
                    INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, auth_date, created_at, last_login_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    telegram_id,
                    telegram_data.get('first_name'),
                    telegram_data.get('last_name'),
                    telegram_data.get('username'),
                    telegram_data.get('photo_url'),
                    telegram_data.get('auth_date'),
                    now,
                    now
                ))
                user_id = cursor.lastrowid
                print(f"✅ Создан новый пользователь {telegram_id} с id={user_id}")

            conn.commit()
            return user_id

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Получает данные пользователя по user_id

        Args:
            user_id: ID пользователя в нашей базе

        Returns:
            Словарь с данными пользователя или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """
        Получает данные пользователя по telegram_id

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Словарь с данными пользователя или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None


# Тесты для проверки
if __name__ == "__main__":
    print("🧪 Тестируем AuthManager...\n")

    auth = AuthManager()

    # Тестовые данные (без реальной подписи)
    test_data = {
        'id': 123456789,
        'first_name': 'Test',
        'last_name': 'User',
        'username': 'testuser',
        'photo_url': 'https://t.me/i/userpic/320/testuser.jpg',
        'auth_date': 1234567890
    }

    print("📝 Создаем тестового пользователя...")
    user_id = auth.create_or_update_user(test_data)
    print(f"✅ User ID: {user_id}\n")

    print("🔍 Получаем данные пользователя...")
    user = auth.get_user_by_id(user_id)
    print(f"✅ User data: {user}\n")

    print("✅ Тесты завершены")
