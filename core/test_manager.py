#!/usr/bin/env python3
"""
TestManager - менеджер для создания и управления тестами
Работает с YandexAIClient для генерации вариантов ответов
"""

import random
from typing import List, Dict
from datetime import datetime
from database import WordoorioDatabase
from core.yandex_ai_client import YandexAIClient


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
            translation = self._get_translation_for_word(word['id'])
            if translation:
                words_data.append({
                    'word': word['lemma'],
                    'correct_translation': translation,
                    'word_id': word['id']  # Сохраняем для использования позже
                })

        if not words_data:
            return []

        # 2. Запрос к AI (async)
        try:
            # Готовим данные для API (без word_id)
            ai_input = [{'word': w['word'], 'correct_translation': w['correct_translation']}
                       for w in words_data]

            response = await self.ai_client.generate_test_options(ai_input)

            if 'tests' not in response:
                raise Exception("Неверный формат ответа от AI")

        except Exception as e:
            print(f"⚠️ Ошибка генерации тестов: {e}")
            # Fallback: используем случайные переводы из словаря пользователя
            response = await self._generate_fallback_options(user_id, words_data)

        # 3. Сохранение тестов
        test_ids = []
        for test_data in response['tests']:
            # Находим word_id для этого слова
            word_id = next((w['word_id'] for w in words_data if w['word'] == test_data['word']), None)
            if not word_id:
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

        return test_ids

    async def _generate_fallback_options(self, user_id: int, words_data: List[Dict]) -> Dict:
        """
        Генерация вариантов без AI (fallback)
        Использует случайные переводы из словаря пользователя
        """
        import sqlite3

        tests = []
        for word_data in words_data:
            # Получаем 3 случайных перевода других слов пользователя
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT dt.translation
                    FROM dictionary_translations dt
                    JOIN dictionary_words dw ON dt.word_id = dw.id
                    WHERE dw.user_id = ?
                      AND dt.translation != ?
                    ORDER BY RANDOM()
                    LIMIT 3
                """, (user_id, word_data['correct_translation']))

                wrong_options = [row[0] for row in cursor.fetchall()]

            # Если не хватает вариантов, добавляем заглушки
            while len(wrong_options) < 3:
                wrong_options.append(f"вариант {len(wrong_options) + 1}")

            tests.append({
                'word': word_data['word'],
                'correct_translation': word_data['correct_translation'],
                'wrong_options': wrong_options[:3]
            })

        return {'tests': tests}

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

        # Перемешиваем
        random.shuffle(options)

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

        # Обновляем статус (new → learning)
        if word['status'] == 'new':
            self.db.update_word_status(test['word_id'], 'learning')
            word['status'] = 'learning'

        # Обновляем рейтинг
        if is_correct:
            new_rating = word['rating'] + 1
        else:
            new_rating = 0
            # Если слово было learned, возвращаем в learning
            if word['status'] == 'learned':
                self.db.update_word_status(test['word_id'], 'learning')
                word['status'] = 'learning'

        # Обновляем рейтинг в БД
        self.db.update_word_rating(test['word_id'], new_rating)

        # Переходим в learned если рейтинг >= 10
        if word['status'] == 'learning' and new_rating >= 10:
            self.db.update_word_status(test['word_id'], 'learned')
            word['status'] = 'learned'

        # Обновляем статистику
        self.db.update_word_statistics(test['user_id'], test['word_id'], is_correct)

        # Удаляем тест
        self.db.delete_test(test_id)

        return {
            'is_correct': is_correct,
            'correct_translation': test['correct_translation'],
            'new_rating': new_rating,
            'new_status': word['status'],
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

    def _get_translation_for_word(self, word_id: int) -> str:
        """
        Получить перевод для слова

        Args:
            word_id: ID слова

        Returns:
            Перевод слова (первый из списка)
        """
        import sqlite3

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
