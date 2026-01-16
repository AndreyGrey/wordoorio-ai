#!/usr/bin/env python3
"""
Скрипт для проверки содержимого всех таблиц
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_content():
    """Проверить содержимое всех основных таблиц"""
    db = WordoorioDatabase()

    tables = {
        'users': 'SELECT COUNT(*) as count FROM users',
        'dictionary_words': 'SELECT COUNT(*) as count FROM dictionary_words',
        'dictionary_translations': 'SELECT COUNT(*) as count FROM dictionary_translations',
        'dictionary_examples': 'SELECT COUNT(*) as count FROM dictionary_examples',
        'analyses': 'SELECT COUNT(*) as count FROM analyses',
        'highlights': 'SELECT COUNT(*) as count FROM highlights',
    }

    print("\n" + "="*80)
    print("DATABASE CONTENT")
    print("="*80)

    for table_name, query in tables.items():
        try:
            result = db._fetch_one(query, {})
            count = result['count'] if result else 0
            print(f"{table_name:30} {count:>10} записей")
        except Exception as e:
            print(f"{table_name:30} ERROR: {e}")

    print("="*80)

    # Показать несколько слов, если они есть
    try:
        words_query = """
        SELECT id, lemma, user_id, status, added_at
        FROM dictionary_words
        LIMIT 10
        """
        words = db._fetch_all(words_query, {})
        if words:
            print("\nПримеры слов в словаре:")
            print("-"*80)
            for word in words:
                print(f"  ID: {word['id']}, Lemma: {word['lemma']}, User ID: {word.get('user_id', 'NULL')}, Status: {word.get('status', 'N/A')}")
            print("-"*80)
    except Exception as e:
        print(f"Ошибка получения слов: {e}")


if __name__ == '__main__':
    check_database_content()
