"""
Модуль для работы с базой данных Wordoorio
Сохраняет историю анализов текстов и результатов
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class WordoorioDatabase:
    def __init__(self, db_path: str = "wordoorio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица для сохранения анализов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_highlights INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    session_id TEXT,
                    ip_address TEXT
                )
            """)
            
            # Таблица для сохранения найденных хайлайтов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS highlights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    highlight_word TEXT NOT NULL,
                    context TEXT NOT NULL,
                    highlight_translation TEXT NOT NULL,
                    dictionary_meanings TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
            """)
            
            # Индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analyses(analysis_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_highlight_word ON highlights(highlight_word)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_id ON highlights(analysis_id)")

            # ===== ЛИЧНЫЙ СЛОВАРЬ =====

            # Таблица слов в словаре
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT NULL,
                    lemma TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    added_at TEXT NOT NULL,
                    last_reviewed_at TEXT,
                    review_count INTEGER DEFAULT 0,
                    correct_streak INTEGER DEFAULT 0,
                    UNIQUE(user_id, lemma)
                )
            """)

            # Таблица переводов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary_translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    translation TEXT NOT NULL,
                    source_session_id TEXT,
                    added_at TEXT NOT NULL,
                    FOREIGN KEY (word_id) REFERENCES dictionary_words(id) ON DELETE CASCADE
                )
            """)

            # Таблица примеров использования
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary_examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    original_form TEXT NOT NULL,
                    context TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    FOREIGN KEY (word_id) REFERENCES dictionary_words(id) ON DELETE CASCADE
                )
            """)

            # Индексы для словаря
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_lemma ON dictionary_words(lemma)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_user ON dictionary_words(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_status ON dictionary_words(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_word_id ON dictionary_translations(word_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_examples_word_id ON dictionary_examples(word_id)")

            # ===== TELEGRAM USERS =====

            # Таблица пользователей Telegram
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    photo_url TEXT,
                    auth_date INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT NOT NULL
                )
            """)

            # Индекс для быстрого поиска по telegram_id
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")

            # ===== СИСТЕМА ТРЕНИРОВКИ =====

            # Добавляем поля rating и last_rating_change в dictionary_words (миграция)
            try:
                cursor.execute("ALTER TABLE dictionary_words ADD COLUMN rating INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует

            try:
                cursor.execute("ALTER TABLE dictionary_words ADD COLUMN last_rating_change TEXT")
            except sqlite3.OperationalError:
                pass  # Колонка уже существует

            # Таблица состояния тренировки пользователя
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_training_state (
                    user_id INTEGER PRIMARY KEY,
                    last_selection_position INTEGER DEFAULT 1,
                    last_training_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Таблица тестов (удаляются после ответа)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    correct_translation TEXT NOT NULL,
                    wrong_option_1 TEXT NOT NULL,
                    wrong_option_2 TEXT NOT NULL,
                    wrong_option_3 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (word_id) REFERENCES dictionary_words(id)
                )
            """)

            # Таблица статистики тестов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS word_test_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    total_tests INTEGER DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    wrong_answers INTEGER DEFAULT 0,
                    last_test_at TEXT,
                    last_result BOOLEAN,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (word_id) REFERENCES dictionary_words(id),
                    UNIQUE(user_id, word_id)
                )
            """)

            # Индексы для тренировочной системы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tests_user ON tests(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_user_word ON word_test_statistics(user_id, word_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_rating ON dictionary_words(rating)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_last_rating_change ON dictionary_words(last_rating_change)")

            conn.commit()
    
    def save_analysis(self, 
                     original_text: str, 
                     highlights: List[Dict], 
                     stats: Dict,
                     session_id: str = None,
                     ip_address: str = None) -> int:
        """
        Сохранение результата анализа в базу данных
        
        Args:
            original_text: Исходный текст для анализа
            highlights: Список найденных хайлайтов
            stats: Статистика анализа (total_highlights, total_words)
            session_id: ID сессии пользователя
            ip_address: IP адрес пользователя
            
        Returns:
            ID созданного анализа
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Сохраняем основную запись анализа
            # Убираем переносы строк для компактного отображения
            cleaned_text = original_text.replace('\n', ' ').replace('\r', ' ')
            # Убираем множественные пробелы
            cleaned_text = ' '.join(cleaned_text.split())
            
            cursor.execute("""
                INSERT INTO analyses 
                (original_text, total_highlights, total_words, session_id, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cleaned_text,
                stats.get('total_highlights', 0),
                stats.get('total_words', 0),
                session_id,
                ip_address
            ))
            
            analysis_id = cursor.lastrowid
            
            # Сохраняем каждый хайлайт
            for highlight in highlights:
                cursor.execute("""
                    INSERT INTO highlights
                    (analysis_id, highlight_word, context, highlight_translation, dictionary_meanings)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    highlight['highlight'],
                    highlight['context'],
                    highlight['highlight_translation'],
                    json.dumps(highlight.get('dictionary_meanings', []))
                ))
            
            conn.commit()
            return analysis_id
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Получение последних анализов"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, original_text, analysis_date, total_highlights, total_words
                FROM analyses 
                ORDER BY analysis_date DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'original_text': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                    'analysis_date': row[2],
                    'total_highlights': row[3],
                    'total_words': row[4]
                })
            
            return results
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Получение полного анализа по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем основную информацию
            cursor.execute("""
                SELECT original_text, analysis_date, total_highlights, total_words
                FROM analyses 
                WHERE id = ?
            """, (analysis_id,))
            
            analysis_row = cursor.fetchone()
            if not analysis_row:
                return None
            
            # Получаем хайлайты
            cursor.execute("""
                SELECT highlight_word, context, highlight_translation, dictionary_meanings
                FROM highlights
                WHERE analysis_id = ?
            """, (analysis_id,))

            highlights = []
            for row in cursor.fetchall():
                highlights.append({
                    'highlight': row[0],
                    'context': row[1],
                    'highlight_translation': row[2],
                    'dictionary_meanings': json.loads(row[3]) if row[3] else []
                })
            
            return {
                'id': analysis_id,
                'original_text': analysis_row[0],
                'analysis_date': analysis_row[1],
                'stats': {
                    'total_highlights': analysis_row[2],
                    'total_words': analysis_row[3]
                },
                'highlights': highlights
            }
    
    def search_by_word(self, word: str, limit: int = 20) -> List[Dict]:
        """Поиск анализов по конкретному слову"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT a.id, a.original_text, a.analysis_date, h.highlight_word, h.context
                FROM analyses a
                JOIN highlights h ON a.id = h.analysis_id
                WHERE h.highlight_word LIKE ?
                ORDER BY a.analysis_date DESC
                LIMIT ?
            """, (f'%{word}%', limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'analysis_id': row[0],
                    'text_preview': row[1][:80] + '...' if len(row[1]) > 80 else row[1],
                    'date': row[2],
                    'highlight_word': row[3],
                    'context': row[4]
                })
            
            return results
    
    def get_stats(self) -> Dict:
        """Получение общей статистики"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Общее количество анализов
            cursor.execute("SELECT COUNT(*) FROM analyses")
            total_analyses = cursor.fetchone()[0]
            
            # Общее количество хайлайтов
            cursor.execute("SELECT COUNT(*) FROM highlights")
            total_highlights = cursor.fetchone()[0]
            
            # Самые популярные слова
            cursor.execute("""
                SELECT highlight_word, COUNT(*) as count
                FROM highlights 
                GROUP BY highlight_word 
                ORDER BY count DESC 
                LIMIT 10
            """)
            popular_words = [{'word': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return {
                'total_analyses': total_analyses,
                'total_highlights': total_highlights,
                'popular_words': popular_words
            }

    # ===== МЕТОДЫ ДЛЯ ТРЕНИРОВОЧНОЙ СИСТЕМЫ =====

    def get_user_training_state(self, user_id: int) -> Dict:
        """Получить состояние тренировки пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_selection_position, last_training_at
                FROM user_training_state
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'last_selection_position': row[0],
                    'last_training_at': row[1]
                }
            else:
                # Создаем начальное состояние
                cursor.execute("""
                    INSERT INTO user_training_state (user_id, last_selection_position)
                    VALUES (?, 1)
                """, (user_id,))
                conn.commit()
                return {
                    'last_selection_position': 1,
                    'last_training_at': None
                }

    def update_training_position(self, user_id: int, position: int):
        """Обновить позицию в алгоритме отбора"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO user_training_state (user_id, last_selection_position, last_training_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_selection_position = excluded.last_selection_position,
                    last_training_at = excluded.last_training_at
            """, (user_id, position, now))
            conn.commit()

    def insert_test(self, user_id: int, word_id: int, word: str,
                    correct_translation: str, wrong_option_1: str,
                    wrong_option_2: str, wrong_option_3: str) -> int:
        """Создать тест"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO tests (user_id, word_id, word, correct_translation,
                                 wrong_option_1, wrong_option_2, wrong_option_3, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, word_id, word, correct_translation,
                  wrong_option_1, wrong_option_2, wrong_option_3, now))
            conn.commit()
            return cursor.lastrowid

    def get_test(self, test_id: int) -> Optional[Dict]:
        """Получить тест по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, word_id, word, correct_translation,
                       wrong_option_1, wrong_option_2, wrong_option_3, created_at
                FROM tests
                WHERE id = ?
            """, (test_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'word_id': row[2],
                    'word': row[3],
                    'correct_translation': row[4],
                    'wrong_option_1': row[5],
                    'wrong_option_2': row[6],
                    'wrong_option_3': row[7],
                    'created_at': row[8]
                }
            return None

    def delete_test(self, test_id: int):
        """Удалить тест"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tests WHERE id = ?", (test_id,))
            conn.commit()

    def get_pending_tests(self, user_id: int) -> List[Dict]:
        """Получить все нерешенные тесты пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, word_id, word, correct_translation,
                       wrong_option_1, wrong_option_2, wrong_option_3, created_at
                FROM tests
                WHERE user_id = ?
                ORDER BY created_at ASC
            """, (user_id,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'word_id': row[1],
                    'word': row[2],
                    'correct_translation': row[3],
                    'wrong_option_1': row[4],
                    'wrong_option_2': row[5],
                    'wrong_option_3': row[6],
                    'created_at': row[7]
                })
            return results

    def update_word_rating(self, word_id: int, rating: int, last_rating_change: str = None):
        """Обновить рейтинг слова"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if last_rating_change is None:
                last_rating_change = datetime.now().isoformat()

            cursor.execute("""
                UPDATE dictionary_words
                SET rating = ?, last_rating_change = ?, last_reviewed_at = ?
                WHERE id = ?
            """, (rating, last_rating_change, datetime.now().isoformat(), word_id))
            conn.commit()

    def update_word_status(self, word_id: int, status: str):
        """Обновить статус слова"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dictionary_words
                SET status = ?, last_reviewed_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), word_id))
            conn.commit()

    def update_word_statistics(self, user_id: int, word_id: int, is_correct: bool):
        """Обновить статистику тестов слова"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO word_test_statistics
                (user_id, word_id, total_tests, correct_answers, wrong_answers, last_test_at, last_result)
                VALUES (?, ?, 1, ?, ?, ?, ?)
                ON CONFLICT(user_id, word_id) DO UPDATE SET
                    total_tests = total_tests + 1,
                    correct_answers = correct_answers + ?,
                    wrong_answers = wrong_answers + ?,
                    last_test_at = excluded.last_test_at,
                    last_result = excluded.last_result
            """, (
                user_id, word_id,
                1 if is_correct else 0,
                1 if not is_correct else 0,
                now,
                is_correct,
                1 if is_correct else 0,
                1 if not is_correct else 0
            ))
            conn.commit()

    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """Получить слово по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, lemma, type, status, added_at,
                       last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                FROM dictionary_words
                WHERE id = ?
            """, (word_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'lemma': row[2],
                    'type': row[3],
                    'status': row[4],
                    'added_at': row[5],
                    'last_reviewed_at': row[6],
                    'review_count': row[7],
                    'correct_streak': row[8],
                    'rating': row[9] or 0,
                    'last_rating_change': row[10]
                }
            return None