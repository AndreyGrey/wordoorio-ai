#!/usr/bin/env python3
"""
Скрипт для просмотра всех пользователей
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_all_users():
    """Показать всех пользователей"""
    db = WordoorioDatabase()

    query = """
    SELECT id, username, telegram_id, created_at FROM users
    """

    users = db._fetch_all(query, {})

    if not users:
        logger.info("Пользователей не найдено")
        return

    logger.info(f"Найдено пользователей: {len(users)}")
    print("\n" + "="*80)
    for user in users:
        user_id = user.get('id')
        username = user.get('username')
        telegram_id = user.get('telegram_id')
        created_at = user.get('created_at')

        # Подсчитать слова пользователя
        count_query = """
        DECLARE $user_id AS Uint64?;

        SELECT COUNT(*) as word_count FROM dictionary_words
        WHERE user_id = $user_id
        """
        count_result = db._fetch_one(count_query, {'$user_id': user_id})
        word_count = count_result['word_count'] if count_result else 0

        print(f"User ID: {user_id}")
        print(f"Username: {username}")
        print(f"Telegram ID: {telegram_id}")
        print(f"Created: {created_at}")
        print(f"Words in dictionary: {word_count}")
        print("-"*80)


if __name__ == '__main__':
    list_all_users()
