#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в YDB
"""

import ydb
import sqlite3
import subprocess
from datetime import datetime

# YDB connection parameters
YDB_ENDPOINT = "grpcs://ydb.serverless.yandexcloud.net:2135"
YDB_DATABASE = "/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e"
SQLITE_DB = "wordoorio-from-s3.db"


def get_iam_token():
    """Получить IAM токен из yc CLI"""
    try:
        result = subprocess.run(['yc', 'iam', 'create-token'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Ошибка получения IAM токена: {e}")
        return None


def parse_timestamp(dt_string):
    """Преобразовать ISO строку в timestamp (микросекунды)"""
    if not dt_string:
        return None
    try:
        dt = datetime.fromisoformat(dt_string)
        return int(dt.timestamp() * 1000000)  # Микросекунды
    except:
        return None


def migrate_users(sqlite_conn, ydb_pool):
    """Миграция таблицы users"""
    print("\n📊 Миграция users...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO users (id, telegram_id, first_name, last_name, username, photo_url, auth_date, created_at, last_login_at)
            VALUES ($id, $telegram_id, $first_name, $last_name, $username, $photo_url, $auth_date, $created_at, $last_login_at)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$telegram_id': row[1],
                    '$first_name': row[2],
                    '$last_name': row[3],
                    '$username': row[4],
                    '$photo_url': row[5],
                    '$auth_date': row[6],
                    '$created_at': row[7],
                    '$last_login_at': row[8]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_dictionary_words(sqlite_conn, ydb_pool):
    """Миграция таблицы dictionary_words"""
    print("\n📊 Миграция dictionary_words...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM dictionary_words")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO dictionary_words (id, user_id, lemma, type, status, added_at, last_reviewed_at, review_count, correct_streak, rating, last_rating_change)
            VALUES ($id, $user_id, $lemma, $type, $status, $added_at, $last_reviewed_at, $review_count, $correct_streak, $rating, $last_rating_change)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$user_id': row[1],
                    '$lemma': row[2],
                    '$type': row[3],
                    '$status': row[4],
                    '$added_at': row[5],
                    '$last_reviewed_at': row[6],
                    '$review_count': row[7] or 0,
                    '$correct_streak': row[8] or 0,
                    '$rating': row[9] or 0,
                    '$last_rating_change': row[10]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_dictionary_translations(sqlite_conn, ydb_pool):
    """Миграция таблицы dictionary_translations"""
    print("\n📊 Миграция dictionary_translations...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM dictionary_translations")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
            VALUES ($id, $word_id, $translation, $source_session_id, $added_at)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$word_id': row[1],
                    '$translation': row[2],
                    '$source_session_id': row[3],
                    '$added_at': row[4]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_dictionary_examples(sqlite_conn, ydb_pool):
    """Миграция таблицы dictionary_examples"""
    print("\n📊 Миграция dictionary_examples...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM dictionary_examples")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO dictionary_examples (id, word_id, original_form, context, session_id, added_at)
            VALUES ($id, $word_id, $original_form, $context, $session_id, $added_at)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$word_id': row[1],
                    '$original_form': row[2],
                    '$context': row[3],
                    '$session_id': row[4],
                    '$added_at': row[5]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_analyses(sqlite_conn, ydb_pool):
    """Миграция таблицы analyses"""
    print("\n📊 Миграция analyses...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM analyses")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO analyses (id, original_text, analysis_date, total_highlights, total_words, session_id, ip_address)
            VALUES ($id, $original_text, $analysis_date, $total_highlights, $total_words, $session_id, $ip_address)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$original_text': row[1],
                    '$analysis_date': parse_timestamp(row[2]),
                    '$total_highlights': row[3] or 0,
                    '$total_words': row[4] or 0,
                    '$session_id': row[5],
                    '$ip_address': row[6]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_highlights(sqlite_conn, ydb_pool):
    """Миграция таблицы highlights"""
    print("\n📊 Миграция highlights...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM highlights")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO highlights (id, analysis_id, highlight_word, context, highlight_translation, dictionary_meanings)
            VALUES ($id, $analysis_id, $highlight_word, $context, $highlight_translation, $dictionary_meanings)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$analysis_id': row[1],
                    '$highlight_word': row[2],
                    '$context': row[3],
                    '$highlight_translation': row[4],
                    '$dictionary_meanings': row[5]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_user_training_state(sqlite_conn, ydb_pool):
    """Миграция таблицы user_training_state"""
    print("\n📊 Миграция user_training_state...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM user_training_state")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO user_training_state (user_id, last_selection_position, last_training_at)
            VALUES ($user_id, $last_selection_position, $last_training_at)
            """
            session.transaction().execute(
                query,
                {
                    '$user_id': row[0],
                    '$last_selection_position': row[1] or 0,
                    '$last_training_at': row[2]
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def migrate_word_test_statistics(sqlite_conn, ydb_pool):
    """Миграция таблицы word_test_statistics"""
    print("\n📊 Миграция word_test_statistics...")

    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM word_test_statistics")
    rows = cursor.fetchall()

    if not rows:
        print("  Нет данных для миграции")
        return

    def callee(session):
        for row in rows:
            query = """
            UPSERT INTO word_test_statistics (id, user_id, word_id, total_tests, correct_answers, wrong_answers, last_test_at, last_result)
            VALUES ($id, $user_id, $word_id, $total_tests, $correct_answers, $wrong_answers, $last_test_at, $last_result)
            """
            session.transaction().execute(
                query,
                {
                    '$id': row[0],
                    '$user_id': row[1],
                    '$word_id': row[2],
                    '$total_tests': row[3] or 0,
                    '$correct_answers': row[4] or 0,
                    '$wrong_answers': row[5] or 0,
                    '$last_test_at': row[6],
                    '$last_result': bool(row[7]) if row[7] is not None else None
                },
                commit_tx=True
            )

    ydb_pool.retry_operation_sync(callee)
    print(f"  ✅ Мигрировано записей: {len(rows)}")


def main():
    print("=" * 60)
    print("🚀 МИГРАЦИЯ ДАННЫХ ИЗ SQLITE В YDB")
    print("=" * 60)

    # Подключаемся к SQLite
    print(f"\n📂 Открываем SQLite базу: {SQLITE_DB}")
    sqlite_conn = sqlite3.connect(SQLITE_DB)

    # Подключаемся к YDB
    print(f"\n🔧 Подключаемся к YDB...")
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
        print("✅ Подключение к YDB установлено")

        # Создаем пул сессий
        pool = ydb.SessionPool(driver)

        # Миграция данных
        migrate_users(sqlite_conn, pool)
        migrate_dictionary_words(sqlite_conn, pool)
        migrate_dictionary_translations(sqlite_conn, pool)
        migrate_dictionary_examples(sqlite_conn, pool)
        migrate_analyses(sqlite_conn, pool)
        migrate_highlights(sqlite_conn, pool)
        migrate_user_training_state(sqlite_conn, pool)
        migrate_word_test_statistics(sqlite_conn, pool)

        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_conn.close()
        driver.stop()


if __name__ == "__main__":
    main()
