#!/usr/bin/env python3
"""
Миграция: добавление user_id в таблицу analyses
"""

import ydb
import os

# YDB connection parameters
YDB_ENDPOINT = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
YDB_DATABASE = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')

def main():
    print("🔧 Миграция: добавление user_id в таблицу analyses")
    print(f"Endpoint: {YDB_ENDPOINT}")
    print(f"Database: {YDB_DATABASE}")

    # Initialize YDB driver
    driver_config = ydb.DriverConfig(
        endpoint=YDB_ENDPOINT,
        database=YDB_DATABASE,
        credentials=ydb.iam.MetadataUrlCredentials()
    )

    driver = ydb.Driver(driver_config)

    try:
        driver.wait(fail_fast=True, timeout=5)
        print("✅ Подключено к YDB")

        # Создаем сессию
        session = driver.table_client.session().create()

        try:
            # YDB не поддерживает ALTER TABLE ADD COLUMN напрямую
            # Нужно пересоздать таблицу с новой структурой

            print("\n⚠️  ВНИМАНИЕ: YDB не поддерживает ALTER TABLE ADD COLUMN")
            print("Нужно пересоздать таблицу analyses с новой структурой")
            print("\nВарианты:")
            print("1. Пересоздать таблицу (ПОТЕРЯЕМ ВСЕ ДАННЫЕ)")
            print("2. Создать новую таблицу analyses_v2 и мигрировать данные")
            print("3. Обновить код для сохранения user_id при создании analyses")

            print("\n✅ Рекомендация: вариант 3")
            print("   - Обновляем код в analysis_orchestrator.py")
            print("   - Добавляем user_id при создании новых analyses")
            print("   - Старые данные останутся с NULL user_id")

        finally:
            session.delete()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.stop()

if __name__ == '__main__':
    main()
