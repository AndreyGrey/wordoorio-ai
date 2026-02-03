#!/usr/bin/env python3
"""
🎭 ANALYSIS ORCHESTRATOR

Оркестратор анализа текста через Yandex AI Studio агентов.
Координирует вызовы агентов, собирает результаты, убирает дубликаты.

@version 2.0.0 (Agent Refactoring)
@author Wordoorio Team
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
from contracts.analysis_contracts import (
    Highlight,
    AnalysisResult,
    AnalysisRequest,
    AgentResponse,
    create_success_result,
    create_error_result
)
from core.yandex_ai_client import YandexAIClient
from utils.lemmatizer import lemmatize

# Настройка логирования
logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Координатор анализа текста

    Использует Yandex AI Studio агентов:
    - Agent #1 (fvt3bjtulehmg0v8tss3): Анализ слов
    - Agent #2 (fvt6j0ev2cgf1q2itfr6): Анализ фраз
    """

    # ID агентов в Yandex AI Studio
    AGENT_WORDS_ID = "fvt3bjtulehmg0v8tss3"      # Агент #1: Анализ слов
    AGENT_PHRASES_ID = "fvt6j0ev2cgf1q2itfr6"    # Агент #2: Анализ фраз

    def __init__(self, ai_client: YandexAIClient):
        """
        Инициализация оркестратора

        Args:
            ai_client: Клиент для работы с Yandex AI Studio
        """
        self.ai_client = ai_client

    async def analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Анализ текста через агентов Yandex AI Studio

        Алгоритм:
        1. Валидация запроса
        2. Параллельный вызов Agent #1 (слова) и Agent #2 (фразы)
        3. Сбор ответов от агентов
        4. Преобразование AgentResponse → Highlight
        5. Добавление словарных значений
        6. Удаление дубликатов
        7. Возврат AnalysisResult

        Args:
            request: Запрос на анализ

        Returns:
            AnalysisResult: Результат анализа с хайлайтами
        """
        import time
        start_time = time.time()
        logger.info(f"[ORCHESTRATOR] Начало анализа текста ({len(request.text)} символов)")

        # Валидация запроса
        error = request.validate()
        if error:
            return create_error_result(error)

        try:
            # Параллельный вызов двух агентов
            agents_start = time.time()
            words_task = self._call_words_agent(request.text)
            phrases_task = self._call_phrases_agent(request.text)

            # Ждем оба результата
            words_responses, phrases_responses = await asyncio.gather(
                words_task,
                phrases_task,
                return_exceptions=True
            )
            agents_time = time.time() - agents_start
            logger.info(f"Время вызова агентов: {agents_time:.2f}s")

            # Проверяем ошибки
            if isinstance(words_responses, Exception):
                logger.error(f"Ошибка Agent #1 (words): {words_responses}")
                words_responses = []

            if isinstance(phrases_responses, Exception):
                logger.error(f"Ошибка Agent #2 (phrases): {phrases_responses}")
                phrases_responses = []

            # Преобразуем AgentResponse → Highlight (параллельно!)
            processing_start = time.time()

            # Собираем все задачи преобразования для параллельного выполнения
            tasks = []
            for agent_response in words_responses:
                for highlight_dict in agent_response.highlights:
                    tasks.append(self._dict_to_highlight(highlight_dict, request.text))

            for agent_response in phrases_responses:
                for highlight_dict in agent_response.highlights:
                    tasks.append(self._dict_to_highlight(highlight_dict, request.text))

            # Запускаем все преобразования параллельно
            logger.info(f"Запуск {len(tasks)} задач обработки параллельно")
            highlights_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Фильтруем результаты
            highlights = []
            for result in highlights_results:
                if isinstance(result, Exception):
                    logger.warning(f"Ошибка обработки highlight: {result}")
                elif result:
                    highlights.append(result)

            processing_time = time.time() - processing_start
            logger.info(f"Время обработки хайлайтов (параллельно): {processing_time:.2f}s")

            # Удаляем дубликаты
            highlights = self._remove_duplicates(highlights)

            # Подсчет слов
            word_count = len(request.text.split())

            total_time = time.time() - start_time
            logger.info(f"ОБЩЕЕ ВРЕМЯ: {total_time:.2f}s")
            logger.info(f"[ORCHESTRATOR] Анализ завершен: {len(highlights)} хайлайтов")

            return create_success_result(
                highlights=highlights,
                total_words=word_count,
                performance={
                    'words_agent_results': len(words_responses) if not isinstance(words_responses, Exception) else 0,
                    'phrases_agent_results': len(phrases_responses) if not isinstance(phrases_responses, Exception) else 0,
                    'total_highlights': len(highlights),
                    'agents_time': f"{agents_time:.2f}s",
                    'processing_time': f"{processing_time:.2f}s",
                    'total_time': f"{total_time:.2f}s"
                }
            )

        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Ошибка анализа: {e}", exc_info=True)
            return create_error_result(f"Ошибка анализа: {str(e)}")

    async def _call_words_agent(self, text: str) -> List[AgentResponse]:
        """
        Вызов Agent #1 (анализ слов)

        Args:
            text: Текст для анализа

        Returns:
            List[AgentResponse]: Список найденных слов
        """
        logger.info("[AGENT #1] Анализ слов...")

        try:
            # Вызываем агента через AI Studio (передаем просто текст)
            response = await self.ai_client.call_agent(self.AGENT_WORDS_ID, text)

            # Агент возвращает один AgentResponse, но мы возвращаем список для единообразия
            return [response]

        except Exception as e:
            logger.error(f"[AGENT #1] Ошибка: {e}", exc_info=True)
            raise

    async def _call_phrases_agent(self, text: str) -> List[AgentResponse]:
        """
        Вызов Agent #2 (анализ фраз)

        Args:
            text: Текст для анализа

        Returns:
            List[AgentResponse]: Список найденных фраз
        """
        logger.info("[AGENT #2] Анализ фраз...")

        try:
            # Вызываем агента через AI Studio (передаем просто текст)
            response = await self.ai_client.call_agent(self.AGENT_PHRASES_ID, text)

            # Агент возвращает один AgentResponse
            return [response]

        except Exception as e:
            logger.error(f"[AGENT #2] Ошибка: {e}", exc_info=True)
            raise

    async def _dict_to_highlight(self, highlight_dict: Dict[str, Any], original_text: str) -> Highlight:
        """
        Преобразование словаря из AgentResponse → Highlight

        Args:
            highlight_dict: Словарь с данными хайлайта от агента
            original_text: Оригинальный текст (не используется, т.к. контекст уже в highlight_dict)

        Returns:
            Highlight: Хайлайт для фронтенда
        """
        try:
            import time
            word = highlight_dict.get('highlight', '')

            # Лемматизируем слово для запроса в словарь
            lemma_start = time.time()
            word_lemma = lemmatize(word)
            lemma_time = time.time() - lemma_start

            # Yandex Dictionary API поддерживает ТОЛЬКО отдельные слова, НЕ фразы
            word_count = len(word_lemma.split())

            if word_count > 1:
                # Фраза (2+ слов) - словарь не нужен (возвращает мусор)
                dictionary_meanings = []
                dict_time = 0
                print(f"🔄 {word} → {word_lemma} [фраза из {word_count} слов, словарь пропущен]", flush=True)
            else:
                # Отдельное слово (1 слово) - запрашиваем словарь
                dict_start = time.time()

                # СТРАТЕГИЯ: Сначала оригинал, потом лемма
                # 1. Пробуем оригинал (implied)
                dictionary_meanings = await self.ai_client.get_dictionary_meanings(word)
                dict_query = word

                # 2. Если пусто и оригинал != лемма, пробуем лемму (imply)
                if not dictionary_meanings and word.lower() != word_lemma.lower():
                    dictionary_meanings = await self.ai_client.get_dictionary_meanings(word_lemma)
                    dict_query = f"{word}→{word_lemma}"

                dict_time = time.time() - dict_start
                print(f"🔄 {word} → {word_lemma} [лемма: {lemma_time*1000:.0f}ms, словарь '{dict_query}': {dict_time*1000:.0f}ms]", flush=True)

            # Получаем основной перевод от агента
            main_translation = highlight_dict.get('highlight_translation', '').lower().strip()

            # Исключаем основной перевод из дополнительных значений (убираем дубликат)
            if main_translation and dictionary_meanings:
                # Нормализуем строки: нижний регистр, нормализуем пробелы (заменяем любые пробелы на обычные)
                import re
                def normalize(s):
                    # Заменяем любые пробельные символы на обычный пробел
                    normalized = re.sub(r'\s+', ' ', s.strip().lower())
                    return normalized

                main_normalized = normalize(main_translation)

                filtered = []
                duplicates_removed = 0
                for meaning in dictionary_meanings:
                    meaning_normalized = normalize(meaning)

                    # Убираем точные совпадения: "усиливать" == "усиливать"
                    if meaning_normalized == main_normalized:
                        duplicates_removed += 1
                        continue

                    filtered.append(meaning)

                dictionary_meanings = filtered
                if duplicates_removed > 0:
                    print(f"   🗑️ Убрано дубликатов: {duplicates_removed}", flush=True)
                print(f"   📖 Дополнительных значений: {len(dictionary_meanings)}", flush=True)

            # Создаем Highlight из данных агента
            highlight = Highlight(
                highlight=word,  # Оригинальное слово - то что видит пользователь
                context=highlight_dict.get('context', ''),  # Контекст с оригинальной формой
                highlight_translation=highlight_dict.get('highlight_translation', ''),
                lemma=word_lemma,  # Лемматизированная форма для хранения в БД
                dictionary_meanings=dictionary_meanings
            )

            return highlight

        except Exception as e:
            print(f"⚠️ Ошибка преобразования highlight dict: {e}", flush=True)
            return None

    def _extract_context(self, word: str, text: str) -> str:
        """
        Извлечение контекста (предложения) для слова из текста

        Args:
            word: Слово/фраза для поиска
            text: Исходный текст

        Returns:
            str: Предложение, содержащее слово
        """
        # Разбиваем текст на предложения
        sentences = text.replace('!', '.').replace('?', '.').split('.')

        # Ищем предложение, содержащее слово
        word_lower = word.lower()
        for sentence in sentences:
            if word_lower in sentence.lower():
                return sentence.strip()

        # Если не нашли - возвращаем начало текста
        return text[:200].strip()

    def _remove_duplicates(self, highlights: List[Highlight]) -> List[Highlight]:
        """
        Удаление дубликатов из списка хайлайтов по леммам

        Args:
            highlights: Список хайлайтов

        Returns:
            List[Highlight]: Список без дубликатов
        """
        seen = set()
        unique_highlights = []

        for highlight in highlights:
            # Используем готовую лемму из Highlight (уже вычислена ранее)
            # amplify/amplifying/amplified = одна лемма "amplify"
            lemma = highlight.lemma.lower() if highlight.lemma else highlight.highlight.lower()

            if lemma not in seen:
                seen.add(lemma)
                unique_highlights.append(highlight)

        removed_count = len(highlights) - len(unique_highlights)
        if removed_count > 0:
            print(f"🔄 Удалено дубликатов: {removed_count}", flush=True)

        return unique_highlights
