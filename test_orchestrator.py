#!/usr/bin/env python3
"""
Тестовый скрипт для проверки AnalysisOrchestrator
"""

import asyncio
from contracts.analysis_contracts import AnalysisRequest, AgentResponse
from core.analysis_orchestrator import AnalysisOrchestrator
from core.yandex_ai_client import YandexAIClient


async def test_agent_response_to_highlight():
    """Тест преобразования AgentResponse → Highlight"""
    print("🧪 Тест 1: Преобразование AgentResponse → Highlight")

    client = YandexAIClient()
    orchestrator = AnalysisOrchestrator(client)

    # Создаем тестовый AgentResponse
    agent_response = AgentResponse(
        highlight="compelling",  # Английское слово
        category="word",
        translation="убедительный",  # Русский перевод
        examples=["compelling argument", "compelling evidence"],
        collocations=["compelling reason", "compelling case"]
    )

    text = "This is a compelling argument about machine learning."

    highlight = await orchestrator._agent_response_to_highlight(agent_response, text)

    if highlight:
        print(f"✅ Highlight создан:")
        print(f"   - highlight: {highlight.highlight}")
        print(f"   - context: {highlight.context}")
        print(f"   - translation: {highlight.highlight_translation}")
        print(f"   - dictionary_meanings: {highlight.dictionary_meanings}")
    else:
        print("❌ Не удалось создать highlight")


async def test_remove_duplicates():
    """Тест удаления дубликатов"""
    print("\n🧪 Тест 2: Удаление дубликатов")

    from contracts.analysis_contracts import Highlight

    client = YandexAIClient()
    orchestrator = AnalysisOrchestrator(client)

    highlights = [
        Highlight("compelling", "context 1", "убедительный", "C1", 85, ["meaning 1"]),
        Highlight("Compelling", "context 2", "убедительный", "C1", 85, ["meaning 2"]),
        Highlight("argument", "context 3", "аргумент", "B2", 80, ["meaning 3"]),
        Highlight("compelling", "context 4", "убедительный", "C1", 85, ["meaning 4"]),
    ]

    unique = orchestrator._remove_duplicates(highlights)

    print(f"✅ Исходных: {len(highlights)}, уникальных: {len(unique)}")
    for h in unique:
        print(f"   - {h.highlight}")


def test_analysis_request_validation():
    """Тест валидации запроса"""
    print("\n🧪 Тест 3: Валидация AnalysisRequest")

    # Корректный запрос
    request1 = AnalysisRequest(text="This is a valid text with more than five words")
    error1 = request1.validate()
    print(f"✅ Корректный запрос: {error1 if error1 else 'OK'}")

    # Пустой текст
    request2 = AnalysisRequest(text="")
    error2 = request2.validate()
    print(f"✅ Пустой текст: {error2}")

    # Слишком короткий текст
    request3 = AnalysisRequest(text="Too short")
    error3 = request3.validate()
    print(f"✅ Короткий текст: {error3}")


async def main():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ НОВОЙ АРХИТЕКТУРЫ")
    print("=" * 60)

    test_analysis_request_validation()
    await test_agent_response_to_highlight()
    await test_remove_duplicates()

    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
