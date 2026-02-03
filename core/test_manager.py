#!/usr/bin/env python3
"""
TestManager - менеджер для создания и управления тестами
Работает с YandexAIClient для генерации вариантов ответов (YDB версия)
"""

import random
import logging
from typing import List, Dict
from datetime import datetime
from database import WordoorioDatabase
from core.yandex_ai_client import YandexAIClient

logger = logging.getLogger(__name__)


class TestManager:
    """Менеджер для создания и управления тестами"""

    def __init__(self, db: WordoorioDatabase, ai_client: YandexAIClient):
        self.db = db
        self.ai_client = ai_client

    async def create_tests_batch(self, user_id: int, words: List[Dict]) -> List[int]:
        """
        Создать пакет тестов для списка слов

        Args:
            user_id: ID пользователя
            words: Список словарей со словами (из TrainingService)

        Returns:
            Список ID созданных тестов

        Процесс:
            1. Получить переводы для слов из БД
            2. Вызвать YandexAIClient.generate_test_options()
            3. Сохранить тесты в таблицу tests
            4. Вернуть список test_ids
        """
        if not words:
            return []

        # 1. Подготовка данных для AI
        words_data = []
        for word in words:
            translation = self.db.get_translation_for_word(word['id'])
            if translation:
                words_data.append({
                    'word': word['lemma'],
                    'correct_translation': translation,
                    'word_id': word['id']  # Сохраняем для использования позже
                })

        if not words_data:
            logger.warning("[TestManager] Нет слов с переводами для создания тестов")
            return []

        # 2. Запрос к AI (async)
        try:
            # Готовим данные для API (без word_id)
            ai_input = [{'word': w['word'], 'correct_translation': w['correct_translation']}
                       for w in words_data]

            logger.info(f"[TestManager] Запрос к AI для {len(ai_input)} слов")
            logger.info(f"[TestManager] AI input: {ai_input}")
            response = await self.ai_client.generate_test_options(ai_input)

            if 'tests' not in response:
                raise Exception("Неверный формат ответа от AI")

            logger.info(f"[TestManager] AI вернул {len(response['tests'])} тестов")

            # Если AI вернул пустой массив - это ошибка
            if not response['tests']:
                logger.error(f"[TestManager] AI вернул пустой массив тестов")
                raise Exception("AI вернул пустой массив тестов")

        except Exception as e:
            logger.error(f"[TestManager] Ошибка генерации тестов через AI: {e}")
            logger.error(f"[TestManager] Детали ошибки: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[TestManager] Traceback:\n{traceback.format_exc()}")
            # НЕ используем fallback - без AI тесты создавать нельзя
            raise

        # 3. Сохранение тестов
        test_ids = []
        for test_data in response['tests']:
            # Находим word_id для этого слова
            word_id = next((w['word_id'] for w in words_data if w['word'] == test_data['word']), None)
            if not word_id:
                logger.warning(f"[TestManager] Не найден word_id для слова {test_data['word']}")
                continue

            test_id = self.db.insert_test(
                user_id=user_id,
                word_id=word_id,
                word=test_data['word'],
                correct_translation=test_data['correct_translation'],
                wrong_option_1=test_data['wrong_options'][0],
                wrong_option_2=test_data['wrong_options'][1],
                wrong_option_3=test_data['wrong_options'][2]
            )
            test_ids.append(test_id)
            logger.info(f"[TestManager] Создан тест {test_id} для слова '{test_data['word']}'")

        return test_ids

    def get_test_with_shuffled_options(self, test_id: int) -> Dict:
        """
        Получить тест с перемешанными вариантами ответов

        Args:
            test_id: ID теста

        Returns:
            {
                'test_id': 123,
                'word': 'sophisticated',
                'options': [
                    {'text': 'сложный', 'is_correct': False, 'index': 0},
                    {'text': 'утончённый', 'is_correct': True, 'index': 1},
                    ...
                ]
            }
        """
        test = self.db.get_test(test_id)
        if not test:
            return None

        # Создаем массив из 4 вариантов
        options = [
            {'text': test['correct_translation'], 'is_correct': True},
            {'text': test['wrong_option_1'], 'is_correct': False},
            {'text': test['wrong_option_2'], 'is_correct': False},
            {'text': test['wrong_option_3'], 'is_correct': False}
        ]

        # Перемешиваем детерминированно (на основе test_id + created_at)
        # created_at уникален для каждого теста, что даёт равномерное распределение
        seed = hash(f"{test_id}_{test.get('created_at', '')}_{test['word']}")
        rng = random.Random(seed)
        rng.shuffle(options)

        # Добавляем индексы
        for i, option in enumerate(options):
            option['index'] = i

        return {
            'test_id': test['id'],
            'word_id': test['word_id'],
            'word': test['word'],
            'options': options
        }

    def submit_answer(self, test_id: int, selected_option_text: str) -> Dict:
        """
        Проверить ответ пользователя

        Args:
            test_id: ID теста
            selected_option_text: Выбранный вариант ответа (текст)

        Returns:
            {
                'is_correct': True,
                'correct_translation': 'утончённый',
                'new_rating': 8,
                'new_status': 'learning'
            }

        Процесс:
            1. Получить тест из БД
            2. Проверить правильность ответа
            3. Обновить рейтинг и статус слова
            4. Обновить статистику
            5. Удалить тест
            6. Вернуть результат
        """
        # Получаем тест
        test = self.db.get_test(test_id)
        if not test:
            raise Exception(f"Тест {test_id} не найден")

        # Проверяем правильность ответа
        is_correct = (selected_option_text == test['correct_translation'])

        # Получаем текущее состояние слова
        word = self.db.get_word_by_id(test['word_id'])
        if not word:
            raise Exception(f"Слово {test['word_id']} не найдено")

        current_status = word.get('status', 'new')
        current_rating = word.get('rating') or 0

        # Обновляем статус (new → learning)
        if current_status == 'new':
            self.db.update_word_status(test['word_id'], 'learning')
            current_status = 'learning'

        # Обновляем рейтинг (максимум 10)
        if is_correct:
            new_rating = min(current_rating + 1, 10)
        else:
            new_rating = 0
            # Если слово было learned, возвращаем в learning
            if current_status == 'learned':
                self.db.update_word_status(test['word_id'], 'learning')
                current_status = 'learning'

        # Обновляем рейтинг в БД
        self.db.update_word_rating(test['word_id'], new_rating)

        # Переходим в learned если рейтинг >= 10
        if current_status == 'learning' and new_rating >= 10:
            self.db.update_word_status(test['word_id'], 'learned')
            current_status = 'learned'

        # Обновляем статистику
        self.db.update_word_statistics(test['user_id'], test['word_id'], is_correct)

        # Удаляем тест
        self.db.delete_test(test_id)

        # Дополнительные значения (все переводы кроме основного)
        all_translations = self.db.get_all_translations_for_word(test['word_id'])
        additional_meanings = [t for t in all_translations if t != test['correct_translation']]

        return {
            'is_correct': is_correct,
            'correct_translation': test['correct_translation'],
            'additional_meanings': additional_meanings,
            'new_rating': new_rating,
            'new_status': current_status,
            'word': test['word']
        }

    def get_pending_tests(self, user_id: int) -> List[Dict]:
        """
        Получить нерешенные тесты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Список тестов
        """
        return self.db.get_pending_tests(user_id)
