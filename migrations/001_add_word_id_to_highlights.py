#!/usr/bin/env python3
"""
Migration: Add word_id to highlights table and migrate existing data

Цель: Убрать дублирование данных между dictionary_words и highlights.
Сделать highlights ссылкой на dictionary_words через word_id.

Шаги:
1. Создать временную таблицу highlights_new с новой структурой
2. Для каждого существующего highlight:
   - Найти или создать соответствующее слово в dictionary_words
   - Скопировать highlight с word_id в highlights_new
3. Удалить старую таблицу highlights
4. Переименовать highlights_new → highlights
"""

import ydb
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _typed_params(params: Dict) -> Dict[str, ydb.TypedValue]:
    """Конвертирует параметры в TypedValue для YDB"""
    typed = {}
    for key, value in params.items():
        if isinstance(value, bool):
            typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Bool))
        elif isinstance(value, str):
            typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Utf8))
        elif isinstance(value, int):
            if 'id' in key.lower():
                typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Uint64))
            else:
                typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Uint32))
        elif value is None:
            typed[key] = ydb.TypedValue(None, ydb.OptionalType(ydb.PrimitiveType.Uint64))
        else:
            typed[key] = value
    return typed


class HighlightsMigration:
    def __init__(self):
        self.endpoint = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
        self.database = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')

        iam_token = os.getenv('YANDEX_IAM_TOKEN')
        if iam_token:
            credentials = ydb.AccessTokenCredentials(iam_token)
        else:
            credentials = ydb.iam.MetadataUrlCredentials()

        driver_config = ydb.DriverConfig(
            endpoint=self.endpoint,
            database=self.database,
            credentials=credentials
        )

        self.driver = ydb.Driver(driver_config)
        self.driver.wait(fail_fast=True, timeout=5)
        self.pool = ydb.QuerySessionPool(self.driver)

        logger.info(f"[MIGRATION] Connected to {self.endpoint}")

    def _execute_query(self, query: str, parameters: Dict = None):
        """Execute YDB query with retry logic"""
        typed_parameters = _typed_params(parameters) if parameters else {}
        return self.pool.execute_with_retries(query, parameters=typed_parameters)

    def _fetch_all(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute query and return all rows as list of dicts"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return []

        columns = [col.name for col in result[0].columns]
        return [
            {col: getattr(row, col) for col in columns}
            for row in result[0].rows
        ]

    def _fetch_one(self, query: str, parameters: Dict = None) -> Optional[Dict]:
        """Execute query and return first row as dict"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return None

        row = result[0].rows[0]
        columns = [col.name for col in result[0].columns]
        return {col: getattr(row, col) for col in columns}

    def _get_next_id(self, table_name: str) -> int:
        """Get next auto-increment ID for a table"""
        query = f"SELECT MAX(id) AS max_id FROM {table_name}"
        result = self._fetch_one(query)

        if not result or result['max_id'] is None:
            return 1

        return result['max_id'] + 1

    def run(self):
        """Выполнить миграцию"""
        logger.info("[MIGRATION] Starting migration...")

        # Сначала проверим, не мигрирована ли уже таблица
        try:
            check_query = """
            SELECT id, analysis_id, word_id, position
            FROM highlights
            LIMIT 1
            """
            self._fetch_all(check_query)
            logger.info("[MIGRATION] ✓ Таблица highlights УЖЕ имеет новую структуру. Миграция не требуется!")
            return
        except Exception as e:
            error_msg = str(e).lower()
            if "word_id" not in error_msg or "not found" not in error_msg:
                # Если ошибка не связана с отсутствием word_id, пробрасываем её
                logger.warning(f"[MIGRATION] Unexpected error checking structure: {e}")
            logger.info("[MIGRATION] Старая структура highlights обнаружена, начинаем миграцию...")

        # Шаг 1: Создать новую таблицу highlights_new
        logger.info("[MIGRATION] Step 1: Creating highlights_new table...")
        self._create_new_table()

        # Шаг 2: Мигрировать данные
        logger.info("[MIGRATION] Step 2: Migrating data...")
        self._migrate_data()

        # Шаг 3: Удалить старую таблицу и переименовать новую
        logger.info("[MIGRATION] Step 3: Replacing old table...")
        self._replace_table()

        logger.info("[MIGRATION] Migration completed successfully!")

    def _create_new_table(self):
        """Создать таблицу highlights_new с новой структурой"""
        create_table_query = """
        CREATE TABLE highlights_new (
            id Uint64,
            analysis_id Uint64,
            word_id Uint64,
            position Uint32,
            PRIMARY KEY (id)
        )
        """
        try:
            self._execute_query(create_table_query)
            logger.info("[MIGRATION] ✓ Table highlights_new created")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("[MIGRATION] ⚠ Table highlights_new already exists, dropping...")
                self._execute_query("DROP TABLE highlights_new")
                self._execute_query(create_table_query)
                logger.info("[MIGRATION] ✓ Table highlights_new recreated")
            else:
                raise

    def _migrate_data(self):
        """Мигрировать данные из старой таблицы в новую"""
        # Сначала проверим, что старая таблица highlights существует и имеет старую структуру
        # Если уже мигрирована (есть только word_id), пропускаем миграцию
        try:
            check_structure_query = """
            SELECT id, analysis_id, word_id
            FROM highlights
            LIMIT 1
            """
            test_result = self._fetch_all(check_structure_query)
            logger.info("[MIGRATION] ⚠ Таблица highlights уже имеет новую структуру (word_id найден). Миграция не требуется.")
            return
        except Exception as e:
            if "word_id" in str(e) and "not found" in str(e).lower():
                logger.info("[MIGRATION] Старая структура highlights обнаружена, продолжаем миграцию...")
            else:
                logger.error(f"[MIGRATION] Ошибка проверки структуры: {e}")
                raise

        # Получить все существующие highlights
        get_highlights_query = """
        SELECT
            h.id,
            h.analysis_id,
            h.highlight_word,
            h.context,
            h.highlight_translation,
            h.dictionary_meanings,
            a.user_id,
            a.session_id
        FROM highlights AS h
        LEFT JOIN analyses AS a ON h.analysis_id = a.id
        """

        old_highlights = self._fetch_all(get_highlights_query)
        logger.info(f"[MIGRATION] Found {len(old_highlights)} highlights to migrate")

        migrated = 0
        skipped = 0

        for idx, highlight in enumerate(old_highlights, 1):
            try:
                # DEBUG: print highlight keys to understand structure
                if idx == 1:
                    logger.info(f"[MIGRATION DEBUG] First highlight keys: {list(highlight.keys())}")
                    logger.info(f"[MIGRATION DEBUG] First highlight: {highlight}")

                highlight_id = highlight.get('id')
                analysis_id = highlight.get('analysis_id')
                lemma = highlight.get('highlight_word')
                context = highlight.get('context')
                translation = highlight.get('highlight_translation')
                user_id = highlight.get('user_id')
                session_id = highlight.get('session_id') or 'migration'

                if not lemma or not translation:
                    logger.warning(f"[MIGRATION] Skipping highlight {highlight_id}: missing lemma or translation")
                    skipped += 1
                    continue

                # Найти или создать слово в dictionary_words
                word_id = self._find_or_create_word(
                    lemma=lemma,
                    translation=translation,
                    context=context,
                    user_id=user_id,
                    session_id=session_id
                )

                # Вставить в highlights_new
                insert_query = """
                DECLARE $id AS Uint64?;
                DECLARE $analysis_id AS Uint64?;
                DECLARE $word_id AS Uint64?;
                DECLARE $position AS Uint32?;

                UPSERT INTO highlights_new (id, analysis_id, word_id, position)
                VALUES ($id, $analysis_id, $word_id, $position)
                """

                self._execute_query(insert_query, {
                    '$id': highlight_id,
                    '$analysis_id': analysis_id,
                    '$word_id': word_id,
                    '$position': idx  # Порядковый номер
                })

                migrated += 1

                if migrated % 10 == 0:
                    logger.info(f"[MIGRATION] Migrated {migrated}/{len(old_highlights)} highlights...")

            except Exception as e:
                logger.error(f"[MIGRATION] Error migrating highlight {highlight.get('id')}: {e}")
                skipped += 1
                continue

        logger.info(f"[MIGRATION] ✓ Migrated {migrated} highlights, skipped {skipped}")

    def _find_or_create_word(self, lemma: str, translation: str, context: str,
                            user_id: Optional[int], session_id: str) -> int:
        """
        Найти существующее слово в dictionary_words или создать новое

        Returns:
            word_id
        """
        # Проверить, существует ли слово
        if user_id is not None:
            check_query = """
            DECLARE $lemma AS Utf8?;
            DECLARE $user_id AS Uint64?;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            existing = self._fetch_one(check_query, {
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            check_query = """
            DECLARE $lemma AS Utf8?;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            existing = self._fetch_one(check_query, {'$lemma': lemma})

        if existing:
            word_id = existing['id']
            logger.debug(f"[MIGRATION] Word '{lemma}' already exists (id={word_id})")

            # Добавить пример, если его еще нет
            self._add_example_if_not_exists(word_id, lemma, context, session_id)

            return word_id

        # Создать новое слово
        word_id = self._get_next_id('dictionary_words')

        insert_word_query = """
        DECLARE $id AS Uint64?;
        DECLARE $user_id AS Uint64?;
        DECLARE $lemma AS Utf8?;
        DECLARE $type AS Utf8?;
        DECLARE $status AS Utf8?;
        DECLARE $added_at AS Utf8?;
        DECLARE $review_count AS Uint32?;
        DECLARE $correct_streak AS Uint32?;
        DECLARE $rating AS Uint32?;

        UPSERT INTO dictionary_words (id, user_id, lemma, type, status, added_at, review_count, correct_streak, rating)
        VALUES ($id, $user_id, $lemma, $type, $status, $added_at, $review_count, $correct_streak, $rating)
        """

        # Определить тип (word или expression)
        word_type = 'expression' if ' ' in lemma else 'word'

        from datetime import datetime
        now = datetime.now().isoformat()

        self._execute_query(insert_word_query, {
            '$id': word_id,
            '$user_id': user_id,
            '$lemma': lemma,
            '$type': word_type,
            '$status': 'new',
            '$added_at': now,
            '$review_count': 0,
            '$correct_streak': 0,
            '$rating': 0
        })

        # Добавить перевод
        translation_id = self._get_next_id('dictionary_translations')
        insert_translation_query = """
        DECLARE $id AS Uint64?;
        DECLARE $word_id AS Uint64?;
        DECLARE $translation AS Utf8?;
        DECLARE $session_id AS Utf8?;
        DECLARE $added_at AS Utf8?;

        UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
        VALUES ($id, $word_id, $translation, $session_id, $added_at)
        """

        self._execute_query(insert_translation_query, {
            '$id': translation_id,
            '$word_id': word_id,
            '$translation': translation,
            '$session_id': session_id,
            '$added_at': now
        })

        # Добавить пример
        if context:
            example_id = self._get_next_id('dictionary_examples')
            insert_example_query = """
            DECLARE $id AS Uint64?;
            DECLARE $word_id AS Uint64?;
            DECLARE $original_form AS Utf8?;
            DECLARE $context AS Utf8?;
            DECLARE $session_id AS Utf8?;
            DECLARE $added_at AS Utf8?;

            UPSERT INTO dictionary_examples (id, word_id, original_form, context, session_id, added_at)
            VALUES ($id, $word_id, $original_form, $context, $session_id, $added_at)
            """

            self._execute_query(insert_example_query, {
                '$id': example_id,
                '$word_id': word_id,
                '$original_form': lemma,
                '$context': context,
                '$session_id': session_id,
                '$added_at': now
            })

        logger.debug(f"[MIGRATION] Created new word '{lemma}' (id={word_id})")
        return word_id

    def _add_example_if_not_exists(self, word_id: int, lemma: str, context: str, session_id: str):
        """Добавить пример к слову, если его еще нет"""
        if not context:
            return

        # Проверить, есть ли уже такой пример
        check_query = """
        DECLARE $word_id AS Uint64?;
        DECLARE $context AS Utf8?;

        SELECT COUNT(*) AS count FROM dictionary_examples
        WHERE word_id = $word_id AND context = $context
        """

        existing = self._fetch_one(check_query, {
            '$word_id': word_id,
            '$context': context
        })

        if existing and existing['count'] > 0:
            return

        # Добавить новый пример
        example_id = self._get_next_id('dictionary_examples')

        from datetime import datetime
        now = datetime.now().isoformat()

        insert_query = """
        DECLARE $id AS Uint64?;
        DECLARE $word_id AS Uint64?;
        DECLARE $original_form AS Utf8?;
        DECLARE $context AS Utf8?;
        DECLARE $session_id AS Utf8?;
        DECLARE $added_at AS Utf8?;

        UPSERT INTO dictionary_examples (id, word_id, original_form, context, session_id, added_at)
        VALUES ($id, $word_id, $original_form, $context, $session_id, $added_at)
        """

        self._execute_query(insert_query, {
            '$id': example_id,
            '$word_id': word_id,
            '$original_form': lemma,
            '$context': context,
            '$session_id': session_id,
            '$added_at': now
        })

    def _replace_table(self):
        """Удалить старую таблицу highlights и переименовать highlights_new"""
        # YDB не поддерживает RENAME TABLE, поэтому:
        # 1. Удаляем старую таблицу
        # 2. Создаем новую таблицу highlights с правильной структурой
        # 3. Копируем данные из highlights_new
        # 4. Удаляем highlights_new

        logger.info("[MIGRATION] Dropping old highlights table...")
        self._execute_query("DROP TABLE highlights")

        logger.info("[MIGRATION] Creating new highlights table...")
        create_query = """
        CREATE TABLE highlights (
            id Uint64,
            analysis_id Uint64,
            word_id Uint64,
            position Uint32,
            PRIMARY KEY (id)
        )
        """
        self._execute_query(create_query)

        logger.info("[MIGRATION] Copying data from highlights_new to highlights...")
        # Получить все записи из highlights_new
        get_all_query = "SELECT id, analysis_id, word_id, position FROM highlights_new"
        all_highlights = self._fetch_all(get_all_query)

        # Вставить в highlights
        for highlight in all_highlights:
            insert_query = """
            DECLARE $id AS Uint64?;
            DECLARE $analysis_id AS Uint64?;
            DECLARE $word_id AS Uint64?;
            DECLARE $position AS Uint32?;

            UPSERT INTO highlights (id, analysis_id, word_id, position)
            VALUES ($id, $analysis_id, $word_id, $position)
            """

            self._execute_query(insert_query, {
                '$id': highlight['id'],
                '$analysis_id': highlight['analysis_id'],
                '$word_id': highlight['word_id'],
                '$position': highlight['position']
            })

        logger.info("[MIGRATION] Dropping highlights_new...")
        self._execute_query("DROP TABLE highlights_new")

        logger.info("[MIGRATION] ✓ Table replacement complete")


if __name__ == '__main__':
    migration = HighlightsMigration()
    migration.run()
