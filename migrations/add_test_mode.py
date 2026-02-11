#!/usr/bin/env python3
"""
Миграция: добавление поля test_mode в таблицу tests

test_mode:
  1 = EN→RU (показываем английское слово, выбираем русский перевод)
  2 = RU→EN (показываем русский перевод, выбираем английское слово)
"""

import ydb
import subprocess

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


def run_migration(session):
    """Добавить колонку test_mode в таблицу tests"""

    query = """
    ALTER TABLE tests ADD COLUMN test_mode Uint32
    """

    try:
        print("Добавляем колонку test_mode в таблицу tests...")
        session.execute_scheme(query)
        print("✅ Колонка test_mode добавлена")
    except Exception as e:
        if "already exists" in str(e).lower() or "Member not found" in str(e):
            print("ℹ️ Колонка test_mode уже существует")
        else:
            print(f"❌ Ошибка: {e}")
            raise


def main():
    print("🔧 Миграция: добавление test_mode в таблицу tests")
    print(f"Endpoint: {YDB_ENDPOINT}")
    print(f"Database: {YDB_DATABASE}")

    iam_token = get_iam_token()
    if not iam_token:
        print("❌ Не удалось получить IAM токен")
        return

    driver_config = ydb.DriverConfig(
        endpoint=YDB_ENDPOINT,
        database=YDB_DATABASE,
        credentials=ydb.AccessTokenCredentials(iam_token)
    )

    driver = ydb.Driver(driver_config)

    try:
        driver.wait(fail_fast=True, timeout=5)
        print("✅ Подключение установлено")

        with ydb.SessionPool(driver) as pool:
            pool.retry_operation_sync(lambda session: run_migration(session))

        print("\n✅ Миграция завершена!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.stop()


if __name__ == "__main__":
    main()
