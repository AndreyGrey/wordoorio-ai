#!/usr/bin/env python3
"""
YDB Database Manager for Wordoorio
Manages all database operations using Yandex Database (YDB)
"""

import ydb
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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
        # Use MetadataUrlCredentials for serverless containers
        # This automatically uses the service account attached to the container
        driver_config = ydb.DriverConfig(
            endpoint=self.endpoint,
            database=self.database,
            credentials=ydb.iam.MetadataUrlCredentials()
        )

        self.driver = ydb.Driver(driver_config)
        self.driver.wait(fail_fast=True, timeout=5)

        # Create session pool for efficient connection reuse
        self.pool = ydb.SessionPool(self.driver)

    def _execute_query(self, query: str, parameters: Dict = None):
        """
        Execute YQL query with automatic retries

        Args:
            query: YQL query string
            parameters: Query parameters as dict

        Returns:
            Query result
        """
        def callee(session):
            return session.transaction().execute(
                query,
                parameters or {},
                commit_tx=True
            )

        return self.pool.retry_operation_sync(callee)

    def _fetch_one(self, query: str, parameters: Dict = None) -> Optional[Dict]:
        """Execute query and return first row as dict"""
        result = self._execute_query(query, parameters)

        if not result or not result[0].rows:
            return None

        row = result[0].rows[0]
        return {col: getattr(row, col) for col in result[0].columns}

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

    # ====================
    # Analysis Methods
    # ====================

    def save_analysis(self,
                     original_text: str,
                     analysis_result: Dict,
                     session_id: Optional[str] = None,
                     ip_address: Optional[str] = None) -> int:
        """
        Save text analysis results to database

        Args:
            original_text: Original input text
            analysis_result: Analysis results with highlights
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
        UPSERT INTO analyses (id, original_text, analysis_date, total_highlights, total_words, session_id, ip_address)
        VALUES ($id, $original_text, CurrentUtcTimestamp(), $total_highlights, $total_words, $session_id, $ip_address)
        """

        self._execute_query(query, {
            '$id': analysis_id,
            '$original_text': original_text,
            '$total_highlights': total_highlights,
            '$total_words': total_words,
            '$session_id': session_id,
            '$ip_address': ip_address
        })

        # Insert highlights
        for highlight in highlights:
            highlight_id = self._get_next_id('highlights')

            highlight_query = """
            UPSERT INTO highlights (id, analysis_id, highlight_word, context, highlight_translation, dictionary_meanings)
            VALUES ($id, $analysis_id, $highlight_word, $context, $highlight_translation, $dictionary_meanings)
            """

            self._execute_query(highlight_query, {
                '$id': highlight_id,
                '$analysis_id': analysis_id,
                '$highlight_word': highlight.get('word', ''),
                '$context': highlight.get('context', ''),
                '$highlight_translation': highlight.get('translation', ''),
                '$dictionary_meanings': str(highlight.get('meanings', []))
            })

        logger.info(f"[YDB] Saved analysis {analysis_id} with {total_highlights} highlights")
        return analysis_id

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
        SELECT *
        FROM analyses
        WHERE id = $id
        """

        analysis = self._fetch_one(analysis_query, {'$id': analysis_id})

        if not analysis:
            return None

        # Get highlights
        highlights_query = """
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
        SELECT *
        FROM tests
        WHERE id = $id
        """

        return self._fetch_one(query, {'$id': test_id})

    def delete_test(self, test_id: int):
        """Delete test by ID"""
        query = """
        DELETE FROM tests
        WHERE id = $id
        """

        self._execute_query(query, {'$id': test_id})

    def get_pending_tests(self, user_id: int) -> List[Dict]:
        """Get all pending tests for user"""
        query = """
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
        SELECT *
        FROM dictionary_words
        WHERE id = $id
        """

        return self._fetch_one(query, {'$id': word_id})

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'driver'):
            self.driver.stop()
