#!/usr/bin/env python3
"""
📖 DICTIONARY MANAGER

Управление персональным словарем пользователя.
Добавление, получение, удаление слов и фраз для изучения.

@version 2.0.0 (YDB)
@author Wordoorio Team
"""

import ydb
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

def _typed_params(params: Dict[str, Any]) -> Dict[str, tuple]:
    """
    Конвертирует словарь параметров в формат с явными типами для YDB

    Args:
        params: Словарь вида {'$lemma': 'test', '$user_id': 1}

    Returns:
        Словарь с явными типами: {'$lemma': ('test', ydb.PrimitiveType.Utf8)}
    """
    typed = {}
    for key, value in params.items():
        if isinstance(value, str):
            typed[key] = (value, ydb.PrimitiveType.Utf8)
        elif isinstance(value, int):
            typed[key] = (value, ydb.PrimitiveType.Int64)
        elif value is None:
            # Для Optional[Int64] передаем None с типом
            typed[key] = (None, ydb.OptionalType(ydb.PrimitiveType.Int64))
        else:
            typed[key] = value  # Оставляем как есть для других типов
    return typed


class DictionaryManager:
    """Менеджер персонального словаря (YDB)"""

    def __init__(self, db_path: str = "wordoorio.db"):
        """
        Инициализация менеджера словаря

        Args:
            db_path: Не используется для YDB, сохранено для совместимости API
        """
        # YDB connection parameters from environment
        self.endpoint = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
        self.database = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')

        # For API compatibility
        self.db_path = db_path

        # Initialize YDB driver
        self._init_driver()

        logger.info(f"[DICTIONARY] YDB connected: {self.endpoint}")

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

        # Create QuerySessionPool for efficient connection reuse
        # NOTE: Using QuerySessionPool instead of SessionPool to avoid SDK 3.23.0 bug
        # with session.transaction().execute() and missing parameters
        self.pool = ydb.QuerySessionPool(self.driver)

    def _execute_query(self, query: str, parameters: Dict = None):
        """
        Execute YQL query with automatic retries using QuerySessionPool

        Args:
            query: YQL query string
            parameters: Query parameters as dict

        Returns:
            Query result
        """
        # Конвертируем параметры с явными типами
        typed_parameters = _typed_params(parameters) if parameters else {}
        logger.info(f"[DEBUG _execute_query] Typed params: {typed_parameters}")

        # Use execute_with_retries instead of session.transaction().execute()
        # to avoid SDK 3.23.0 bug with missing parameters
        return self.pool.execute_with_retries(
            query,
            parameters=typed_parameters
        )

    def _fetch_one(self, query: str, parameters: Dict = None) -> Optional[Dict]:
        """Execute query and return first row as dict"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return None

        row = result[0].rows[0]
        columns = [col.name for col in result[0].columns]
        return {col: getattr(row, col) for col in columns}

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

    def add_word(self, highlight_dict: Dict, session_id: str, user_id: Optional[int] = None) -> Dict:
        """
        Добавить слово в словарь из хайлайта

        Args:
            highlight_dict: Словарь с данными хайлайта
                {
                    'highlight': 'give up',  # УЖЕ лемматизировано!
                    'type': 'expression',
                    'highlight_translation': 'сдаться',
                    'context': 'Never give up on your dreams',
                    'dictionary_meanings': ['бросить', 'оставить']
                }
            session_id: ID сессии анализа
            user_id: ID пользователя (None для anonymous)

        Returns:
            {
                'success': bool,
                'is_new': bool,  # True если слово новое, False если добавлен пример к существующему
                'word_id': int,
                'message': str
            }
        """
        # Извлекаем и валидируем данные
        lemma = highlight_dict.get('highlight')
        if not lemma or not lemma.strip():
            error_msg = f"Missing or empty 'highlight' field. Received keys: {list(highlight_dict.keys())}"
            print(f"[ERROR add_word] {error_msg}")
            print(f"[ERROR add_word] highlight_dict: {highlight_dict}")
            raise ValueError(error_msg)

        word_type = highlight_dict.get('type', 'word')
        main_translation = highlight_dict.get('highlight_translation')
        if not main_translation or not main_translation.strip():
            error_msg = f"Missing or empty 'highlight_translation' field for word '{lemma}'"
            print(f"[ERROR add_word] {error_msg}")
            raise ValueError(error_msg)

        context = highlight_dict.get('context')
        if not context or not context.strip():
            error_msg = f"Missing or empty 'context' field for word '{lemma}'"
            print(f"[ERROR add_word] {error_msg}")
            raise ValueError(error_msg)

        additional_meanings = highlight_dict.get('dictionary_meanings', [])

        logger.info(f"[DEBUG add_word] Adding word: lemma='{lemma}', type='{word_type}', user_id={user_id}")

        # Проверяем: есть ли слово с такой lemma?
        if user_id is not None:
            check_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $user_id AS Int64;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            params = {
                '$lemma': lemma,
                '$user_id': user_id
            }
            logger.info(f"[DEBUG] Params before query: {params}")
            logger.info(f"[DEBUG] lemma type={type(lemma)}, value={repr(lemma)}, user_id={user_id}")
            existing = self._fetch_one(check_query, params)
        else:
            check_query = """
            DECLARE $lemma AS Utf8;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            existing = self._fetch_one(check_query, {'$lemma': lemma})

        now = datetime.now().isoformat()

        if existing:
            # Слово уже есть - добавляем новый перевод и пример
            word_id = existing['id']

            # Добавляем основной перевод (если еще нет)
            check_translation_query = """
            DECLARE $word_id AS Int64;
            DECLARE $translation AS Utf8;

            SELECT COUNT(*) AS count FROM dictionary_translations
            WHERE word_id = $word_id AND translation = $translation
            """
            translation_exists = self._fetch_one(check_translation_query, {
                '$word_id': word_id,
                '$translation': main_translation
            })

            if translation_exists['count'] == 0:
                translation_id = self._get_next_id('dictionary_translations')
                insert_translation_query = """
                DECLARE $id AS Int64;
                DECLARE $word_id AS Int64;
                DECLARE $translation AS Utf8;
                DECLARE $session_id AS Utf8;
                DECLARE $added_at AS Utf8;

                UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
                VALUES ($id, $word_id, $translation, $session_id, $added_at)
                """
                self._execute_query(insert_translation_query, {
                    '$id': translation_id,
                    '$word_id': word_id,
                    '$translation': main_translation,
                    '$session_id': session_id,
                    '$added_at': now
                })

            # Добавляем дополнительные переводы
            for meaning in additional_meanings:
                check_meaning_query = """
                DECLARE $word_id AS Int64;
                DECLARE $translation AS Utf8;

                SELECT COUNT(*) AS count FROM dictionary_translations
                WHERE word_id = $word_id AND translation = $translation
                """
                meaning_exists = self._fetch_one(check_meaning_query, {
                    '$word_id': word_id,
                    '$translation': meaning
                })

                if meaning_exists['count'] == 0:
                    meaning_id = self._get_next_id('dictionary_translations')
                    insert_meaning_query = """
                    DECLARE $id AS Int64;
                    DECLARE $word_id AS Int64;
                    DECLARE $translation AS Utf8;
                    DECLARE $session_id AS Utf8;
                    DECLARE $added_at AS Utf8;

                    UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
                    VALUES ($id, $word_id, $translation, $session_id, $added_at)
                    """
                    self._execute_query(insert_meaning_query, {
                        '$id': meaning_id,
                        '$word_id': word_id,
                        '$translation': meaning,
                        '$session_id': session_id,
                        '$added_at': now
                    })

            # Добавляем новый пример использования
            example_id = self._get_next_id('dictionary_examples')
            insert_example_query = """
            DECLARE $id AS Int64;
            DECLARE $word_id AS Int64;
            DECLARE $original_form AS Utf8;
            DECLARE $context AS Utf8;
            DECLARE $session_id AS Utf8;
            DECLARE $added_at AS Utf8;

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

            return {
                'success': True,
                'is_new': False,
                '$word_id': word_id,
                'message': f'Добавлен новый пример к слову "{lemma}"'
            }

        else:
            # Новое слово - создаем запись
            word_id = self._get_next_id('dictionary_words')

            insert_word_query = """
            DECLARE $id AS Int64;
            DECLARE $user_id AS Int64?;
            DECLARE $lemma AS Utf8;
            DECLARE $type AS Utf8;
            DECLARE $status AS Utf8;
            DECLARE $added_at AS Utf8;
            DECLARE $review_count AS Int64;
            DECLARE $correct_streak AS Int64;
            DECLARE $rating AS Int64;

            UPSERT INTO dictionary_words (id, user_id, lemma, type, status, added_at, review_count, correct_streak, rating)
            VALUES ($id, $user_id, $lemma, $type, $status, $added_at, $review_count, $correct_streak, $rating)
            """

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

            # Добавляем основной перевод
            translation_id = self._get_next_id('dictionary_translations')
            insert_translation_query = """
            DECLARE $id AS Int64;
            DECLARE $word_id AS Int64;
            DECLARE $translation AS Utf8;
            DECLARE $session_id AS Utf8;
            DECLARE $added_at AS Utf8;

            UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
            VALUES ($id, $word_id, $translation, $session_id, $added_at)
            """
            self._execute_query(insert_translation_query, {
                '$id': translation_id,
                '$word_id': word_id,
                '$translation': main_translation,
                '$session_id': session_id,
                '$added_at': now
            })

            # Добавляем дополнительные переводы
            for meaning in additional_meanings:
                meaning_id = self._get_next_id('dictionary_translations')
                insert_meaning_query = """
                DECLARE $id AS Int64;
                DECLARE $word_id AS Int64;
                DECLARE $translation AS Utf8;
                DECLARE $session_id AS Utf8;
                DECLARE $added_at AS Utf8;

                UPSERT INTO dictionary_translations (id, word_id, translation, source_session_id, added_at)
                VALUES ($id, $word_id, $translation, $session_id, $added_at)
                """
                self._execute_query(insert_meaning_query, {
                    '$id': meaning_id,
                    '$word_id': word_id,
                    '$translation': meaning,
                    '$session_id': session_id,
                    '$added_at': now
                })

            # Добавляем первый пример использования
            example_id = self._get_next_id('dictionary_examples')
            insert_example_query = """
            DECLARE $id AS Int64;
            DECLARE $word_id AS Int64;
            DECLARE $original_form AS Utf8;
            DECLARE $context AS Utf8;
            DECLARE $session_id AS Utf8;
            DECLARE $added_at AS Utf8;

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

            return {
                'success': True,
                'is_new': True,
                '$word_id': word_id,
                'message': f'Слово "{lemma}" добавлено в словарь'
            }

    def get_word(self, lemma: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """
        Получить слово с деталями (переводы + примеры)

        Args:
            lemma: Словарная форма слова
            user_id: ID пользователя (None для anonymous)

        Returns:
            {
                '$lemma': 'give up',
                '$type': 'expression',
                '$status': 'new',
                '$added_at': '2024-12-09T10:00:00',
                'translations': [
                    {
                        'text': 'сдаться',
                        'source_session_id': 'session_123',
                        '$added_at': '2024-12-09T10:00:00'
                    }
                ],
                'examples': [
                    {
                        '$original_form': 'gave up',
                        '$context': 'He never gave up on his dreams',
                        '$session_id': 'session_123',
                        '$added_at': '2024-12-09T10:00:00'
                    }
                ]
            }
        """
        # Получаем основную информацию о слове
        if user_id is not None:
            word_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $user_id AS Int64;

            SELECT id, type, status, added_at, last_reviewed_at, review_count, correct_streak
            FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            word_row = self._fetch_one(word_query, {
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            word_query = """
            DECLARE $lemma AS Utf8;

            SELECT id, type, status, added_at, last_reviewed_at, review_count, correct_streak
            FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            word_row = self._fetch_one(word_query, {'$lemma': lemma})

        if not word_row:
            return None

        word_id = word_row['id']

        # Получаем переводы
        translations_query = """
        DECLARE $word_id AS Int64;

        SELECT translation, source_session_id, added_at
        FROM dictionary_translations
        WHERE word_id = $word_id
        ORDER BY added_at ASC
        """
        translation_rows = self._fetch_all(translations_query, {'$word_id': word_id})

        translations = [
            {
                'text': row['translation'],
                'source_session_id': row['source_session_id'],
                '$added_at': row['added_at']
            }
            for row in translation_rows
        ]

        # Получаем примеры
        examples_query = """
        DECLARE $word_id AS Int64;

        SELECT original_form, context, session_id, added_at
        FROM dictionary_examples
        WHERE word_id = $word_id
        ORDER BY added_at ASC
        """
        example_rows = self._fetch_all(examples_query, {'$word_id': word_id})

        examples = [
            {
                '$original_form': row['original_form'],
                '$context': row['context'],
                '$session_id': row['session_id'],
                '$added_at': row['added_at']
            }
            for row in example_rows
        ]

        return {
            '$lemma': lemma,
            '$type': word_row['type'],
            '$status': word_row['status'],
            '$added_at': word_row['added_at'],
            '$last_reviewed_at': word_row['last_reviewed_at'],
            '$review_count': word_row['review_count'],
            '$correct_streak': word_row['correct_streak'],
            'translations': translations,
            'examples': examples
        }

    def get_all_words(self, user_id: Optional[int] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Получить все слова словаря

        Args:
            user_id: ID пользователя (None для anonymous)
            filters: Фильтры (пока не используется, для будущего)

        Returns:
            [
                {
                    '$lemma': 'give up',
                    '$type': 'expression',
                    'translations': ['сдаться', 'бросить'],
                    'examples_count': 3,
                    '$status': 'new',
                    '$added_at': '2024-12-09T10:00:00'
                }
            ]
        """
        # Получаем все слова
        if user_id is not None:
            words_query = """
            DECLARE $user_id AS Int64?;

            SELECT id, lemma, type, status, added_at
            FROM dictionary_words
            WHERE user_id = $user_id
            ORDER BY added_at DESC
            """
            word_rows = self._fetch_all(words_query, {'$user_id': user_id})
        else:
            words_query = """
            SELECT id, lemma, type, status, added_at
            FROM dictionary_words
            WHERE user_id IS NULL
            ORDER BY added_at DESC
            """
            word_rows = self._fetch_all(words_query)

        words = []
        for row in word_rows:
            word_id = row['id']
            lemma = row['lemma']
            word_type = row['type']
            status = row['status']
            added_at = row['added_at']

            # Получаем переводы
            translations_query = """
            DECLARE $word_id AS Int64;

            SELECT translation FROM dictionary_translations
            WHERE word_id = $word_id
            ORDER BY added_at ASC
            """
            translation_rows = self._fetch_all(translations_query, {'$word_id': word_id})
            translations = [t['translation'] for t in translation_rows]

            # Получаем количество примеров
            examples_count_query = """
            DECLARE $word_id AS Int64;

            SELECT COUNT(*) AS count FROM dictionary_examples
            WHERE word_id = $word_id
            """
            examples_count_row = self._fetch_one(examples_count_query, {'$word_id': word_id})
            examples_count = examples_count_row['count'] if examples_count_row else 0

            words.append({
                '$lemma': lemma,
                '$type': word_type,
                'translations': translations,
                'examples_count': examples_count,
                '$status': status,
                '$added_at': added_at
            })

        return words

    def delete_word(self, lemma: str, user_id: Optional[int] = None) -> Dict:
        """
        Удалить слово из словаря

        Args:
            lemma: Словарная форма слова
            user_id: ID пользователя

        Returns:
            {'success': bool, 'message': str}
        """
        # YDB doesn't have CASCADE DELETE, so we need to delete manually
        # First check if word exists and get its ID
        if user_id is not None:
            check_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $user_id AS Int64?;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            word_row = self._fetch_one(check_query, {
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            check_query = """
            DECLARE $lemma AS Utf8;

            SELECT id FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            word_row = self._fetch_one(check_query, {'$lemma': lemma})

        if not word_row:
            return {
                'success': False,
                'message': f'Слово "{lemma}" не найдено в словаре'
            }

        word_id = word_row['id']

        # Delete translations
        delete_translations_query = """
            DECLARE $word_id AS Int64;

        DELETE FROM dictionary_translations
        WHERE word_id = $word_id
        """
        self._execute_query(delete_translations_query, {'$word_id': word_id})

        # Delete examples
        delete_examples_query = """
            DECLARE $word_id AS Int64;

        DELETE FROM dictionary_examples
        WHERE word_id = $word_id
        """
        self._execute_query(delete_examples_query, {'$word_id': word_id})

        # Delete word
        delete_word_query = """
            DECLARE $word_id AS Int64;

        DELETE FROM dictionary_words
        WHERE id = $word_id
        """
        self._execute_query(delete_word_query, {'$word_id': word_id})

        return {
            'success': True,
            'message': f'Слово "{lemma}" удалено из словаря'
        }

    def get_stats(self, user_id: Optional[int] = None) -> Dict:
        """
        Получить статистику словаря

        Args:
            user_id: ID пользователя

        Returns:
            {
                'total_words': 42,
                'total_phrases': 18,
                'total_count': 60,
                'status_breakdown': {
                    'new': 60,
                    'learning': 0,
                    'learned': 0
                }
            }
        """
        # Общее количество слов
        if user_id is not None:
            words_query = """
            DECLARE $user_id AS Int64?;

            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE user_id = $user_id AND type = 'word'
            """
            words_result = self._fetch_one(words_query, {'$user_id': user_id})
        else:
            words_query = """
            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE user_id IS NULL AND type = 'word'
            """
            words_result = self._fetch_one(words_query)

        total_words = words_result['count'] if words_result else 0

        # Общее количество фраз
        if user_id is not None:
            phrases_query = """
            DECLARE $user_id AS Int64?;

            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE user_id = $user_id AND type = 'expression'
            """
            phrases_result = self._fetch_one(phrases_query, {'$user_id': user_id})
        else:
            phrases_query = """
            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE user_id IS NULL AND type = 'expression'
            """
            phrases_result = self._fetch_one(phrases_query)

        total_phrases = phrases_result['count'] if phrases_result else 0

        # Разбивка по статусам
        if user_id is not None:
            status_query = """
            DECLARE $user_id AS Int64?;

            SELECT status, COUNT(*) AS count FROM dictionary_words
            WHERE user_id = $user_id
            GROUP BY status
            """
            status_rows = self._fetch_all(status_query, {'$user_id': user_id})
        else:
            status_query = """
            SELECT status, COUNT(*) AS count FROM dictionary_words
            WHERE user_id IS NULL
            GROUP BY status
            """
            status_rows = self._fetch_all(status_query)

        status_breakdown = {row['status']: row['count'] for row in status_rows}

        return {
            'total_words': total_words,
            'total_phrases': total_phrases,
            'total_count': total_words + total_phrases,
            'status_breakdown': status_breakdown
        }

    def update_word_status(self, lemma: str, status: str, user_id: Optional[int] = None) -> Dict:
        """
        Обновить статус слова (для будущей интеграции с ботом)

        Args:
            lemma: Словарная форма слова
            status: Новый статус ('new', 'learning', 'learned', 'review')
            user_id: ID пользователя

        Returns:
            {'success': bool, 'message': str}
        """
        valid_statuses = ['new', 'learning', 'learned', 'review']
        if status not in valid_statuses:
            return {
                'success': False,
                'message': f'Недопустимый статус. Допустимые: {", ".join(valid_statuses)}'
            }

        if user_id is not None:
            update_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $status AS Utf8;
            DECLARE $user_id AS Int64?;

            UPDATE dictionary_words
            SET status = $status
            WHERE lemma = $lemma AND user_id = $user_id
            """
            self._execute_query(update_query, {
                '$status': status,
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            update_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $status AS Utf8;

            UPDATE dictionary_words
            SET status = $status
            WHERE lemma = $lemma AND user_id IS NULL
            """
            self._execute_query(update_query, {
                '$status': status,
                '$lemma': lemma
            })

        # Check if update was successful by checking if word exists
        if user_id is not None:
            check_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $user_id AS Int64?;

            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            result = self._fetch_one(check_query, {
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            check_query = """
            DECLARE $lemma AS Utf8;

            SELECT COUNT(*) AS count FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            result = self._fetch_one(check_query, {'$lemma': lemma})

        if result and result['count'] > 0:
            return {
                'success': True,
                'message': f'Статус слова "{lemma}" обновлен на "{status}"'
            }
        else:
            return {
                'success': False,
                'message': f'Слово "{lemma}" не найдено в словаре'
            }

    def update_review_stats(self, lemma: str, is_correct: bool, user_id: Optional[int] = None) -> Dict:
        """
        Обновить статистику повторений (для будущей интеграции с ботом)

        Args:
            lemma: Словарная форма слова
            is_correct: Правильно ли пользователь ответил
            user_id: ID пользователя

        Returns:
            {
                'success': bool,
                'new_status': str,  # Если изменился
                '$correct_streak': int,
                'message': str
            }
        """
        # Получаем текущую статистику
        if user_id is not None:
            word_query = """
            DECLARE $lemma AS Utf8;
            DECLARE $user_id AS Int64?;

            SELECT correct_streak, review_count, status
            FROM dictionary_words
            WHERE lemma = $lemma AND user_id = $user_id
            """
            word_row = self._fetch_one(word_query, {
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            word_query = """
            DECLARE $lemma AS Utf8;

            SELECT correct_streak, review_count, status
            FROM dictionary_words
            WHERE lemma = $lemma AND user_id IS NULL
            """
            word_row = self._fetch_one(word_query, {'$lemma': lemma})

        if not word_row:
            return {
                'success': False,
                'message': f'Слово "{lemma}" не найдено в словаре'
            }

        current_streak = word_row['correct_streak']
        review_count = word_row['review_count']
        current_status = word_row['status']

        # Обновляем streak
        if is_correct:
            new_streak = current_streak + 1
        else:
            new_streak = 0  # Сбрасываем при ошибке

        # Обновляем статус
        new_status = current_status
        if new_streak >= 10 and current_status != 'learned':
            new_status = 'learned'  # 10 правильных подряд = изучено
        elif review_count == 0 and current_status == 'new':
            new_status = 'learning'  # Первая тренировка

        now = datetime.now().isoformat()

        # Обновляем запись
        if user_id is not None:
            update_query = """
            DECLARE $correct_streak AS Int64;
            DECLARE $last_reviewed_at AS Utf8;
            DECLARE $lemma AS Utf8;
            DECLARE $review_count AS Int64;
            DECLARE $status AS Utf8;
            DECLARE $user_id AS Int64?;

            UPDATE dictionary_words
            SET
                correct_streak = $correct_streak,
                review_count = $review_count,
                last_reviewed_at = $last_reviewed_at,
                status = $status
            WHERE lemma = $lemma AND user_id = $user_id
            """
            self._execute_query(update_query, {
                '$correct_streak': new_streak,
                '$review_count': review_count + 1,
                '$last_reviewed_at': now,
                '$status': new_status,
                '$lemma': lemma,
                '$user_id': user_id
            })
        else:
            update_query = """
            DECLARE $correct_streak AS Int64;
            DECLARE $last_reviewed_at AS Utf8;
            DECLARE $lemma AS Utf8;
            DECLARE $review_count AS Int64;
            DECLARE $status AS Utf8;

            UPDATE dictionary_words
            SET
                correct_streak = $correct_streak,
                review_count = $review_count,
                last_reviewed_at = $last_reviewed_at,
                status = $status
            WHERE lemma = $lemma AND user_id IS NULL
            """
            self._execute_query(update_query, {
                '$correct_streak': new_streak,
                '$review_count': review_count + 1,
                '$last_reviewed_at': now,
                '$status': new_status,
                '$lemma': lemma
            })

        return {
            'success': True,
            'new_status': new_status,
            '$correct_streak': new_streak,
            'message': f'Статистика обновлена. Серия: {new_streak}'
        }

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'driver'):
            self.driver.stop()


# Для тестирования
if __name__ == '__main__':
    print("🧪 ТЕСТ DICTIONARY MANAGER (YDB)")
    print("=" * 50)

    manager = DictionaryManager()

    # Тест 1: Добавление нового слова
    print("\n📝 Тест 1: Добавление нового слова")
    test_highlight = {
        'highlight': 'give up',
        'type': 'expression',
        'highlight_translation': 'сдаться',
        'context': 'Never give up on your dreams',
        'dictionary_meanings': ['бросить', 'оставить']
    }

    result = manager.add_word(test_highlight, 'test_session_1')
    print(f"Результат: {result}")

    # Тест 2: Добавление еще одного примера к тому же слову
    print("\n📝 Тест 2: Добавление примера к существующему слову")
    test_highlight2 = {
        'highlight': 'give up',
        'type': 'expression',
        'highlight_translation': 'бросить дело',
        'context': 'Don\'t give up so easily',
        'dictionary_meanings': []
    }

    result2 = manager.add_word(test_highlight2, 'test_session_2')
    print(f"Результат: {result2}")

    # Тест 3: Получение слова с деталями
    print("\n📖 Тест 3: Получение деталей слова")
    word = manager.get_word('give up')
    if word:
        print(f"Слово: {word['lemma']}")
        print(f"Переводы: {[t['text'] for t in word['translations']]}")
        print(f"Примеров: {len(word['examples'])}")

    # Тест 4: Получение всех слов
    print("\n📚 Тест 4: Все слова в словаре")
    all_words = manager.get_all_words()
    print(f"Всего слов: {len(all_words)}")
    for w in all_words:
        print(f"  - {w['lemma']} ({w['type']}): {', '.join(w['translations'][:2])}")

    # Тест 5: Статистика
    print("\n📊 Тест 5: Статистика словаря")
    stats = manager.get_stats()
    print(f"Слов: {stats['total_words']}, Фраз: {stats['total_phrases']}, Всего: {stats['total_count']}")
    print(f"Статусы: {stats['status_breakdown']}")

    print("\n✅ Тесты завершены!")
