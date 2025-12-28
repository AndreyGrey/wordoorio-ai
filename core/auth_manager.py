#!/usr/bin/env python3
"""
🔐 Auth Manager
Управление авторизацией через Telegram Login Widget

@version 2.0.0 (YDB)
"""

import ydb
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, db_path: str = "wordoorio.db"):
        """
        Инициализация Auth Manager

        Args:
            db_path: Не используется для YDB, сохранено для совместимости API
        """
        # YDB connection parameters from environment
        self.endpoint = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
        self.database = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')

        # For API compatibility
        self.db_path = db_path

        # Получаем BOT_TOKEN из .env для проверки подписи Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')

        # Initialize YDB driver
        self._init_driver()

        logger.info(f"[AUTH] YDB connected: {self.endpoint}")

    def _init_driver(self):
        """Initialize YDB driver with credentials"""
        # Use MetadataUrlCredentials for serverless containers
        driver_config = ydb.DriverConfig(
            endpoint=self.endpoint,
            database=self.database,
            credentials=ydb.iam.MetadataUrlCredentials()
        )

        self.driver = ydb.Driver(driver_config)
        self.driver.wait(fail_fast=True, timeout=5)

        # Create session pool for efficient connection reuse
        self.pool = ydb.SessionPool(self.driver)

    def _execute_query(self, query: str, parameters: Dict = None):
        """
        Execute YQL query with automatic retries

        Args:
            query: YQL query string
            parameters: Query parameters as dict

        Returns:
            Query result
        """
        def callee(session):
            return session.transaction().execute(
                query,
                parameters or {},
                commit_tx=True
            )

        return self.pool.retry_operation_sync(callee)

    def _fetch_one(self, query: str, parameters: Dict = None) -> Optional[Dict]:
        """Execute query and return first row as dict"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return None

        row = result[0].rows[0]
        columns = [col.name for col in result[0].columns]
        return {col: getattr(row, col) for col in columns}

    def _get_next_id(self, table_name: str) -> int:
        """
        Get next auto-increment ID for a table
        YDB doesn't have auto-increment, so we simulate it
        """
        query = f"SELECT MAX(id) AS max_id FROM {table_name}"
        result = self._fetch_one(query)

        if not result or result['max_id'] is None:
            return 1

        return result['max_id'] + 1

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

        # Проверяем существует ли пользователь
        check_query = """
        SELECT id FROM users WHERE telegram_id = $telegram_id
        """
        existing = self._fetch_one(check_query, {'$telegram_id': telegram_id})

        if existing:
            # Обновляем данные пользователя
            user_id = existing['id']
            update_query = """
            UPDATE users SET
                first_name = $first_name,
                last_name = $last_name,
                username = $username,
                photo_url = $photo_url,
                auth_date = $auth_date,
                last_login_at = $last_login_at
            WHERE id = $id
            """
            self._execute_query(update_query, {
                '$first_name': telegram_data.get('first_name'),
                '$last_name': telegram_data.get('last_name'),
                '$username': telegram_data.get('username'),
                '$photo_url': telegram_data.get('photo_url'),
                '$auth_date': telegram_data.get('auth_date'),
                '$last_login_at': now,
                '$id': user_id
            })
            logger.info(f"[AUTH] Пользователь {telegram_id} обновлен")
        else:
            # Создаем нового пользователя
            user_id = self._get_next_id('users')
            insert_query = """
            UPSERT INTO users (id, telegram_id, first_name, last_name, username, photo_url, auth_date, created_at, last_login_at)
            VALUES ($id, $telegram_id, $first_name, $last_name, $username, $photo_url, $auth_date, $created_at, $last_login_at)
            """
            self._execute_query(insert_query, {
                '$id': user_id,
                '$telegram_id': telegram_id,
                '$first_name': telegram_data.get('first_name'),
                '$last_name': telegram_data.get('last_name'),
                '$username': telegram_data.get('username'),
                '$photo_url': telegram_data.get('photo_url'),
                '$auth_date': telegram_data.get('auth_date'),
                '$created_at': now,
                '$last_login_at': now
            })
            logger.info(f"[AUTH] Создан новый пользователь {telegram_id} с id={user_id}")

        return user_id

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Получает данные пользователя по user_id

        Args:
            user_id: ID пользователя в нашей базе

        Returns:
            Словарь с данными пользователя или None
        """
        query = """
        SELECT * FROM users WHERE id = $id
        """
        return self._fetch_one(query, {'$id': user_id})

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """
        Получает данные пользователя по telegram_id

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Словарь с данными пользователя или None
        """
        query = """
        SELECT * FROM users WHERE telegram_id = $telegram_id
        """
        return self._fetch_one(query, {'$telegram_id': telegram_id})

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'driver'):
            self.driver.stop()


# Тесты для проверки
if __name__ == "__main__":
    print("🧪 Тестируем AuthManager (YDB)...\n")

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
