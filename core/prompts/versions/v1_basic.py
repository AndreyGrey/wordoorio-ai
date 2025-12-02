#!/usr/bin/env python3
"""
🎯 V1 BASIC PROMPT - Оригинальная версия

Единый промпт для поиска выразительной английской лексики.
Стабильная версия, используется по умолчанию.
"""

import json
import re
from typing import List
from contracts.analysis_contracts import PromptStrategy, PromptMetadata, Highlight


class BasicPromptV1(PromptStrategy):
    """Базовая версия промпта - единый анализ"""
    
    def get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            id="v1_basic",
            name="Базовая версия",
            description="Единый промпт для поиска выразительной лексики",
            is_stable=True,
            created_at="2024-11-01",
            performance_score=85.0,
            estimated_cost=0.4
        )
    
    async def analyze_text(self, text: str, ai_client) -> List[Highlight]:
        """Анализ текста через единый промпт"""
        print(f"🎯 Анализ через v1_basic промпт...", flush=True)

        try:
            # Определяем количество хайлайтов по длине текста
            word_count = len(text.split())
            if word_count < 20:
                target_count = "3-5"
            elif word_count < 50:
                target_count = "5-10"
            elif word_count < 100:
                target_count = "10-20"
            else:
                target_count = "15-30"

            prompt = self._create_prompt(text, target_count)
            response = await ai_client.request_gpt(prompt)
            highlights = self._parse_response(response)

            # Добавляем словарные значения для каждого хайлайта
            print(f"📚 Получение словарных значений...", flush=True)
            for highlight in highlights:
                try:
                    meanings = ai_client.get_dictionary_meanings(highlight.highlight)
                    highlight.dictionary_meanings = meanings
                except Exception as e:
                    print(f"⚠️ Ошибка получения значений для '{highlight.highlight}': {e}", flush=True)

            # Добавляем переводы
            highlights = await self._add_translations(highlights, ai_client)

            print(f"✅ v1_basic: найдено {len(highlights)} хайлайтов", flush=True)
            return highlights

        except Exception as e:
            print(f"❌ Ошибка v1_basic промпта: {e}", flush=True)
            return []
    
    def _create_prompt(self, text: str, target_count: str) -> str:
        """Создает промпт для анализа"""
        return f"""
Ты — эксперт по продвинутой английской лексике, которая делает речь выразительной, натуральной и стильной. Найди {target_count} слов и выражений из текста, которые действительно стоят изучения.

Проанализируй этот английский текст:
"{text}"

БРАТЬ (приоритет):
- Выразительные, точные, "живые" слова, которые часто встречаются в качественном медиа-контенте.
- Сильные коллокации (например: "compelling argument", "sheer determination").
- Идиомы, метафоры, устойчивые выражения.
- Продвинутые фразовые глаголы.
- Профессиональные термины, если они широко используются (например: "leverage", "scalability", "breakthrough").

НЕ БРАТЬ:
- Узкую, сухую техническую терминологию, понятную только специалистам.
- Частотную базовую лексику (простые слова, которые все знают).
- Списки слов, перечисления через запятую.
- Длинные описания или фрагменты предложений.

КРИТИЧЕСКИ ВАЖНО: используй только слова и фразы которые ТОЧНО есть в исходном тексте!
НЕ придумывай и НЕ добавляй слова которых нет в тексте!

ТРЕБОВАНИЯ:
- Бери максимум потенциально полезных выражений. Если сомневаешься — бери.
- "highlight" должен быть одним словом или короткой фразой.
- "context" — только ОДНО предложение из текста, которое ОБЯЗАТЕЛЬНО содержит выбранное слово/фразу. 
- ВАЖНО: слово/фраза из "highlight" должно точно присутствовать в "context".
- "context_translation" — это перевод ТОЛЬКО выбранного слова/выражения (кратко, без пояснений).

Формат ответа — только массив JSON:
[
  {{
    "highlight": "слово или выражение",
    "context": "одно предложение из текста",
    "context_translation": "перевод слова/выражения"
  }}
]

Перед тем как вернуть ответ:
Проверь, что базовые и узкотехнические слова исключены, а лучшие выразительные выражения включены.

Верни только массив JSON.
"""

    def _parse_response(self, response: str) -> List[Highlight]:
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
                
                highlight = Highlight(
                    highlight=item["highlight"],
                    context=item["context"],
                    context_translation=item.get("context_translation", ""),
                    english_example=f"Example: {item['context']}",
                    russian_example="",  # Будет заполнено через переводчик
                    cefr_level="C1",
                    importance_score=85,
                    dictionary_meanings=[],
                    why_interesting="Выразительная лексика для стильной речи"
                )
                highlights.append(highlight)
            
            return highlights
            
        except Exception as e:
            print(f"❌ Ошибка парсинга v1_basic ответа: {e}", flush=True)
            print(f"❌ Ответ был: {response[:200]}...", flush=True)
            return []
    
    def _validate_highlight_data(self, item: dict) -> bool:
        """Проверяет корректность данных хайлайта"""
        required_fields = ["highlight", "context"]
        for field in required_fields:
            if field not in item or not item[field]:
                return False
        
        # Проверяем что хайлайт действительно есть в контексте
        highlight_text = item["highlight"].lower()
        context_text = item["context"].lower()
        
        # Для фраз проверяем по частям
        if ' ' in highlight_text:
            for word in highlight_text.split():
                if len(word) > 2 and word not in context_text:
                    print(f"⚠️ v1_basic: пропускаю '{item['highlight']}' - слово '{word}' не найдено в контексте", flush=True)
                    return False
        else:
            # Для одного слова
            if highlight_text not in context_text:
                print(f"⚠️ v1_basic: пропускаю '{item['highlight']}' - не найдено в контексте", flush=True)
                return False
        
        return True
    
    async def _add_translations(self, highlights: List[Highlight], ai_client) -> List[Highlight]:
        """Добавляет переводы к хайлайтам"""
        for highlight in highlights:
            try:
                if not highlight.russian_example:
                    # Переводим только само слово/фразу, а не весь контекст
                    translation = await ai_client.translate_text(highlight.highlight, "ru")
                    highlight.russian_example = translation
            except Exception as e:
                print(f"⚠️ Ошибка перевода '{highlight.highlight}': {e}", flush=True)
        
        return highlights