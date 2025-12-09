#!/usr/bin/env python3
"""
🎯 V2 DUAL PROMPT - Двойной запрос

Два отдельных запроса к AI:
1. Анализ слов-одиночек
2. Анализ устойчивых фраз и выражений
"""

import json
from typing import List
from contracts.analysis_contracts import PromptStrategy, PromptMetadata, Highlight
from utils.lemmatizer import lemmatize, lemmatize_russian


class DualPromptV2(PromptStrategy):
    """Dual-prompt версия - два отдельных запроса"""

    def get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            id="v2_dual",
            name="Dual Prompt (два запроса)",
            description="Два отдельных запроса: слова + фразы",
            is_stable=True,
            created_at="2024-11-15",
            performance_score=88.0,
            estimated_cost=0.8  # Два запроса = дороже
        )

    async def analyze_text(self, text: str, ai_client) -> List[Highlight]:
        """Dual анализ через два промпта"""
        print(f"🎯 Dual анализ через v2_dual промпт...", flush=True)

        try:
            # ЗАПРОС 1: Слова-одиночки
            print(f"\n📝 ЗАПРОС 1/2: Анализ слов-одиночек", flush=True)
            words_prompt = self._create_words_prompt(text)
            words_response = await ai_client.request_gpt(words_prompt)
            words = self._parse_response(words_response, "word")
            print(f"✅ Найдено {len(words)} слов", flush=True)

            # ЗАПРОС 2: Фразы и выражения
            print(f"\n📝 ЗАПРОС 2/2: Анализ фраз и выражений", flush=True)
            phrases_prompt = self._create_phrases_prompt(text)
            phrases_response = await ai_client.request_gpt(phrases_prompt)
            phrases = self._parse_response(phrases_response, "expression")
            print(f"✅ Найдено {len(phrases)} фраз", flush=True)

            # Объединяем результаты
            all_highlights = words + phrases

            # Добавляем словарные значения только для слов
            print(f"\n📚 Получение словарных значений для слов...", flush=True)
            for highlight in words:
                try:
                    meanings = ai_client.get_dictionary_meanings(highlight.highlight)

                    # Фильтруем - убираем основной перевод
                    main_translation = highlight.highlight_translation.lower().strip()
                    filtered_meanings = [
                        m for m in meanings
                        if m.lower().strip() != main_translation
                    ]

                    highlight.dictionary_meanings = filtered_meanings
                except Exception as e:
                    print(f"⚠️ Ошибка получения значений для '{highlight.highlight}': {e}", flush=True)

            print(f"\n✅ v2_dual: найдено {len(all_highlights)} хайлайтов (слова: {len(words)}, фразы: {len(phrases)})", flush=True)
            return all_highlights

        except Exception as e:
            print(f"❌ Ошибка v2_dual промпта: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return []

    def _create_words_prompt(self, text: str) -> str:
        """Промпт для поиска слов-одиночек"""
        return f"""
Ты — эксперт по продвинутой английской лексике. Найди ТОЛЬКО ОТДЕЛЬНЫЕ СЛОВА (не фразы!) из текста, которые стоят изучения.

Проанализируй этот английский текст:
"{text}"

БРАТЬ:
- Выразительные, точные слова (яркие прилагательные, сильные глаголы)
- Продвинутую лексику уровня C1-C2
- Слова которые встречаются в качественных медиа

НЕ БРАТЬ:
- Фразы и выражения (их найдем отдельно!)
- Базовую лексику A1-B1
- Узкую техническую терминологию

ВАЖНО:
- Бери ТОЛЬКО отдельные слова (одно слово = один хайлайт)
- НЕ бери фразы типа "give up", "make sense" - это для второго запроса!
- "highlight" = слово из текста (в любой форме - incentives, running, went)
- "context" = ОДНО предложение из текста, содержащее это слово
- "highlight_translation" = перевод слова с учетом контекста на русский

КРИТИЧЕСКИ ВАЖНО: берем СМЫСЛ из контекста!
  Примеры:
  - "running a business" → "управление" (не "бег")
  - "incentives for influencers" → "стимулы" (в значении "мотивация")
  - "went" → "пошел/пошла" (не "уехал")

Формат ответа — только массив JSON:
[
  {{
    "highlight": "слово из текста",
    "context": "предложение из текста",
    "highlight_translation": "перевод"
  }}
]

Верни только массив JSON.
"""

    def _create_phrases_prompt(self, text: str) -> str:
        """Промпт для поиска фраз и выражений"""
        return f"""
Ты — эксперт по английским фразам и выражениям. Найди ТОЛЬКО УСТОЙЧИВЫЕ ФРАЗЫ И ВЫРАЖЕНИЯ (не отдельные слова!) из текста.

Проанализируй этот английский текст:
"{text}"

БРАТЬ:
- Фразовые глаголы (give up, figure out, come across)
- Устойчивые выражения и коллокации (make sense, take into account)
- Идиомы и метафоры
- Сильные словосочетания (compelling argument, sheer determination)

НЕ БРАТЬ:
- Отдельные слова (их уже нашли в первом запросе!)
- Случайные сочетания слов
- Простые предлогные фразы
- Длинные фрагменты предложений

ВАЖНО:
- Бери ТОЛЬКО фразы (2-4 слова)
- НЕ бери отдельные слова - это для первого запроса!
- "context" = ОДНО предложение (8-15 слов) содержащее фразу
- "highlight_translation" = перевод фразы с учетом контекста на русский

КРИТИЧЕСКИ ВАЖНО: берем СМЫСЛ из контекста!

Формат ответа — только массив JSON:
[
  {{
    "highlight": "фраза или выражение",
    "context": "одно предложение из текста",
    "highlight_translation": "перевод фразы"
  }}
]

Верни только массив JSON.
"""

    def _parse_response(self, response: str, highlight_type: str) -> List[Highlight]:
        """Парсит ответ от AI"""
        try:
            # Очищаем от markdown разметки
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()

            # Парсим JSON
            highlights_data = json.loads(text)

            highlights = []
            for item in highlights_data:
                # Валидация данных
                if not self._validate_highlight_data(item):
                    continue

                original_translation = item.get("highlight_translation", "")

                # Лемматизируем английский highlight (преобразуем в словарную форму)
                original_highlight = item["highlight"]
                lemmatized_highlight = lemmatize(original_highlight)

                # Логируем если была изменена форма
                if lemmatized_highlight != original_highlight:
                    print(f"  🔤 EN: '{original_highlight}' → '{lemmatized_highlight}'", flush=True)

                # Лемматизируем русский перевод (преобразуем в словарную форму)
                lemmatized_translation = lemmatize_russian(original_translation)

                # Логируем если была изменена форма перевода
                if lemmatized_translation != original_translation:
                    print(f"  🔤 RU: '{original_translation}' → '{lemmatized_translation}'", flush=True)

                highlight = Highlight(
                    highlight=lemmatized_highlight,  # Используем лемматизированную форму
                    context=item["context"],
                    highlight_translation=lemmatized_translation,  # Используем лемматизированный перевод
                    cefr_level="C1",
                    importance_score=85,
                    dictionary_meanings=[],
                    why_interesting="Выразительная лексика для стильной речи",
                    type=highlight_type  # "word" или "expression"
                )
                highlights.append(highlight)

            return highlights

        except Exception as e:
            print(f"❌ Ошибка парсинга v2_dual ответа: {e}", flush=True)
            print(f"❌ Ответ был: {response[:200]}...", flush=True)
            return []

    def _validate_highlight_data(self, item: dict) -> bool:
        """Проверяет корректность данных хайлайта"""
        required_fields = ["highlight", "context"]
        for field in required_fields:
            if field not in item or not item[field]:
                return False

        # Проверка длины контекста (минимум 6 слов)
        context_words = item["context"].split()
        if len(context_words) < 6:
            print(f"⚠️ v2_dual: пропускаю '{item['highlight']}' - контекст слишком короткий", flush=True)
            return False

        # Проверяем что хайлайт действительно есть в контексте
        highlight_text = item["highlight"].lower()
        context_text = item["context"].lower()

        # Для фраз проверяем по частям
        if ' ' in highlight_text:
            for word in highlight_text.split():
                if len(word) > 2 and word not in context_text:
                    print(f"⚠️ v2_dual: пропускаю '{item['highlight']}' - слово '{word}' не найдено в контексте", flush=True)
                    return False
        else:
            # Для одного слова
            if highlight_text not in context_text:
                print(f"⚠️ v2_dual: пропускаю '{item['highlight']}' - не найдено в контексте", flush=True)
                return False

        return True
