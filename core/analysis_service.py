#!/usr/bin/env python3
"""
🎯 ANALYSIS SERVICE - Интеграционный слой
Объединяет все компоненты новой архитектуры:
- Prompt versioning
- Deduplication
- Page configurations
- AI clients
"""

import time
from typing import Dict, Any, List
from contracts.analysis_contracts import (
    AnalysisRequest,
    AnalysisResult,
    Highlight,
    create_error_result,
    create_success_result
)
from core.prompts.prompt_manager import get_prompt_manager
from core.services.deduplication_service import get_deduplication_service


class AnalysisService:
    """
    Центральный сервис для анализа текста
    Объединяет версионирование промптов, дедупликацию и конфигурации страниц
    """

    def __init__(self):
        self.prompt_manager = get_prompt_manager()
        self.deduplication_service = get_deduplication_service()

        # Маппинг page_id -> prompt_version
        self.page_to_prompt = {
            'main': 'v1_basic',
            'experimental': 'v2_dual',
        }

    async def analyze_text(self, request: AnalysisRequest, ai_client) -> AnalysisResult:
        """
        Главный метод анализа текста

        Args:
            request: Запрос с текстом и параметрами
            ai_client: AI клиент (YandexAIClient или ExperimentalAIClient)

        Returns:
            AnalysisResult: Результат с хайлайтами или ошибкой
        """
        print(f"\n{'='*60}")
        print(f"🎯 ЗАПУСК АНАЛИЗА (page: {request.page_id})")
        print(f"{'='*60}\n", flush=True)

        start_time = time.time()

        # 1. Валидация запроса
        validation_error = request.validate()
        if validation_error:
            print(f"❌ Ошибка валидации: {validation_error}", flush=True)
            return create_error_result(validation_error)

        try:
            # 2. Получаем версию промпта для данной страницы
            prompt_version = self.page_to_prompt.get(request.page_id, 'v1_basic')
            print(f"📋 Используем промпт: {prompt_version}", flush=True)

            # 3. Получаем стратегию промпта
            prompt_strategy = self.prompt_manager.get_prompt(prompt_version)
            metadata = prompt_strategy.get_metadata()
            print(f"ℹ️  {metadata.name} - {metadata.description}", flush=True)
            print(f"💰 Примерная стоимость: {metadata.estimated_cost}₽", flush=True)

            # 4. Запускаем анализ через стратегию
            print(f"\n🤖 Анализируем текст ({len(request.text.split())} слов)...", flush=True)
            highlights = await prompt_strategy.analyze_text(request.text, ai_client)
            print(f"✅ Получено {len(highlights)} хайлайтов", flush=True)

            # 5. Дедупликация
            if len(highlights) > 1:
                print(f"\n🔍 Запуск дедупликации...", flush=True)
                highlights, duplications = self.deduplication_service.deduplicate_highlights(highlights)

                if duplications:
                    dup_analysis = self.deduplication_service.analyze_duplications(duplications)
                    print(f"📊 Статистика дубликатов:", flush=True)
                    print(f"   - Всего удалено: {dup_analysis['total_duplicates']}", flush=True)
                    print(f"   - По типам: {dup_analysis['by_type']}", flush=True)

            # 6. Формируем результат
            end_time = time.time()
            performance = {
                'duration_seconds': round(end_time - start_time, 2),
                'prompt_version': prompt_version,
                'highlights_before_dedup': len(highlights) + len(duplications) if 'duplications' in locals() else len(highlights),
                'highlights_after_dedup': len(highlights),
                'estimated_cost': metadata.estimated_cost
            }

            result = create_success_result(
                highlights=highlights,
                total_words=len(request.text.split()),
                performance=performance
            )

            print(f"\n{'='*60}")
            print(f"✅ АНАЛИЗ ЗАВЕРШЕН")
            print(f"{'='*60}")
            print(f"⏱️  Время: {performance['duration_seconds']}с")
            print(f"📊 Хайлайтов: {len(highlights)}")
            print(f"💰 Стоимость: ~{metadata.estimated_cost}₽")
            print(f"{'='*60}\n", flush=True)

            return result

        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return create_error_result(f"Ошибка анализа: {str(e)}")

    def get_available_pages(self) -> List[Dict[str, str]]:
        """Получить список доступных страниц и их промптов"""
        result = []
        for page_id, prompt_version in self.page_to_prompt.items():
            try:
                strategy = self.prompt_manager.get_prompt(prompt_version)
                metadata = strategy.get_metadata()
                result.append({
                    'page_id': page_id,
                    'prompt_version': prompt_version,
                    'prompt_name': metadata.name,
                    'description': metadata.description,
                    'is_stable': metadata.is_stable,
                    'estimated_cost': metadata.estimated_cost
                })
            except Exception as e:
                print(f"⚠️  Ошибка получения информации о странице {page_id}: {e}", flush=True)
        return result

    def register_page(self, page_id: str, prompt_version: str):
        """
        Регистрирует новую страницу с привязкой к версии промпта

        Example:
            service.register_page('advanced', 'v3_enhanced')
        """
        # Проверяем что такой промпт существует
        try:
            self.prompt_manager.get_prompt(prompt_version)
            self.page_to_prompt[page_id] = prompt_version
            print(f"✅ Зарегистрирована страница '{page_id}' -> промпт '{prompt_version}'", flush=True)
        except ValueError as e:
            print(f"❌ Не удалось зарегистрировать страницу: {e}", flush=True)
            raise


# Глобальный синглтон
_analysis_service = None

def get_analysis_service() -> AnalysisService:
    """Получить глобальный экземпляр AnalysisService"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


# ============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================================================

async def example_usage():
    """Примеры как использовать сервис"""
    from core.yandex_ai_client import YandexAIClient

    # 1. Получаем сервис
    service = get_analysis_service()

    # 2. Создаем запрос
    request = AnalysisRequest(
        text="This is a sophisticated approach to solving complex problems in modern software development.",
        page_id="main"
    )

    # 3. Анализируем
    ai_client = YandexAIClient()
    result = await service.analyze_text(request, ai_client)

    # 4. Используем результат
    if result.success:
        print(f"Найдено хайлайтов: {len(result.highlights)}")
        for h in result.highlights:
            print(f"  - {h.highlight}: {h.context_translation}")
    else:
        print(f"Ошибка: {result.error}")

    # 5. Регистрируем новую страницу (когда создадим v3)
    # service.register_page('advanced', 'v3_enhanced')


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
