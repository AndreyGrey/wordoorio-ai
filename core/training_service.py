#!/usr/bin/env python3
"""
TrainingService - сервис для отбора слов для тренировки
Реализует 8-шаговый алгоритм отбора слов
"""

import sqlite3
import logging
from typing import List, Dict
from database import WordoorioDatabase

logger = logging.getLogger(__name__)


class TrainingService:
    """Сервис для отбора слов для тренировки"""

    def __init__(self, db: WordoorioDatabase):
        self.db = db

    def select_words_for_training(self, user_id: int, count: int = 8) -> List[Dict]:
        """
        Отбор N слов для тренировки по 8-шаговому алгоритму

        Args:
            user_id: ID пользователя
            count: Количество слов для отбора (по умолчанию 8)

        Returns:
            Список словарей со словами для тренировки

        Алгоритм:
            1. Новое слово, добавленное последним
            2. Слово в процессе обучения (по давности повтора)
            3. Новое слово, добавленное давнее всего
            4. Слово learning с максимальной оценкой (рандомно)
            5. Слово, обнулившее оценку последней
            6. Слово learning с максимальной оценкой (дубликат шага 4)
            7. Новое слово, добавленное давнее всего (дубликат шага 3)
            8. Рандомное слово из выученных
        """
        # Получаем текущую позицию в алгоритме
        state = self.db.get_user_training_state(user_id)
        current_position = state['last_selection_position']
        logger.info(f"[TrainingService] user_id={user_id}, текущая позиция: {current_position}, нужно слов: {count}")

        selected_words = []
        position = current_position
        iterations = 0
        max_iterations = 20  # Защита от бесконечного цикла

        # Продолжаем отбирать, пока не наберем нужное количество
        while len(selected_words) < count and iterations < max_iterations:
            iterations += 1
            # Получаем слова по текущему шагу
            step_words = self._get_words_by_step(user_id, position)
            logger.info(f"[TrainingService] Шаг {position}: найдено {len(step_words)} слов")

            # Добавляем слова, избегая дубликатов
            for word in step_words:
                if len(selected_words) >= count:
                    break
                # Проверяем, что слово еще не добавлено
                if not any(w['id'] == word['id'] for w in selected_words):
                    selected_words.append(word)
                    logger.info(f"[TrainingService] Добавлено слово: {word.get('lemma', '?')} (status={word.get('status', '?')})")

            # Переходим к следующему шагу (циклически)
            position = (position % 8) + 1

            # Защита от бесконечного цикла (если слов вообще нет)
            if position == current_position and not step_words:
                logger.warning(f"[TrainingService] Прошли полный цикл, но слов не найдено. Выход.")
                break

        logger.info(f"[TrainingService] Итого отобрано {len(selected_words)} слов за {iterations} итераций")

        # Сохраняем новую позицию
        new_position = position
        self.db.update_training_position(user_id, new_position)

        return selected_words

    def _get_words_by_step(self, user_id: int, step: int) -> List[Dict]:
        """
        Получить слова по конкретному шагу алгоритма

        Args:
            user_id: ID пользователя
            step: Номер шага (1-8)

        Returns:
            Список слов для данного шага
        """
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if step == 1:
                # Шаг 1: Новое слово, добавленное последним
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'new'
                    ORDER BY added_at DESC
                    LIMIT 1
                """, (user_id,))

            elif step == 2:
                # Шаг 2: Слово в процессе обучения (по давности повтора)
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'learning'
                    ORDER BY COALESCE(last_reviewed_at, added_at) ASC
                    LIMIT 1
                """, (user_id,))

            elif step == 3 or step == 7:
                # Шаг 3 и 7: Новое слово, добавленное давнее всего
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'new'
                    ORDER BY added_at ASC
                    LIMIT 1
                """, (user_id,))

            elif step == 4 or step == 6:
                # Шаг 4 и 6: Слово learning с максимальной оценкой (рандомно среди равных)
                # Сначала находим максимальный рейтинг
                cursor.execute("""
                    SELECT MAX(COALESCE(rating, 0)) as max_rating
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'learning'
                """, (user_id,))

                row = cursor.fetchone()
                max_rating = row['max_rating'] if row and row['max_rating'] is not None else 0

                # Берем все слова с этим рейтингом и рандомизируем
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'learning' AND COALESCE(rating, 0) = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (user_id, max_rating))

            elif step == 5:
                # Шаг 5: Слово, обнулившее оценку последней
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'learning'
                          AND COALESCE(rating, 0) = 0
                          AND last_rating_change IS NOT NULL
                    ORDER BY last_rating_change DESC
                    LIMIT 1
                """, (user_id,))

            elif step == 8:
                # Шаг 8: Рандомное слово из выученных
                cursor.execute("""
                    SELECT id, user_id, lemma, type, status, added_at,
                           last_reviewed_at, review_count, correct_streak, rating, last_rating_change
                    FROM dictionary_words
                    WHERE user_id = ? AND status = 'learned'
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (user_id,))

            else:
                return []

            # Конвертируем результаты в список словарей
            rows = cursor.fetchall()
            words = []
            for row in rows:
                words.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'lemma': row['lemma'],
                    'type': row['type'],
                    'status': row['status'],
                    'added_at': row['added_at'],
                    'last_reviewed_at': row['last_reviewed_at'],
                    'review_count': row['review_count'],
                    'correct_streak': row['correct_streak'],
                    'rating': row['rating'] or 0,
                    'last_rating_change': row['last_rating_change']
                })

            return words

    def get_translation_for_word(self, word_id: int) -> str:
        """
        Получить перевод для слова

        Args:
            word_id: ID слова

        Returns:
            Перевод слова (первый из списка)
        """
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT translation
                FROM dictionary_translations
                WHERE word_id = ?
                LIMIT 1
            """, (word_id,))

            row = cursor.fetchone()
            return row[0] if row else ""
