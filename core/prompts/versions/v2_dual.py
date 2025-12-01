#!/usr/bin/env python3
"""
🧪 V2 DUAL PROMPT - Экспериментальная версия

Два параллельных промпта: один для слов, другой для фраз.
Повышенная точность за счет специализации промптов.
"""

import json
import asyncio
from typing import List
from contracts.analysis_contracts import PromptStrategy, PromptMetadata, Highlight


class DualPromptV2(PromptStrategy):
    """Экспериментальная dual-prompt версия"""
    
    def get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            id="v2_dual",
            name="Dual-Prompt Experimental",
            description="Два специализированных промпта: слова + фразы",
            is_stable=False,
            created_at="2024-11-15",
            performance_score=92.0,
            estimated_cost=0.8
        )
    
    async def analyze_text(self, text: str, ai_client) -> List[Highlight]:
        """Анализ текста через два параллельных промпта"""
        print(f"🧪 Анализ через v2_dual промпт...", flush=True)
        
        try:
            # Два параллельных запроса
            words_prompt = self._create_words_prompt(text)
            phrases_prompt = self._create_phrases_prompt(text)
            
            print(f"🧪 Отправляем запрос для слов...", flush=True)
            words_response = await ai_client.request_gpt(words_prompt)
            
            print(f"🧪 Отправляем запрос для фраз...", flush=True)
            phrases_response = await ai_client.request_gpt(phrases_prompt)
            
            # Парсим оба ответа
            words = self._parse_response(words_response, "words")
            phrases = self._parse_response(phrases_response, "phrases")
            
            print(f"🧪 Найдено {len(words)} слов и {len(phrases)} фраз", flush=True)
            
            # Объединяем результаты
            all_highlights = words + phrases
            
            # Добавляем переводы
            all_highlights = await self._add_translations(all_highlights, ai_client)
            
            print(f"✅ v2_dual: итого {len(all_highlights)} хайлайтов", flush=True)
            return all_highlights
            
        except Exception as e:
            print(f"❌ Ошибка v2_dual промпта: {e}", flush=True)
            return []
    
    def _create_words_prompt(self, text: str) -> str:
        """Промпт для поиска отдельных слов"""
        return f"""
Ты — эксперт по английской лексике. Найди ТОЛЬКО ОТДЕЛЬНЫЕ ВЫРАЗИТЕЛЬНЫЕ СЛОВА (не фразы!) из текста.

Проанализируй этот английский текст:
"{text}"

БРАТЬ (только отдельные слова):
- Выразительные прилагательные (compelling, crucial, remarkable)
- Точные глаголы (leverage, optimize, streamline)  
- Продвинутые существительные (paradigm, framework, methodology)
- Наречия высокого уровня (substantially, meticulously, predominantly)

НЕ БРАТЬ:
- Словосочетания и фразы (это для другого промпта)
- Базовую лексику (good, bad, big, small)
- Технические термины узкой области

КРИТИЧЕСКИ ВАЖНО: используй только слова которые ТОЧНО есть в исходном тексте!

JSON формат: [{{"highlight": "одно_слово", "context": "предложение", "context_translation": "перевод_слова"}}]
"""

    def _create_phrases_prompt(self, text: str) -> str:
        """Промпт для поиска фраз и выражений"""  
        return f"""
Ты — эксперт по английским фразам. Найди ТОЛЬКО ФРАЗЫ И ВЫРАЖЕНИЯ (2+ слова) из текста.

Проанализируй этот английский текст:
"{text}"

БРАТЬ (только фразы 2+ слов):
- Устойчивые словосочетания (cutting edge, state of the art)
- Фразовые глаголы в контексте (break down, figure out)
- Идиоматические выражения (piece of cake, break the ice)
- Профессиональные термины (best practices, data-driven approach)
- Коллокации (make a decision, take action)

НЕ БРАТЬ:
- Отдельные слова (это для другого промпта)
- Случайные сочетания слов
- Простые предлогные фразы

КРИТИЧЕСКИ ВАЖНО: используй только фразы которые ТОЧНО есть в данном тексте!

JSON формат: [{{"highlight": "фраза из нескольких слов", "context": "предложение", "context_translation": "перевод_фразы"}}]
"""

    def _parse_response(self, response: str, prompt_type: str) -> List[Highlight]:
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
                if not self._validate_highlight_data(item, prompt_type):
                    continue
                
                highlight = Highlight(
                    highlight=item["highlight"],
                    context=item["context"],
                    context_translation=item.get("context_translation", ""),
                    english_example=f"Example: {item['context']}",
                    russian_example="",  # Будет заполнено через переводчик
                    cefr_level="C1",
                    importance_score=90,  # Dual-prompt дает более качественные результаты
                    dictionary_meanings=[],
                    why_interesting=f"Выразительная {prompt_type[:-1]} для продвинутого уровня"
                )
                highlights.append(highlight)
            
            print(f"✅ v2_dual {prompt_type}: распознано {len(highlights)} элементов", flush=True)
            return highlights
            
        except Exception as e:
            print(f"❌ Ошибка парсинга v2_dual {prompt_type}: {e}", flush=True)
            print(f"❌ Ответ был: {response[:200]}...", flush=True)
            return []
    
    def _validate_highlight_data(self, item: dict, prompt_type: str) -> bool:
        """Проверяет корректность данных хайлайта"""
        required_fields = ["highlight", "context"]
        for field in required_fields:
            if field not in item or not item[field]:
                return False
        
        highlight_text = item["highlight"].lower()
        context_text = item["context"].lower()
        
        # Дополнительная валидация для dual-prompt
        if prompt_type == "words":
            # Для слов - не должно быть пробелов
            if ' ' in highlight_text:
                print(f"⚠️ v2_dual words: пропускаю '{item['highlight']}' - должно быть одно слово", flush=True)
                return False
        else:  # phrases
            # Для фраз - должно быть 2+ слов
            if ' ' not in highlight_text:
                print(f"⚠️ v2_dual phrases: пропускаю '{item['highlight']}' - должна быть фраза", flush=True)
                return False
        
        # Проверяем что хайлайт действительно есть в контексте
        if ' ' in highlight_text:
            # Для фраз проверяем по частям
            for word in highlight_text.split():
                if len(word) > 2 and word not in context_text:
                    print(f"⚠️ v2_dual {prompt_type}: пропускаю '{item['highlight']}' - слово '{word}' не найдено", flush=True)
                    return False
        else:
            # Для одного слова
            if highlight_text not in context_text:
                print(f"⚠️ v2_dual {prompt_type}: пропускаю '{item['highlight']}' - не найдено в контексте", flush=True)
                return False
        
        return True
    
    async def _add_translations(self, highlights: List[Highlight], ai_client) -> List[Highlight]:
        """Добавляет переводы к хайлайтам"""
        for highlight in highlights:
            try:
                if not highlight.russian_example:
                    # Переводим только само слово/фразу
                    translation = await ai_client.translate_text(highlight.highlight, "ru")
                    highlight.russian_example = translation
            except Exception as e:
                print(f"⚠️ Ошибка перевода '{highlight.highlight}': {e}", flush=True)
        
        return highlights