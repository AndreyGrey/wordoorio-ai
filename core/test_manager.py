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
            # Находим оригинальные данные для этого слова (НЕ из ответа AI!)
            original_word_data = next((w for w in words_data if w['word'] == test_data['word']), None)
            if not original_word_data:
                logger.warning(f"[TestManager] Не найдены данные для слова {test_data['word']}")
                continue

            word_id = original_word_data['word_id']
            correct_translation = original_word_data['correct_translation']  # Наш перевод, не от AI!

            # Валидация: проверяем количество и уникальность вариантов
            wrong_options = test_data.get('wrong_options', [])

            if len(wrong_options) < 3:
                logger.warning(f"[TestManager] Недостаточно вариантов для '{test_data['word']}': {wrong_options}")
                continue

            all_options = [correct_translation] + wrong_options[:3]
            unique_options = set(all_options)

            if len(unique_options) < 4:
                logger.warning(f"[TestManager] Дубликаты в вариантах для '{test_data['word']}': {wrong_options}")
                continue  # Пропускаем тест с дубликатами

            test_id = self.db.insert_test(
                user_id=user_id,
                word_id=word_id,
                word=test_data['word'],
                correct_translation=correct_translation,
                wrong_option_1=wrong_options[0],
                wrong_option_2=wrong_options[1],
                wrong_option_3=wrong_options[2],
                test_mode=1  # EN→RU режим
            )
            test_ids.append(test_id)
            logger.info(f"[TestManager] Создан тест {test_id} для слова '{test_data['word']}' (mode=1)")

        return test_ids

    async def create_reverse_tests_batch(self, user_id: int, words: List[Dict]) -> List[int]:
        """
        Создать пакет обратных тестов (RU→EN) для списка слов

        Args:
            user_id: ID пользователя
            words: Список словарей со словами

        Returns:
            Список ID созданных тестов
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
                    'word_id': word['id']
                })

        if not words_data:
            logger.warning("[TestManager] Нет слов с переводами для создания обратных тестов")
            return []

        # 2. Запрос к AI Agent #4 (обратный режим)
        try:
            ai_input = [{'word': w['word'], 'correct_translation': w['correct_translation']}
                       for w in words_data]

            logger.info(f"[TestManager] Запрос к AI (reverse) для {len(ai_input)} слов")
            response = await self.ai_client.generate_reverse_test_options(ai_input)

            if 'tests' not in response:
                raise Exception("Неверный формат ответа от AI (reverse)")

            logger.info(f"[TestManager] AI (reverse) вернул {len(response['tests'])} тестов")

            if not response['tests']:
                logger.error(f"[TestManager] AI (reverse) вернул пустой массив тестов")
                raise Exception("AI вернул пустой массив тестов (reverse)")

        except Exception as e:
            logger.error(f"[TestManager] Ошибка генерации обратных тестов через AI: {e}")
            import traceback
            logger.error(f"[TestManager] Traceback:\n{traceback.format_exc()}")
            raise

        # 3. Сохранение тестов
        test_ids = []
        for test_data in response['tests']:
            # Находим оригинальные данные для этого слова (НЕ из ответа AI!)
            original_word_data = next((w for w in words_data if w['word'] == test_data['word']), None)
            if not original_word_data:
                logger.warning(f"[TestManager] Не найдены данные для слова {test_data['word']} (reverse)")
                continue

            word_id = original_word_data['word_id']
            correct_translation = original_word_data['correct_translation']  # Наш перевод, не от AI!

            wrong_options = test_data.get('wrong_options', [])

            if len(wrong_options) < 3:
                logger.warning(f"[TestManager] Недостаточно вариантов для '{test_data['word']}' (reverse): {wrong_options}")
                continue

            # Для обратного режима: правильный ответ — английское слово (word)
            all_options = [test_data['word']] + wrong_options[:3]
            unique_options = set(all_options)

            if len(unique_options) < 4:
                logger.warning(f"[TestManager] Дубликаты в вариантах для '{test_data['word']}' (reverse): {wrong_options}")
                continue

            test_id = self.db.insert_test(
                user_id=user_id,
                word_id=word_id,
                word=test_data['word'],
                correct_translation=correct_translation,
                wrong_option_1=wrong_options[0],
                wrong_option_2=wrong_options[1],
                wrong_option_3=wrong_options[2],
                test_mode=2  # RU→EN режим
            )
            test_ids.append(test_id)
            logger.info(f"[TestManager] Создан обратный тест {test_id} для слова '{test_data['word']}' (mode=2)")

        return test_ids

    async def create_dual_mode_tests(self, user_id: int, words: List[Dict]) -> List[int]:
        """
        Создать тесты обоих режимов: 10 EN→RU + 10 RU→EN

        Args:
            user_id: ID пользователя
            words: Список из 20 слов (делится пополам)

        Returns:
            Список всех ID созданных тестов (сначала mode=1, потом mode=2)
        """
        if len(words) < 2:
            logger.warning("[TestManager] Недостаточно слов для dual mode")
            return []

        # Делим слова пополам
        mid = len(words) // 2
        words_mode1 = words[:mid]  # Первая половина для EN→RU
        words_mode2 = words[mid:]  # Вторая половина для RU→EN

        logger.info(f"[TestManager] Создание dual mode тестов: {len(words_mode1)} EN→RU + {len(words_mode2)} RU→EN")

        all_test_ids = []

        # Создаем тесты mode=1 (EN→RU)
        try:
            test_ids_1 = await self.create_tests_batch(user_id, words_mode1)
            all_test_ids.extend(test_ids_1)
            logger.info(f"[TestManager] Создано {len(test_ids_1)} тестов mode=1")
        except Exception as e:
            logger.error(f"[TestManager] Ошибка создания тестов mode=1: {e}")

        # Создаем тесты mode=2 (RU→EN)
        try:
            test_ids_2 = await self.create_reverse_tests_batch(user_id, words_mode2)
            all_test_ids.extend(test_ids_2)
            logger.info(f"[TestManager] Создано {len(test_ids_2)} тестов mode=2")
        except Exception as e:
            logger.error(f"[TestManager] Ошибка создания тестов mode=2: {e}")

        logger.info(f"[TestManager] Всего создано {len(all_test_ids)} тестов dual mode")
        return all_test_ids

    def get_test_with_shuffled_options(self, test_id: int) -> Dict:
        """
        Получить тест с перемешанными вариантами ответов

        Args:
            test_id: ID теста

        Returns:
            {
                'test_id': 123,
                'test_mode': 1,  # 1=EN→RU, 2=RU→EN
                'question': 'sophisticated',  # что показываем пользователю
                'correct_answer': 'утончённый',  # правильный ответ
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

        test_mode = test.get('test_mode') or 1

        if test_mode == 1:
            # EN→RU: показываем английское, выбираем русское
            question = test['word']
            correct_answer = test['correct_translation']
            options = [
                {'text': test['correct_translation'], 'is_correct': True},
                {'text': test['wrong_option_1'], 'is_correct': False},
                {'text': test['wrong_option_2'], 'is_correct': False},
                {'text': test['wrong_option_3'], 'is_correct': False}
            ]
        else:
            # RU→EN: показываем русское, выбираем английское
            question = test['correct_translation']
            correct_answer = test['word']
            options = [
                {'text': test['word'], 'is_correct': True},
                {'text': test['wrong_option_1'], 'is_correct': False},
                {'text': test['wrong_option_2'], 'is_correct': False},
                {'text': test['wrong_option_3'], 'is_correct': False}
            ]

        # Перемешиваем детерминированно
        seed = hash(f"{test_id}_{test.get('created_at', '')}_{test['word']}")
        rng = random.Random(seed)
        rng.shuffle(options)

        # Добавляем индексы
        for i, option in enumerate(options):
            option['index'] = i

        return {
            'test_id': test['id'],
            'word_id': test['word_id'],
            'test_mode': test_mode,
            'question': question,
            'correct_answer': correct_answer,
            'word': test['word'],  # оставляем для совместимости
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
                'correct_answer': 'утончённый',
                'test_mode': 1,
                'new_rating': 8,
                'new_status': 'learning'
            }

        Процесс:
            1. Получить тест из БД
            2. Проверить правильность ответа (с учётом test_mode)
            3. Обновить рейтинг и статус слова
            4. Обновить статистику
            5. Удалить тест
            6. Вернуть результат
        """
        # Получаем тест
        test = self.db.get_test(test_id)
        if not test:
            raise Exception(f"Тест {test_id} не найден")

        test_mode = test.get('test_mode') or 1

        # Проверяем правильность ответа в зависимости от режима
        if test_mode == 1:
            # EN→RU: правильный ответ — русский перевод
            correct_answer = test['correct_translation']
        else:
            # RU→EN: правильный ответ — английское слово
            correct_answer = test['word']

        is_correct = (selected_option_text == correct_answer)

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
            'correct_answer': correct_answer,
            'correct_translation': test['correct_translation'],  # для совместимости
            'additional_meanings': additional_meanings,
            'new_rating': new_rating,
            'new_status': current_status,
            'word': test['word'],
            'test_mode': test_mode
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
