#!/usr/bin/env python3
"""
TrainingService - сервис для отбора слов для тренировки
Реализует 8-шаговый алгоритм отбора слов (YDB версия)
"""

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
        current_position = state.get('last_selection_position', 1) or 1
        logger.info(f"[TrainingService] user_id={user_id}, текущая позиция: {current_position}, нужно слов: {count}")

        selected_words = []
        position = current_position
        iterations = 0
        max_iterations = 20  # Защита от бесконечного цикла

        # Продолжаем отбирать, пока не наберем нужное количество
        while len(selected_words) < count and iterations < max_iterations:
            iterations += 1
            # Получаем слова по текущему шагу через YDB
            step_words = self.db.get_words_by_training_step(user_id, position)
            logger.info(f"[TrainingService] Шаг {position}: найдено {len(step_words)} слов")

            # Добавляем слова, избегая дубликатов
            for word in step_words:
                if len(selected_words) >= count:
                    break
                # Проверяем, что слово еще не добавлено
                if not any(w['id'] == word['id'] for w in selected_words):
                    # Нормализуем rating (может быть None)
                    word['rating'] = word.get('rating') or 0
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
        self.db.update_training_position(user_id, position)

        return selected_words

    def get_translation_for_word(self, word_id: int) -> str:
        """
        Получить перевод для слова

        Args:
            word_id: ID слова

        Returns:
            Перевод слова (первый из списка)
        """
        return self.db.get_translation_for_word(word_id)
