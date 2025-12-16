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


class AnalysisOrchestrator:
    """
    Координатор анализа текста

    Использует Yandex AI Studio агентов:
    - Agent #1 (fvt3bjtu1ehmg0v8tss3): Анализ слов
    - Agent #2 (fvt6j0ev2cgf1q2itfr6): Анализ фраз
    """

    # ID агентов в Yandex AI Studio
    AGENT_WORDS_ID = "fvt3bjtu1ehmg0v8tss3"      # Агент #1: Анализ слов
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
        print(f"🎭 [ORCHESTRATOR] Начало анализа текста ({len(request.text)} символов)", flush=True)

        # Валидация запроса
        error = request.validate()
        if error:
            return create_error_result(error)

        try:
            # Параллельный вызов двух агентов
            words_task = self._call_words_agent(request.text)
            phrases_task = self._call_phrases_agent(request.text)

            # Ждем оба результата
            words_responses, phrases_responses = await asyncio.gather(
                words_task,
                phrases_task,
                return_exceptions=True
            )

            # Проверяем ошибки
            if isinstance(words_responses, Exception):
                print(f"❌ Ошибка Agent #1 (words): {words_responses}", flush=True)
                words_responses = []

            if isinstance(phrases_responses, Exception):
                print(f"❌ Ошибка Agent #2 (phrases): {phrases_responses}", flush=True)
                phrases_responses = []

            # Преобразуем AgentResponse → Highlight
            highlights = []

            for agent_response in words_responses:
                highlight = await self._agent_response_to_highlight(agent_response, request.text)
                if highlight:
                    highlights.append(highlight)

            for agent_response in phrases_responses:
                highlight = await self._agent_response_to_highlight(agent_response, request.text)
                if highlight:
                    highlights.append(highlight)

            # Удаляем дубликаты
            highlights = self._remove_duplicates(highlights)

            # Подсчет слов
            word_count = len(request.text.split())

            print(f"✅ [ORCHESTRATOR] Анализ завершен: {len(highlights)} хайлайтов", flush=True)

            return create_success_result(
                highlights=highlights,
                total_words=word_count,
                performance={
                    'words_agent_results': len(words_responses) if not isinstance(words_responses, Exception) else 0,
                    'phrases_agent_results': len(phrases_responses) if not isinstance(phrases_responses, Exception) else 0,
                    'total_highlights': len(highlights)
                }
            )

        except Exception as e:
            print(f"❌ [ORCHESTRATOR] Ошибка анализа: {e}", flush=True)
            return create_error_result(f"Ошибка анализа: {str(e)}")

    async def _call_words_agent(self, text: str) -> List[AgentResponse]:
        """
        Вызов Agent #1 (анализ слов)

        Args:
            text: Текст для анализа

        Returns:
            List[AgentResponse]: Список найденных слов
        """
        print(f"📝 [AGENT #1] Анализ слов...", flush=True)

        # Формируем входные данные для агента
        user_input = json.dumps({
            "text": text
        }, ensure_ascii=False)

        try:
            # Вызываем агента через AI Studio
            response = await self.ai_client.call_agent(self.AGENT_WORDS_ID, user_input)

            # Агент возвращает один AgentResponse, но мы возвращаем список для единообразия
            return [response]

        except Exception as e:
            print(f"❌ [AGENT #1] Ошибка: {e}", flush=True)
            raise

    async def _call_phrases_agent(self, text: str) -> List[AgentResponse]:
        """
        Вызов Agent #2 (анализ фраз)

        Args:
            text: Текст для анализа

        Returns:
            List[AgentResponse]: Список найденных фраз
        """
        print(f"💬 [AGENT #2] Анализ фраз...", flush=True)

        # Формируем входные данные для агента
        user_input = json.dumps({
            "text": text
        }, ensure_ascii=False)

        try:
            # Вызываем агента через AI Studio
            response = await self.ai_client.call_agent(self.AGENT_PHRASES_ID, user_input)

            # Агент возвращает один AgentResponse
            return [response]

        except Exception as e:
            print(f"❌ [AGENT #2] Ошибка: {e}", flush=True)
            raise

    async def _agent_response_to_highlight(self, agent_response: AgentResponse, original_text: str) -> Highlight:
        """
        Преобразование AgentResponse → Highlight

        Args:
            agent_response: Ответ от агента
            original_text: Оригинальный текст (для извлечения контекста)

        Returns:
            Highlight: Хайлайт для фронтенда
        """
        try:
            # Извлекаем контекст из оригинального текста
            # Ищем предложение, содержащее английское слово
            context = self._extract_context(agent_response.highlight, original_text)

            # Получаем словарные значения для английского слова
            dictionary_meanings = self.ai_client.get_dictionary_meanings(agent_response.highlight)

            # Создаем Highlight
            highlight = Highlight(
                highlight=agent_response.highlight,  # Английское слово/фраза
                context=context,
                highlight_translation=agent_response.translation,  # Русский перевод
                cefr_level="C1",  # Пока фиксированное значение (можно улучшить)
                importance_score=85,  # Пока фиксированное значение (можно улучшить)
                dictionary_meanings=dictionary_meanings
            )

            return highlight

        except Exception as e:
            print(f"⚠️ Ошибка преобразования AgentResponse: {e}", flush=True)
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
        Удаление дубликатов из списка хайлайтов

        Args:
            highlights: Список хайлайтов

        Returns:
            List[Highlight]: Список без дубликатов
        """
        seen = set()
        unique_highlights = []

        for highlight in highlights:
            # Используем lowercase версию highlight как ключ
            key = highlight.highlight.lower()

            if key not in seen:
                seen.add(key)
                unique_highlights.append(highlight)

        removed_count = len(highlights) - len(unique_highlights)
        if removed_count > 0:
            print(f"🔄 Удалено дубликатов: {removed_count}", flush=True)

        return unique_highlights
