#!/usr/bin/env python3
"""
YDB Database Manager for Wordoorio
Manages all database operations using Yandex Database (YDB)
"""

import ydb
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _typed_params(params: Dict[str, Any]) -> Dict[str, ydb.TypedValue]:
    """
    Конвертирует словарь параметров в формат TypedValue для YDB

    ВАЖНО: ВСЕ поля в таблицах являются Optional (Utf8?, Uint64?, Uint32?).
    Используем TypedValue (вариант 2 по рекомендации поддержки YDB).

    Args:
        params: Словарь вида {'$lemma': 'test', '$user_id': 1}

    Returns:
        Словарь с TypedValue: {'$lemma': TypedValue('test', Optional<Utf8>), '$user_id': TypedValue(1, Optional<Uint64>)}
    """
    typed = {}
    for key, value in params.items():
        # ВАЖНО: bool проверяем ДО int, т.к. isinstance(True, int) == True в Python
        if isinstance(value, bool):
            typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Bool))
        elif isinstance(value, str):
            # Все строки как Optional<Utf8>
            typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Utf8))
        elif isinstance(value, int):
            # Используем Uint64 для ID и больших чисел, Uint32 для счетчиков
            # ID полей: id, user_id, word_id, analysis_id
            if 'id' in key.lower():
                typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Uint64))
            # Счетчики: review_count, correct_streak, rating, position, total_highlights, total_words, limit
            else:
                typed[key] = ydb.TypedValue(value, ydb.OptionalType(ydb.PrimitiveType.Uint32))
        elif value is None:
            # Для None используем Optional<Uint64>
            typed[key] = ydb.TypedValue(None, ydb.OptionalType(ydb.PrimitiveType.Uint64))
        else:
            typed[key] = value  # Оставляем как есть для других типов
    return typed


class WordoorioDatabase:
    """YDB-based database manager for Wordoorio application"""

    def __init__(self, db_path: str = None):
        """
        Initialize YDB connection

        Args:
            db_path: Not used for YDB, kept for API compatibility
        """
        # YDB connection parameters from environment
        self.endpoint = os.getenv('YDB_ENDPOINT', 'grpcs://ydb.serverless.yandexcloud.net:2135')
        self.database = os.getenv('YDB_DATABASE', '/ru-central1/b1g5sgin5ubfvtkrvjft/etnnib344dr71jrf015e')

        # For API compatibility
        self.db_path = db_path or "ydb"

        # Initialize YDB driver
        self._init_driver()

        logger.info(f"[YDB] Connected to {self.endpoint}, database: {self.database}")

    def _init_driver(self):
        """Initialize YDB driver with credentials"""
        # Use IAM token for local development, metadata service for production
        iam_token = os.getenv('YANDEX_IAM_TOKEN')
        if iam_token:
            credentials = ydb.AccessTokenCredentials(iam_token)
        else:
            # Use MetadataUrlCredentials for serverless containers
            # This automatically uses the service account attached to the container
            credentials = ydb.iam.MetadataUrlCredentials()

        driver_config = ydb.DriverConfig(
            endpoint=self.endpoint,
            database=self.database,
            credentials=credentials
        )

        self.driver = ydb.Driver(driver_config)
        self.driver.wait(fail_fast=True, timeout=5)

        # Create QuerySessionPool for efficient connection reuse
        # QuerySessionPool is newer and handles typed parameters better
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
        # Конвертируем параметры в типизированный формат YDB
        typed_params = _typed_params(parameters) if parameters else {}

        # Use execute_with_retries instead of session.transaction().execute()
        # QuerySessionPool handles typed parameters correctly
        return self.pool.execute_with_retries(
            query,
            parameters=typed_params
        )

    def _fetch_one(self, query: str, parameters: Dict = None) -> Optional[Dict]:
        """Execute query and return first row as dict"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return None

        # YDB rows are already dict-like objects
        return dict(result[0].rows[0])

    def _fetch_all(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute query and return all rows as list of dicts"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return []

        # YDB rows are already dict-like objects
        return [dict(row) for row in result[0].rows]

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

    # ====================
    # Analysis Methods
    # ====================

    def save_analysis(self,
                     original_text: str,
                     analysis_result: Dict,
                     user_id: Optional[int] = None,
                     session_id: Optional[str] = None,
                     ip_address: Optional[str] = None) -> int:
        """
        Save text analysis results to database

        Args:
            original_text: Original input text
            analysis_result: Analysis results with highlights
            user_id: User ID (for authenticated users)
            session_id: Session identifier
            ip_address: Client IP address

        Returns:
            analysis_id: ID of created analysis record
        """
        # Get next ID
        analysis_id = self._get_next_id('analyses')

        # Extract highlights from result
        highlights = analysis_result.get('highlights', [])
        total_highlights = len(highlights)
        total_words = analysis_result.get('total_words', 0)

        # Insert analysis record
        query = """
        DECLARE $id AS Uint64?;
        DECLARE $user_id AS Uint64?;
        DECLARE $original_text AS Utf8?;
        DECLARE $total_highlights AS Uint32?;
        DECLARE $total_words AS Uint32?;
        DECLARE $session_id AS Utf8?;
        DECLARE $ip_address AS Utf8?;

        UPSERT INTO analyses (id, user_id, original_text, analysis_date, total_highlights, total_words, session_id, ip_address)
        VALUES ($id, $user_id, $original_text, CurrentUtcTimestamp(), $total_highlights, $total_words, $session_id, $ip_address)
        """

        self._execute_query(query, {
            '$id': analysis_id,
            '$user_id': user_id,
            '$original_text': original_text,
            '$total_highlights': total_highlights,
            '$total_words': total_words,
            '$session_id': session_id,
            '$ip_address': ip_address
        })

        # НЕ создаем highlights здесь!
        # Highlights создаются ТОЛЬКО при клике "+" через /api/dictionary/add
        # save_analysis() сохраняет только метаинформацию об анализе текста

        logger.info(f"[YDB] Saved analysis {analysis_id} (metadata only, no highlights)")
        return analysis_id

    def get_user_highlights(self, user_id: int, limit: int = 100) -> List[Dict]:
        """
        Get all highlights for a specific user

        Args:
            user_id: User ID
            limit: Maximum number of analyses to fetch

        Returns:
            List of analyses with their highlights
        """
        # Get user's analyses
        analyses_query = """
        DECLARE $user_id AS Uint64?;
        DECLARE $limit AS Uint32?;

        SELECT id, original_text, analysis_date, total_highlights, total_words, session_id
        FROM analyses
        WHERE user_id = $user_id
        ORDER BY analysis_date DESC
        LIMIT $limit
        """

        analyses = self._fetch_all(analyses_query, {
            '$user_id': user_id,
            '$limit': limit
        })

        if not analyses:
            return []

        # Get highlights for each analysis (with JOIN to dictionary_words)
        result = []
        for analysis in analyses:
            analysis_id = analysis['id']

            # НОВЫЙ ЗАПРОС: JOIN с dictionary_words для получения полных данных слова
            # ВАЖНО: Явно задаем алиасы с AS для всех полей, чтобы YDB возвращал их без префиксов
            highlights_query = """
            DECLARE $analysis_id AS Uint64?;

            SELECT
                h.word_id AS word_id,
                h.position AS position,
                w.lemma AS highlight,
                w.type AS type,
                t.translation AS highlight_translation
            FROM highlights AS h
            INNER JOIN dictionary_words AS w ON h.word_id = w.id
            LEFT JOIN dictionary_translations AS t ON w.id = t.word_id
            WHERE h.analysis_id = $analysis_id
            ORDER BY h.position
            """

            raw_highlights = self._fetch_all(highlights_query, {
                '$analysis_id': analysis_id
            })

            # Группируем переводы и примеры по word_id
            highlights_map = {}
            for row in raw_highlights:
                # DEBUG: проверяем какие ключи возвращает YDB
                if not highlights_map:  # Логируем только первую запись
                    logger.debug(f"[YDB] Row keys: {list(row.keys())}")
                    logger.debug(f"[YDB] Row values: {row}")

                word_id = row.get('word_id')
                if not word_id:
                    logger.warning(f"[YDB] word_id not found in row: {row}")
                    continue

                if word_id not in highlights_map:
                    highlights_map[word_id] = {
                        'highlight': row['highlight'],
                        'type': row['type'],
                        'highlight_translation': row['highlight_translation'],
                        'main_translation': row['highlight_translation'],  # Сохраняем основной перевод
                        'translations': [],  # Дополнительные переводы (без основного)
                        'position': row['position']
                    }
                else:
                    # Добавляем дополнительные переводы (исключая основной)
                    translation = row['highlight_translation']
                    main_translation = highlights_map[word_id]['main_translation']

                    if translation and translation != main_translation and translation not in highlights_map[word_id]['translations']:
                        highlights_map[word_id]['translations'].append(translation)

            # Получаем примеры для каждого слова
            for word_id in highlights_map.keys():
                examples_query = """
                DECLARE $word_id AS Uint64?;

                SELECT context
                FROM dictionary_examples
                WHERE word_id = $word_id
                LIMIT 1
                """

                examples = self._fetch_all(examples_query, {'$word_id': word_id})
                if examples and len(examples) > 0:
                    highlights_map[word_id]['context'] = examples[0]['context']
                else:
                    highlights_map[word_id]['context'] = ''

            # Сортируем highlights по position
            highlights = sorted(highlights_map.values(), key=lambda x: x['position'])

            # Удаляем служебные поля перед отправкой
            for h in highlights:
                h.pop('position', None)
                h.pop('main_translation', None)  # Удаляем служебное поле
                # Переименовываем translations → dictionary_meanings для обратной совместимости
                h['dictionary_meanings'] = h.pop('translations', [])

            result.append({
                'analysis_id': analysis_id,
                'original_text': analysis['original_text'],
                'analysis_date': analysis['analysis_date'],
                'total_highlights': analysis['total_highlights'],
                'total_words': analysis['total_words'],
                'session_id': analysis['session_id'],
                'highlights': highlights
            })

        logger.info(f"[YDB] Fetched {len(result)} analyses for user {user_id}")
        return result

    def get_analysis_by_session(self, session_id: str, user_id: int) -> Optional[Dict]:
        """
        Get analysis by session_id and user_id

        Args:
            session_id: Session identifier
            user_id: User ID

        Returns:
            Analysis record or None if not found
        """
        query = """
        DECLARE $session_id AS Utf8?;
        DECLARE $user_id AS Uint64?;

        SELECT id, original_text, analysis_date, total_highlights, total_words, session_id
        FROM analyses
        WHERE session_id = $session_id AND user_id = $user_id
        ORDER BY analysis_date DESC
        LIMIT 1
        """

        result = self._fetch_one(query, {
            '$session_id': session_id,
            '$user_id': user_id
        })

        return result

    def add_highlight_to_analysis(self, analysis_id: int, word_id: int, user_id: Optional[int], session_id: str) -> int:
        """
        Add a single highlight to an existing analysis

        Args:
            analysis_id: Analysis ID
            word_id: ID of word in dictionary_words (already created)
            user_id: User ID (for verification)
            session_id: Session ID (for logging)

        Returns:
            highlight_id: ID of created highlight record
        """
        # word_id уже создан в dictionary_words через dict_manager.add_word()
        # Просто создаем highlight-ссылку

        # Получить последнюю позицию в этом анализе
        get_max_position_query = """
        DECLARE $analysis_id AS Uint64?;

        SELECT MAX(position) AS max_position FROM highlights
        WHERE analysis_id = $analysis_id
        """

        result = self._fetch_one(get_max_position_query, {'$analysis_id': analysis_id})
        position = (result['max_position'] or 0) + 1 if result else 1

        # Создать highlight со ссылкой на word_id
        highlight_id = self._get_next_id('highlights')

        highlight_query = """
        DECLARE $id AS Uint64?;
        DECLARE $analysis_id AS Uint64?;
        DECLARE $word_id AS Uint64?;
        DECLARE $position AS Uint32?;

        UPSERT INTO highlights (id, analysis_id, word_id, position)
        VALUES ($id, $analysis_id, $word_id, $position)
        """

        self._execute_query(highlight_query, {
            '$id': highlight_id,
            '$analysis_id': analysis_id,
            '$word_id': word_id,
            '$position': position
        })

        # Update total_highlights counter in analyses table
        update_query = """
        DECLARE $analysis_id AS Uint64?;

        UPDATE analyses
        SET total_highlights = total_highlights + 1
        WHERE id = $analysis_id
        """

        self._execute_query(update_query, {
            '$analysis_id': analysis_id
        })

        logger.info(f"[YDB] Added highlight {highlight_id} (word_id={word_id}) to analysis {analysis_id}")
        return highlight_id

    def delete_analysis(self, analysis_id: int, user_id: int) -> bool:
        """
        Удалить анализ и все связанные хайлайты

        Args:
            analysis_id: ID анализа
            user_id: ID пользователя (для проверки прав доступа)

        Returns:
            bool: True если удалено, False если не найдено или нет прав
        """
        # Сначала проверяем, что анализ принадлежит пользователю
        check_query = """
        DECLARE $id AS Uint64?;
        DECLARE $user_id AS Uint64?;

        SELECT id FROM analyses
        WHERE id = $id AND user_id = $user_id
        """

        analysis = self._fetch_one(check_query, {
            '$id': analysis_id,
            '$user_id': user_id
        })

        if not analysis:
            logger.warning(f"[YDB] Анализ {analysis_id} не найден или не принадлежит пользователю {user_id}")
            return False

        # Удаляем связанные хайлайты
        delete_highlights_query = """
        DECLARE $analysis_id AS Uint64?;

        DELETE FROM highlights
        WHERE analysis_id = $analysis_id
        """

        self._execute_query(delete_highlights_query, {
            '$analysis_id': analysis_id
        })

        # Удаляем сам анализ
        delete_analysis_query = """
        DECLARE $id AS Uint64?;

        DELETE FROM analyses
        WHERE id = $id
        """

        self._execute_query(delete_analysis_query, {
            '$id': analysis_id
        })

        logger.info(f"[YDB] Удален анализ {analysis_id} пользователя {user_id}")
        return True

    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent text analyses"""
        query = f"""
        SELECT *
        FROM analyses
        ORDER BY analysis_date DESC
        LIMIT {limit}
        """

        return self._fetch_all(query)

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get analysis by ID with all highlights"""
        # Get analysis
        analysis_query = """
        DECLARE $id AS Uint64?;

        SELECT *
        FROM analyses
        WHERE id = $id
        """

        analysis = self._fetch_one(analysis_query, {'$id': analysis_id})

        if not analysis:
            return None

        # Get highlights
        highlights_query = """
        DECLARE $analysis_id AS Uint64?;

        SELECT *
        FROM highlights
        WHERE analysis_id = $analysis_id
        ORDER BY id
        """

        highlights = self._fetch_all(highlights_query, {'$analysis_id': analysis_id})

        analysis['highlights'] = highlights
        return analysis

    def search_by_word(self, word: str, limit: int = 20) -> List[Dict]:
        """Search analyses by word in highlights"""
        query = f"""
        DECLARE $word AS Utf8?;

        SELECT DISTINCT a.*
        FROM analyses AS a
        JOIN highlights AS h ON a.id = h.analysis_id
        WHERE h.highlight_word LIKE '%' || $word || '%'
        ORDER BY a.analysis_date DESC
        LIMIT {limit}
        """

        return self._fetch_all(query, {'$word': word})

    def get_stats(self) -> Dict:
        """Get database statistics"""
        # Count analyses
        analyses_query = "SELECT COUNT(*) AS count FROM analyses"
        analyses_result = self._fetch_one(analyses_query)
        total_analyses = analyses_result['count'] if analyses_result else 0

        # Count highlights
        highlights_query = "SELECT COUNT(*) AS count FROM highlights"
        highlights_result = self._fetch_one(highlights_query)
        total_highlights = highlights_result['count'] if highlights_result else 0

        # Count dictionary words
        words_query = "SELECT COUNT(*) AS count FROM dictionary_words"
        words_result = self._fetch_one(words_query)
        total_words = words_result['count'] if words_result else 0

        return {
            'total_analyses': total_analyses,
            'total_highlights': total_highlights,
            'total_dictionary_words': total_words
        }

    # ====================
    # Training Methods
    # ====================

    def get_user_training_state(self, user_id: int) -> Dict:
        """Get user's training state"""
        query = """
        DECLARE $user_id AS Uint64?;

        SELECT *
        FROM user_training_state
        WHERE user_id = $user_id
        """

        state = self._fetch_one(query, {'$user_id': user_id})

        if not state:
            # Create default state
            return {
                'user_id': user_id,
                'last_selection_position': 0,
                'last_training_at': None
            }

        return state

    def update_training_position(self, user_id: int, position: int):
        """Update user's training position"""
        query = """
        DECLARE $user_id AS Uint64?;
        DECLARE $position AS Uint32?;
        DECLARE $timestamp AS Utf8?;

        UPSERT INTO user_training_state (user_id, last_selection_position, last_training_at)
        VALUES ($user_id, $position, $timestamp)
        """

        self._execute_query(query, {
            '$user_id': user_id,
            '$position': position,
            '$timestamp': datetime.now().isoformat()
        })

    # ====================
    # Test Methods
    # ====================

    def insert_test(self, user_id: int, word_id: int, word: str,
                   correct_translation: str, wrong_option_1: str,
                   wrong_option_2: str, wrong_option_3: str) -> int:
        """Insert new test"""
        test_id = self._get_next_id('tests')

        query = """
        DECLARE $id AS Uint64?;
        DECLARE $user_id AS Uint64?;
        DECLARE $word_id AS Uint64?;
        DECLARE $word AS Utf8?;
        DECLARE $correct_translation AS Utf8?;
        DECLARE $wrong_option_1 AS Utf8?;
        DECLARE $wrong_option_2 AS Utf8?;
        DECLARE $wrong_option_3 AS Utf8?;
        DECLARE $created_at AS Utf8?;

        UPSERT INTO tests (id, user_id, word_id, word, correct_translation, wrong_option_1, wrong_option_2, wrong_option_3, created_at)
        VALUES ($id, $user_id, $word_id, $word, $correct_translation, $wrong_option_1, $wrong_option_2, $wrong_option_3, $created_at)
        """

        self._execute_query(query, {
            '$id': test_id,
            '$user_id': user_id,
            '$word_id': word_id,
            '$word': word,
            '$correct_translation': correct_translation,
            '$wrong_option_1': wrong_option_1,
            '$wrong_option_2': wrong_option_2,
            '$wrong_option_3': wrong_option_3,
            '$created_at': datetime.now().isoformat()
        })

        return test_id

    def get_test(self, test_id: int) -> Optional[Dict]:
        """Get test by ID"""
        query = """
        DECLARE $id AS Uint64?;

        SELECT *
        FROM tests
        WHERE id = $id
        """

        return self._fetch_one(query, {'$id': test_id})

    def delete_test(self, test_id: int):
        """Delete test by ID"""
        query = """
        DECLARE $id AS Uint64?;

        DELETE FROM tests
        WHERE id = $id
        """

        self._execute_query(query, {'$id': test_id})

    def get_pending_tests(self, user_id: int) -> List[Dict]:
        """Get all pending tests for user"""
        query = """
        DECLARE $user_id AS Uint64?;

        SELECT *
        FROM tests
        WHERE user_id = $user_id
        ORDER BY created_at DESC
        """

        return self._fetch_all(query, {'$user_id': user_id})

    # ====================
    # Word Methods
    # ====================

    def update_word_rating(self, word_id: int, rating: int, last_rating_change: str = None):
        """Update word rating"""
        if last_rating_change is None:
            last_rating_change = datetime.now().isoformat()

        query = """
        DECLARE $id AS Uint64?;
        DECLARE $rating AS Uint32?;
        DECLARE $last_rating_change AS Utf8?;

        UPDATE dictionary_words
        SET rating = $rating, last_rating_change = $last_rating_change
        WHERE id = $id
        """

        self._execute_query(query, {
            '$id': word_id,
            '$rating': rating,
            '$last_rating_change': last_rating_change
        })

    def update_word_status(self, word_id: int, status: str):
        """Update word status"""
        query = """
        DECLARE $id AS Uint64?;
        DECLARE $status AS Utf8?;

        UPDATE dictionary_words
        SET status = $status
        WHERE id = $id
        """

        self._execute_query(query, {
            '$id': word_id,
            '$status': status
        })

    def update_word_statistics(self, user_id: int, word_id: int, is_correct: bool):
        """Update word test statistics"""
        # Get existing statistics
        query = """
        DECLARE $user_id AS Uint64?;
        DECLARE $word_id AS Uint64?;

        SELECT *
        FROM word_test_statistics
        WHERE user_id = $user_id AND word_id = $word_id
        """

        stats = self._fetch_one(query, {
            '$user_id': user_id,
            '$word_id': word_id
        })

        if stats:
            # Update existing
            update_query = """
            DECLARE $id AS Uint64?;
            DECLARE $total_tests AS Uint32?;
            DECLARE $correct_answers AS Uint32?;
            DECLARE $wrong_answers AS Uint32?;
            DECLARE $last_test_at AS Utf8?;
            DECLARE $last_result AS Bool?;

            UPDATE word_test_statistics
            SET total_tests = $total_tests,
                correct_answers = $correct_answers,
                wrong_answers = $wrong_answers,
                last_test_at = $last_test_at,
                last_result = $last_result
            WHERE id = $id
            """

            self._execute_query(update_query, {
                '$id': stats['id'],
                '$total_tests': stats['total_tests'] + 1,
                '$correct_answers': stats['correct_answers'] + (1 if is_correct else 0),
                '$wrong_answers': stats['wrong_answers'] + (0 if is_correct else 1),
                '$last_test_at': datetime.now().isoformat(),
                '$last_result': is_correct
            })
        else:
            # Create new
            stat_id = self._get_next_id('word_test_statistics')

            insert_query = """
            DECLARE $id AS Uint64?;
            DECLARE $user_id AS Uint64?;
            DECLARE $word_id AS Uint64?;
            DECLARE $total_tests AS Uint32?;
            DECLARE $correct_answers AS Uint32?;
            DECLARE $wrong_answers AS Uint32?;
            DECLARE $last_test_at AS Utf8?;
            DECLARE $last_result AS Bool?;

            UPSERT INTO word_test_statistics (id, user_id, word_id, total_tests, correct_answers, wrong_answers, last_test_at, last_result)
            VALUES ($id, $user_id, $word_id, $total_tests, $correct_answers, $wrong_answers, $last_test_at, $last_result)
            """

            self._execute_query(insert_query, {
                '$id': stat_id,
                '$user_id': user_id,
                '$word_id': word_id,
                '$total_tests': 1,
                '$correct_answers': 1 if is_correct else 0,
                '$wrong_answers': 0 if is_correct else 1,
                '$last_test_at': datetime.now().isoformat(),
                '$last_result': is_correct
            })

    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """Get dictionary word by ID"""
        query = """
        DECLARE $id AS Uint64?;

        SELECT *
        FROM dictionary_words
        WHERE id = $id
        """

        return self._fetch_one(query, {'$id': word_id})

    def get_words_by_training_step(self, user_id: int, step: int) -> List[Dict]:
        """
        Get words for training by step number (8-step algorithm)

        Args:
            user_id: User ID
            step: Step number (1-8)

        Returns:
            List of words for the given step
        """
        if step == 1:
            # Шаг 1: Новое слово, добавленное последним
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id AND status = 'new'
            ORDER BY added_at DESC
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        elif step == 2:
            # Шаг 2: Слово learning по давности повтора
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id AND status = 'learning'
            ORDER BY COALESCE(last_reviewed_at, added_at) ASC
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        elif step == 3 or step == 7:
            # Шаг 3 и 7: Новое слово, добавленное давнее всего
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id AND status = 'new'
            ORDER BY added_at ASC
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        elif step == 4 or step == 6:
            # Шаг 4 и 6: Learning с макс рейтингом (рандомно)
            # Сортируем по рейтингу DESC, затем RANDOM() для случайного выбора среди одинаковых
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id
              AND status = 'learning'
            ORDER BY COALESCE(rating, 0) DESC, Random(TableRow())
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        elif step == 5:
            # Шаг 5: Слово, обнулившее рейтинг последним
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id
              AND status = 'learning'
              AND COALESCE(rating, 0) = 0
              AND last_rating_change IS NOT NULL
            ORDER BY last_rating_change DESC
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        elif step == 8:
            # Шаг 8: Рандомное выученное слово
            query = """
            DECLARE $user_id AS Uint64?;

            SELECT *
            FROM dictionary_words
            WHERE user_id = $user_id AND status = 'learned'
            ORDER BY Random(TableRow())
            LIMIT 1
            """
            return self._fetch_all(query, {'$user_id': user_id})

        else:
            return []

    def get_translation_for_word(self, word_id: int) -> str:
        """Get first translation for a word"""
        query = """
        DECLARE $word_id AS Uint64?;

        SELECT translation
        FROM dictionary_translations
        WHERE word_id = $word_id
        LIMIT 1
        """

        result = self._fetch_one(query, {'$word_id': word_id})
        return result['translation'] if result else ""

    def get_random_translations(self, user_id: int, exclude_translation: str, limit: int = 3) -> List[str]:
        """Get random translations from user's dictionary (for fallback test options)"""
        query = f"""
        DECLARE $user_id AS Uint64?;
        DECLARE $exclude AS Utf8?;

        SELECT DISTINCT dt.translation
        FROM dictionary_translations dt
        JOIN dictionary_words dw ON dt.word_id = dw.id
        WHERE dw.user_id = $user_id
          AND dt.translation != $exclude
        ORDER BY Random(TableRow())
        LIMIT {limit}
        """

        results = self._fetch_all(query, {
            '$user_id': user_id,
            '$exclude': exclude_translation
        })
        return [r['translation'] for r in results]

    def get_random_words_excluding(self, user_id: int, exclude_ids: List[int], limit: int = 8) -> List[Dict]:
        """
        Get random words excluding specific IDs

        Args:
            user_id: User ID
            exclude_ids: List of word IDs to exclude
            limit: Maximum number of words to return

        Returns:
            List of random words
        """
        if not exclude_ids:
            exclude_ids = [0]  # Dummy value to avoid empty list

        # YDB doesn't support IN with lists directly in DECLARE, so we use a different approach
        # Build the query dynamically with the exclude list
        exclude_str = ', '.join([str(id) for id in exclude_ids])

        query = f"""
        DECLARE $user_id AS Uint64?;

        SELECT *
        FROM dictionary_words
        WHERE user_id = $user_id
          AND id NOT IN ({exclude_str})
        ORDER BY Random(TableRow())
        LIMIT {limit}
        """

        return self._fetch_all(query, {'$user_id': user_id})

    # ====================
    # User/Auth Methods
    # ====================

    def link_telegram_to_user(self, user_id: int, telegram_id: int) -> bool:
        """
        Link Telegram ID to existing user account

        Args:
            user_id: Internal user ID
            telegram_id: Telegram user ID

        Returns:
            True if successful
        """
        query = """
        DECLARE $user_id AS Uint64?;
        DECLARE $telegram_id AS Uint64?;

        UPDATE users
        SET telegram_id = $telegram_id
        WHERE id = $user_id
        """

        try:
            self._execute_query(query, {
                '$user_id': user_id,
                '$telegram_id': telegram_id
            })
            logger.info(f"[YDB] Linked telegram_id={telegram_id} to user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"[YDB] Error linking telegram: {e}")
            return False

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        query = """
        DECLARE $telegram_id AS Uint64?;

        SELECT *
        FROM users
        WHERE telegram_id = $telegram_id
        """

        return self._fetch_one(query, {'$telegram_id': telegram_id})

    def ensure_test_users_exist(self):
        """
        Ensure test users exist in the database
        Called on startup to create test accounts if they don't exist
        """
        test_accounts = [
            {'id': 1, 'username': 'andrew'},
            {'id': 2, 'username': 'friend1'},
            {'id': 3, 'username': 'friend2'},
        ]

        for account in test_accounts:
            # Check if user exists
            check_query = """
            DECLARE $id AS Uint64?;

            SELECT id FROM users WHERE id = $id
            """
            existing = self._fetch_one(check_query, {'$id': account['id']})

            if not existing:
                # Create user
                insert_query = """
                DECLARE $id AS Uint64?;
                DECLARE $username AS Utf8?;
                DECLARE $created_at AS Utf8?;

                UPSERT INTO users (id, username, created_at)
                VALUES ($id, $username, $created_at)
                """
                self._execute_query(insert_query, {
                    '$id': account['id'],
                    '$username': account['username'],
                    '$created_at': datetime.now().isoformat()
                })
                logger.info(f"[YDB] Created test user: {account['username']} (id={account['id']})")

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'driver'):
            self.driver.stop()
