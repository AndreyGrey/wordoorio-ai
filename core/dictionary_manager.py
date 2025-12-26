#!/usr/bin/env python3
"""
📖 DICTIONARY MANAGER

Управление персональным словарем пользователя.
Добавление, получение, удаление слов и фраз для изучения.

@version 1.0.0
@author Wordoorio Team
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class DictionaryManager:
    """Менеджер персонального словаря"""

    def __init__(self, db_path: str = "wordoorio.db"):
        """
        Инициализация менеджера словаря

        Args:
            db_path: Путь к базе данных SQLite
        """
        self.db_path = db_path

        # S3 configuration
        self.s3_enabled = all([
            os.getenv('AWS_ACCESS_KEY_ID'),
            os.getenv('AWS_SECRET_ACCESS_KEY'),
            os.getenv('S3_BUCKET')
        ])

        if self.s3_enabled:
            self.s3_bucket = os.getenv('S3_BUCKET')
            self.s3_endpoint = os.getenv('S3_ENDPOINT', 'https://storage.yandexcloud.net')
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.s3_endpoint,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info(f"[DICTIONARY] S3 синхронизация включена: {self.s3_bucket}")
        else:
            logger.warning("[DICTIONARY] S3 синхронизация отключена")

    def _upload_to_s3(self):
        """
        Загрузить БД в S3

        Вызывается после каждого изменения данных.
        """
        if not self.s3_enabled:
            return

        try:
            self.s3_client.upload_file(
                Filename=self.db_path,
                Bucket=self.s3_bucket,
                Key=self.db_path
            )
            logger.info(f"[DICTIONARY] БД загружена в S3: s3://{self.s3_bucket}/{self.db_path}")
        except Exception as e:
            logger.error(f"[DICTIONARY] Ошибка загрузки в S3: {e}")

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
        lemma = highlight_dict['highlight']
        word_type = highlight_dict.get('type', 'word')
        main_translation = highlight_dict['highlight_translation']
        context = highlight_dict['context']
        additional_meanings = highlight_dict.get('dictionary_meanings', [])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Проверяем: есть ли слово с такой lemma?
            cursor.execute("""
                SELECT id FROM dictionary_words
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (lemma, user_id, user_id))

            existing = cursor.fetchone()
            now = datetime.now().isoformat()

            if existing:
                # Слово уже есть - добавляем новый перевод и пример
                word_id = existing[0]

                # Добавляем основной перевод (если еще нет)
                cursor.execute("""
                    SELECT COUNT(*) FROM dictionary_translations
                    WHERE word_id = ? AND translation = ?
                """, (word_id, main_translation))

                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO dictionary_translations
                        (word_id, translation, source_session_id, added_at)
                        VALUES (?, ?, ?, ?)
                    """, (word_id, main_translation, session_id, now))

                # Добавляем дополнительные переводы
                for meaning in additional_meanings:
                    cursor.execute("""
                        SELECT COUNT(*) FROM dictionary_translations
                        WHERE word_id = ? AND translation = ?
                    """, (word_id, meaning))

                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO dictionary_translations
                            (word_id, translation, source_session_id, added_at)
                            VALUES (?, ?, ?, ?)
                        """, (word_id, meaning, session_id, now))

                # Добавляем новый пример использования
                cursor.execute("""
                    INSERT INTO dictionary_examples
                    (word_id, original_form, context, session_id, added_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (word_id, lemma, context, session_id, now))

                conn.commit()
                self._upload_to_s3()

                return {
                    'success': True,
                    'is_new': False,
                    'word_id': word_id,
                    'message': f'Добавлен новый пример к слову "{lemma}"'
                }

            else:
                # Новое слово - создаем запись
                cursor.execute("""
                    INSERT INTO dictionary_words
                    (user_id, lemma, type, status, added_at)
                    VALUES (?, ?, ?, 'new', ?)
                """, (user_id, lemma, word_type, now))

                word_id = cursor.lastrowid

                # Добавляем основной перевод
                cursor.execute("""
                    INSERT INTO dictionary_translations
                    (word_id, translation, source_session_id, added_at)
                    VALUES (?, ?, ?, ?)
                """, (word_id, main_translation, session_id, now))

                # Добавляем дополнительные переводы
                for meaning in additional_meanings:
                    cursor.execute("""
                        INSERT INTO dictionary_translations
                        (word_id, translation, source_session_id, added_at)
                        VALUES (?, ?, ?, ?)
                    """, (word_id, meaning, session_id, now))

                # Добавляем первый пример использования
                cursor.execute("""
                    INSERT INTO dictionary_examples
                    (word_id, original_form, context, session_id, added_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (word_id, lemma, context, session_id, now))

                conn.commit()
                self._upload_to_s3()

                return {
                    'success': True,
                    'is_new': True,
                    'word_id': word_id,
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
                'lemma': 'give up',
                'type': 'expression',
                'status': 'new',
                'added_at': '2024-12-09T10:00:00',
                'translations': [
                    {
                        'text': 'сдаться',
                        'source_session_id': 'session_123',
                        'added_at': '2024-12-09T10:00:00'
                    }
                ],
                'examples': [
                    {
                        'original_form': 'gave up',
                        'context': 'He never gave up on his dreams',
                        'session_id': 'session_123',
                        'added_at': '2024-12-09T10:00:00'
                    }
                ]
            }
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Получаем основную информацию о слове
            cursor.execute("""
                SELECT id, type, status, added_at, last_reviewed_at, review_count, correct_streak
                FROM dictionary_words
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (lemma, user_id, user_id))

            word_row = cursor.fetchone()
            if not word_row:
                return None

            word_id = word_row[0]

            # Получаем переводы
            cursor.execute("""
                SELECT translation, source_session_id, added_at
                FROM dictionary_translations
                WHERE word_id = ?
                ORDER BY added_at ASC
            """, (word_id,))

            translations = [
                {
                    'text': row[0],
                    'source_session_id': row[1],
                    'added_at': row[2]
                }
                for row in cursor.fetchall()
            ]

            # Получаем примеры
            cursor.execute("""
                SELECT original_form, context, session_id, added_at
                FROM dictionary_examples
                WHERE word_id = ?
                ORDER BY added_at ASC
            """, (word_id,))

            examples = [
                {
                    'original_form': row[0],
                    'context': row[1],
                    'session_id': row[2],
                    'added_at': row[3]
                }
                for row in cursor.fetchall()
            ]

            return {
                'lemma': lemma,
                'type': word_row[1],
                'status': word_row[2],
                'added_at': word_row[3],
                'last_reviewed_at': word_row[4],
                'review_count': word_row[5],
                'correct_streak': word_row[6],
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
                    'lemma': 'give up',
                    'type': 'expression',
                    'translations': ['сдаться', 'бросить'],
                    'examples_count': 3,
                    'status': 'new',
                    'added_at': '2024-12-09T10:00:00'
                }
            ]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Получаем все слова
            cursor.execute("""
                SELECT id, lemma, type, status, added_at
                FROM dictionary_words
                WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)
                ORDER BY added_at DESC
            """, (user_id, user_id))

            words = []
            for row in cursor.fetchall():
                word_id, lemma, word_type, status, added_at = row

                # Получаем переводы
                cursor.execute("""
                    SELECT translation FROM dictionary_translations
                    WHERE word_id = ?
                    ORDER BY added_at ASC
                """, (word_id,))
                translations = [t[0] for t in cursor.fetchall()]

                # Получаем количество примеров
                cursor.execute("""
                    SELECT COUNT(*) FROM dictionary_examples
                    WHERE word_id = ?
                """, (word_id,))
                examples_count = cursor.fetchone()[0]

                words.append({
                    'lemma': lemma,
                    'type': word_type,
                    'translations': translations,
                    'examples_count': examples_count,
                    'status': status,
                    'added_at': added_at
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM dictionary_words
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (lemma, user_id, user_id))

            if cursor.rowcount > 0:
                conn.commit()
                self._upload_to_s3()
                return {
                    'success': True,
                    'message': f'Слово "{lemma}" удалено из словаря'
                }
            else:
                return {
                    'success': False,
                    'message': f'Слово "{lemma}" не найдено в словаре'
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Общее количество слов
            cursor.execute("""
                SELECT COUNT(*) FROM dictionary_words
                WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL)) AND type = 'word'
            """, (user_id, user_id))
            total_words = cursor.fetchone()[0]

            # Общее количество фраз
            cursor.execute("""
                SELECT COUNT(*) FROM dictionary_words
                WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL)) AND type = 'expression'
            """, (user_id, user_id))
            total_phrases = cursor.fetchone()[0]

            # Разбивка по статусам
            cursor.execute("""
                SELECT status, COUNT(*) FROM dictionary_words
                WHERE user_id = ? OR (user_id IS NULL AND ? IS NULL)
                GROUP BY status
            """, (user_id, user_id))

            status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

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

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE dictionary_words
                SET status = ?
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (status, lemma, user_id, user_id))

            if cursor.rowcount > 0:
                conn.commit()
                self._upload_to_s3()
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
                'correct_streak': int,
                'message': str
            }
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Получаем текущую статистику
            cursor.execute("""
                SELECT correct_streak, review_count, status
                FROM dictionary_words
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (lemma, user_id, user_id))

            word_row = cursor.fetchone()
            if not word_row:
                return {
                    'success': False,
                    'message': f'Слово "{lemma}" не найдено в словаре'
                }

            current_streak = word_row[0]
            review_count = word_row[1]
            current_status = word_row[2]

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

            cursor.execute("""
                UPDATE dictionary_words
                SET
                    correct_streak = ?,
                    review_count = review_count + 1,
                    last_reviewed_at = ?,
                    status = ?
                WHERE lemma = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
            """, (new_streak, now, new_status, lemma, user_id, user_id))

            conn.commit()
            self._upload_to_s3()

            return {
                'success': True,
                'new_status': new_status,
                'correct_streak': new_streak,
                'message': f'Статистика обновлена. Серия: {new_streak}'
            }


# Для тестирования
if __name__ == '__main__':
    print("🧪 ТЕСТ DICTIONARY MANAGER")
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
