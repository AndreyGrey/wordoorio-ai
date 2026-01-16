#!/usr/bin/env python3
"""
Скрипт для удаления всех слов конкретного пользователя
"""

import sys
from database import WordoorioDatabase
from core.dictionary_manager import DictionaryManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_all_user_words(username: str):
    """Удалить все слова пользователя по username"""
    db = WordoorioDatabase()

    # Найти user_id по username
    query = """
    DECLARE $username AS Utf8?;

    SELECT id, username FROM users
    WHERE username = $username
    """

    result = db._fetch_one(query, {'$username': username})

    if not result:
        logger.error(f"Пользователь '{username}' не найден")
        return

    user_id = result['id']
    logger.info(f"Найден пользователь '{username}' (user_id={user_id})")

    # Получить все слова пользователя
    get_words_query = """
    DECLARE $user_id AS Uint64?;

    SELECT id, lemma FROM dictionary_words
    WHERE user_id = $user_id
    """

    words = db._fetch_all(get_words_query, {'$user_id': user_id})
    logger.info(f"Найдено {len(words)} слов для удаления")

    if not words:
        logger.info("Слов не найдено, нечего удалять")
        return

    # Создать DictionaryManager для корректного удаления с каскадом
    dict_manager = DictionaryManager()

    # Удалить каждое слово (с автоматическим удалением highlights)
    deleted_count = 0
    for word in words:
        word_id = word['id']
        lemma = word['lemma']
        try:
            dict_manager.delete_word(lemma, user_id)
            deleted_count += 1
            logger.info(f"Удалено: {lemma} (id={word_id})")
        except Exception as e:
            logger.error(f"Ошибка при удалении '{lemma}': {e}")

    logger.info(f"✅ Удалено {deleted_count} из {len(words)} слов пользователя '{username}'")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python delete_user_words.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    delete_all_user_words(username)
