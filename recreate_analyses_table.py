#!/usr/bin/env python3
"""
Пересоздание таблицы analyses с полем user_id
ВНИМАНИЕ: Удалит все существующие данные!
"""

import ydb
import os
import sys
from dotenv import load_dotenv

load_dotenv()

YDB_ENDPOINT = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
YDB_DATABASE = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')
YANDEX_IAM_TOKEN = os.getenv('YANDEX_IAM_TOKEN')

def main():
    print("🔧 Пересоздание таблицы analyses с user_id")
    print(f"Endpoint: {YDB_ENDPOINT}")
    print(f"Database: {YDB_DATABASE}")
    print("\n⚠️  ВНИМАНИЕ: Все данные в таблице analyses будут удалены!")

    # Allow --force flag to skip confirmation
    if '--force' not in sys.argv:
        confirm = input("Продолжить? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Отменено")
            return
    else:
        print("--force flag detected, proceeding without confirmation...")

    # Use IAM token for local development, metadata service for production
    if YANDEX_IAM_TOKEN:
        credentials = ydb.AccessTokenCredentials(YANDEX_IAM_TOKEN)
    else:
        credentials = ydb.iam.MetadataUrlCredentials()

    driver_config = ydb.DriverConfig(
        endpoint=YDB_ENDPOINT,
        database=YDB_DATABASE,
        credentials=credentials
    )

    driver = ydb.Driver(driver_config)

    try:
        driver.wait(fail_fast=True, timeout=5)
        print("✅ Подключено к YDB")

        session = driver.table_client.session().create()

        try:
            # 1. Удаляем старую таблицу
            print("\n1️⃣  Удаляем таблицу analyses...")
            drop_query = f"DROP TABLE `{YDB_DATABASE}/analyses`"
            session.execute_scheme(drop_query)
            print("✅ Таблица удалена")

            # 2. Создаем новую таблицу с user_id
            print("\n2️⃣  Создаем новую таблицу analyses с user_id...")
            create_query = """
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
            """
            session.execute_scheme(create_query)
            print("✅ Таблица создана")

            # 3. Также пересоздаем highlights чтобы добавить user_id
            print("\n3️⃣  Удаляем таблицу highlights...")
            drop_highlights = f"DROP TABLE `{YDB_DATABASE}/highlights`"
            session.execute_scheme(drop_highlights)
            print("✅ Таблица удалена")

            print("\n4️⃣  Создаем новую таблицу highlights...")
            create_highlights = """
            CREATE TABLE highlights (
                id Uint64,
                analysis_id Uint64,
                highlight_word Utf8,
                context Utf8,
                highlight_translation Utf8,
                dictionary_meanings Utf8,
                PRIMARY KEY (id),
                INDEX idx_analysis_id GLOBAL ON (analysis_id),
                INDEX idx_highlight_word GLOBAL ON (highlight_word)
            )
            """
            session.execute_scheme(create_highlights)
            print("✅ Таблица создана")

            print("\n✅ Миграция завершена!")
            print("\nТеперь нужно обновить код:")
            print("1. core/analysis_orchestrator.py - передавать user_id при сохранении analysis")
            print("2. web_app.py - добавить API endpoint для получения хайлайтов пользователя")

        finally:
            session.delete()

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.stop()

if __name__ == '__main__':
    main()
