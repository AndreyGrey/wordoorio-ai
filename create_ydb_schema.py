#!/usr/bin/env python3
"""
Скрипт для создания схемы таблиц в YDB
"""

import ydb
import os
import subprocess

# YDB connection parameters
YDB_ENDPOINT = "grpcs://ydb.serverless.yandexcloud.net:2135"
YDB_DATABASE = "/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e"

def get_iam_token():
    """Получить IAM токен из yc CLI"""
    try:
        result = subprocess.run(['yc', 'iam', 'create-token'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Ошибка получения IAM токена: {e}")
        return None

def create_tables(pool, session):
    """Создание всех таблиц"""

    tables = [
        # 1. Таблица пользователей
        """
        CREATE TABLE users (
            id Uint64,
            telegram_id Uint64,
            first_name Utf8,
            last_name Utf8,
            username Utf8,
            photo_url Utf8,
            auth_date Uint64,
            created_at Utf8,
            last_login_at Utf8,
            PRIMARY KEY (id),
            INDEX idx_telegram_id GLOBAL ON (telegram_id)
        )
        """,

        # 2. Таблица словарных слов
        """
        CREATE TABLE dictionary_words (
            id Uint64,
            user_id Uint64,
            lemma Utf8,
            type Utf8,
            status Utf8,
            added_at Utf8,
            last_reviewed_at Utf8,
            review_count Uint32,
            correct_streak Uint32,
            rating Uint32,
            last_rating_change Utf8,
            PRIMARY KEY (id),
            INDEX idx_user_lemma GLOBAL ON (user_id, lemma),
            INDEX idx_lemma GLOBAL ON (lemma),
            INDEX idx_status GLOBAL ON (status),
            INDEX idx_rating GLOBAL ON (rating)
        )
        """,

        # 3. Переводы слов
        """
        CREATE TABLE dictionary_translations (
            id Uint64,
            word_id Uint64,
            translation Utf8,
            source_session_id Utf8,
            added_at Utf8,
            PRIMARY KEY (id),
            INDEX idx_word_id GLOBAL ON (word_id)
        )
        """,

        # 4. Примеры использования слов
        """
        CREATE TABLE dictionary_examples (
            id Uint64,
            word_id Uint64,
            original_form Utf8,
            context Utf8,
            session_id Utf8,
            added_at Utf8,
            PRIMARY KEY (id),
            INDEX idx_word_id GLOBAL ON (word_id)
        )
        """,

        # 5. Анализы текста
        """
        CREATE TABLE analyses (
            id Uint64,
            user_id Uint64,
            original_text Utf8,
            analysis_date Timestamp,
            total_highlights Uint32,
            total_words Uint32,
            session_id Utf8,
            ip_address Utf8,
            PRIMARY KEY (id),
            INDEX idx_user_id GLOBAL ON (user_id),
            INDEX idx_analysis_date GLOBAL ON (analysis_date),
            INDEX idx_session_id GLOBAL ON (session_id)
        )
        """,

        # 6. Хайлайты (связь анализов и слов из словаря)
        """
        CREATE TABLE highlights (
            id Uint64,
            analysis_id Uint64,
            word_id Uint64,
            position Uint32,
            PRIMARY KEY (id),
            INDEX idx_analysis_id GLOBAL ON (analysis_id),
            INDEX idx_word_id GLOBAL ON (word_id)
        )
        """,

        # 7. Состояние тренировки пользователя
        """
        CREATE TABLE user_training_state (
            user_id Uint64,
            last_selection_position Uint32,
            last_training_at Utf8,
            PRIMARY KEY (user_id)
        )
        """,

        # 8. Тесты
        """
        CREATE TABLE tests (
            id Uint64,
            user_id Uint64,
            word_id Uint64,
            word Utf8,
            correct_translation Utf8,
            wrong_option_1 Utf8,
            wrong_option_2 Utf8,
            wrong_option_3 Utf8,
            created_at Utf8,
            PRIMARY KEY (id),
            INDEX idx_user_id GLOBAL ON (user_id)
        )
        """,

        # 9. Статистика тестирования слов
        """
        CREATE TABLE word_test_statistics (
            id Uint64,
            user_id Uint64,
            word_id Uint64,
            total_tests Uint32,
            correct_answers Uint32,
            wrong_answers Uint32,
            last_test_at Utf8,
            last_result Bool,
            PRIMARY KEY (id),
            INDEX idx_user_word GLOBAL ON (user_id, word_id)
        )
        """
    ]

    table_names = [
        "users",
        "dictionary_words",
        "dictionary_translations",
        "dictionary_examples",
        "analyses",
        "highlights",
        "user_training_state",
        "tests",
        "word_test_statistics"
    ]

    for i, query in enumerate(tables):
        try:
            print(f"Создаем таблицу {table_names[i]}...")
            session.execute_scheme(query)
            print(f"✅ Таблица {table_names[i]} создана")
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы {table_names[i]}: {e}")


def main():
    print("🔧 Подключаемся к YDB...")
    print(f"Endpoint: {YDB_ENDPOINT}")
    print(f"Database: {YDB_DATABASE}")

    # Получаем IAM токен
    print("🔑 Получаем IAM токен...")
    iam_token = get_iam_token()
    if not iam_token:
        print("❌ Не удалось получить IAM токен")
        return

    # Создаем драйвер для подключения к YDB
    driver_config = ydb.DriverConfig(
        endpoint=YDB_ENDPOINT,
        database=YDB_DATABASE,
        credentials=ydb.AccessTokenCredentials(iam_token)
    )

    driver = ydb.Driver(driver_config)

    try:
        driver.wait(fail_fast=True, timeout=5)
        print("✅ Подключение установлено")

        # Создаем сессию
        with ydb.SessionPool(driver) as pool:
            def callee(session):
                create_tables(pool, session)

            pool.retry_operation_sync(callee)

        print("\n✅ Все таблицы успешно созданы!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.stop()


if __name__ == "__main__":
    main()
