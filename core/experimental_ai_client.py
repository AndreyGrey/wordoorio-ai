#!/usr/bin/env python3
"""
🧪 ЭКСПЕРИМЕНТАЛЬНЫЙ клиент для dual-prompt анализа
Копия YandexAIClient с поддержкой двух параллельных промптов
"""

import os
import re
import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

@dataclass
class LinguisticHighlight:
    """Лингвистический хайлайт"""
    highlight: str              # Слово или фраза
    context: str               # Контекст из текста
    context_translation: str   # Перевод контекста
    english_example: str       # Пример на английском
    russian_example: str       # Пример на русском
    cefr_level: str           # A1-C2
    importance_score: int      # 0-100
    dictionary_meanings: List[str]  # Словарные значения
    why_interesting: str       # Почему интересен для изучения
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        from dataclasses import asdict
        return asdict(self)

class ExperimentalYandexAIClient:
    """🧪 Экспериментальный клиент для dual-prompt анализа"""
    
    def __init__(self):
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.iam_token = self._get_iam_token()
        self.gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.translate_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        
    def _get_iam_token(self) -> str:
        """Получает IAM токен для Yandex Cloud"""
        return os.getenv('YANDEX_IAM_TOKEN', '')
    
    async def analyze_dual_highlights(self, text: str) -> Dict[str, List[LinguisticHighlight]]:
        """
        🧪 ЭКСПЕРИМЕНТАЛЬНЫЙ: Анализирует текст двумя параллельными промптами
        Возвращает: {"words": [...], "phrases": [...]}
        """
        print(f"🧪 Экспериментальный dual-prompt анализ...", flush=True)
        
        try:
            # Два параллельных запроса к Yandex GPT
            words_prompt = self._create_words_prompt(text)
            phrases_prompt = self._create_phrases_prompt(text)
            
            # Запросы выполняются последовательно для экономии ресурсов
            words_response = await self._request_yandex_gpt(words_prompt)
            phrases_response = await self._request_yandex_gpt(phrases_prompt)
            
            # Парсим оба ответа
            words = self._parse_gpt_response(words_response)
            phrases = self._parse_gpt_response(phrases_response)
            
            # Добавляем переводы
            words = await self._add_translations(words)
            phrases = await self._add_translations(phrases)
            
            result = {
                "words": words,
                "phrases": phrases
            }
            
            print(f"✅ Найдено {len(words)} слов и {len(phrases)} фраз", flush=True)
            return result
            
        except Exception as e:
            print(f"❌ Ошибка экспериментального анализа: {e}", flush=True)
            return {"words": [], "phrases": []}
    
    def _create_words_prompt(self, text: str) -> str:
        """Создает промпт для анализа слов (оригинальный)"""
        return f"""
Ты — эксперт по продвинутой английской лексике, которая делает речь выразительной, натуральной и стильной. Найди ВСЕ слова и выражения из текста, которые действительно стоят изучения.

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
    
    def _create_phrases_prompt(self, text: str) -> str:
        """Создает промпт для анализа продвинутых глагольных конструкций"""
        return f"""
Ты — эксперт по продвинутым речевым конструкциям английского языка. Найди СТИЛЬНЫЕ ГЛАГОЛЬНЫЕ ФРАЗЫ и ВЫРАЗИТЕЛЬНЫЕ РЕЧЕВЫЕ ОБОРОТЫ, которые делают речь профессиональной и естественной.

Проанализируй этот английский текст:
"{text}"

БРАТЬ (только продвинутые конструкции 3+ слов):
- Изощренные речевые паттерны с глаголами
- Стильные глагольные связки и обороты  
- Выразительные модальные конструкции
- Профессиональные речевые обороты
- Сложные фразовые глаголы с дополнениями

НЕ БРАТЬ:
- Базовые конструкции уровня школьной программы
- Простые модальные глаголы с одним словом
- Примитивные связки и переходы
- Очевидные повседневные фразы

ФОКУС: Только конструкции, которые выделяют речь как продвинутую и стильную. Ищи разнообразные паттерны.

JSON формат: [{{"highlight": "продвинутая фраза", "context": "предложение", "context_translation": "перевод фразы"}}]
"""
    
    async def _request_yandex_gpt(self, prompt: str) -> Dict[str, Any]:
        """Отправляет запрос к Yandex GPT"""
        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        # Приблизительный подсчет токенов (1 токен ≈ 4 символа для английского)
        input_tokens = len(prompt) // 4
        print(f"💰 Приблизительно {input_tokens} входных токенов", flush=True)
        
        # Реальный запрос к Yandex GPT
        if not self.iam_token:
            print("⚠️ Yandex IAM токен не найден, использую fallback")
            return {"result": {"alternatives": [{"message": {"text": "[]"}}]}}
        
        try:
            response = requests.post(self.gpt_url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                # Подсчет выходных токенов
                response_text = result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
                output_tokens = len(response_text) // 4
                total_cost = (input_tokens * 0.0006) + (output_tokens * 0.0012)  # Примерные цены в рублях за 1K токенов
                print(f"💰 ~{output_tokens} выходных токенов | Стоимость: ~{total_cost:.3f}₽", flush=True)
                return result
            else:
                print(f"⚠️ Yandex GPT ошибка {response.status_code}: {response.text[:200]}...")
                return {"result": {"alternatives": [{"message": {"text": "[]"}}]}}
        except Exception as e:
            print(f"⚠️ Ошибка запроса к Yandex GPT: {e}")
            return {"result": {"alternatives": [{"message": {"text": "[]"}}]}}
    
    def _parse_gpt_response(self, response: Dict[str, Any]) -> List[LinguisticHighlight]:
        """Парсит ответ от Yandex GPT"""
        try:
            # Извлекаем текст ответа
            text = response["result"]["alternatives"][0]["message"]["text"]
            
            # Очищаем от markdown разметки
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]  # Убираем первый ```
                if text.startswith("json"):
                    text = text[4:]  # Убираем "json"
                text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()
            
            # Парсим JSON
            highlights_data = json.loads(text)
            
            highlights = []
            for item in highlights_data:
                # Проверяем, что хайлайт действительно есть в контексте
                highlight_text = item["highlight"].lower()
                context_text = item["context"].lower()
                
                # Для фраз проверяем по частям
                words_in_context = True
                if ' ' in highlight_text:
                    for word in highlight_text.split():
                        if len(word) > 2 and word not in context_text:
                            words_in_context = False
                            break
                else:
                    # Для одного слова
                    words_in_context = highlight_text in context_text
                
                # Пропускаем хайлайты, которых нет в контексте
                if not words_in_context:
                    print(f"⚠️ Пропускаю хайлайт '{item['highlight']}' - не найден в контексте")
                    continue
                
                highlight = LinguisticHighlight(
                    highlight=item["highlight"],
                    context=item["context"],
                    context_translation=item.get("context_translation", ""),
                    english_example=f"Example: {item['context']}",
                    russian_example="",  # Будет заполнено через Yandex Translate
                    cefr_level="C1",  # Фиксированное значение - все слова продвинутые
                    importance_score=85,  # Фиксированное значение
                    dictionary_meanings=[],  # Будет заполнено через Yandex Translate
                    why_interesting="Выразительная лексика для стильной речи"
                )
                highlights.append(highlight)
            
            return highlights
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга GPT ответа: {e}", flush=True)
            return []
    
    async def _add_translations(self, highlights: List[LinguisticHighlight]) -> List[LinguisticHighlight]:
        """Добавляет словарные значения через Yandex Translate"""
        for highlight in highlights:
            try:
                # Получаем словарные значения для слова
                dictionary_meanings = self._get_dictionary_meanings(highlight.highlight)
                highlight.dictionary_meanings = dictionary_meanings
                
                # Переводим только сам хайлайт, а не весь пример
                highlight.russian_example = await self._translate_text(highlight.highlight)
                
            except Exception as e:
                print(f"⚠️ Ошибка получения словарных значений для '{highlight.highlight}': {e}", flush=True)
                highlight.dictionary_meanings = [f"Значение: {highlight.highlight}"]
                highlight.russian_example = f"Перевод: {highlight.highlight}"
        
        return highlights
    
    def _get_dictionary_meanings(self, word: str) -> List[str]:
        """Получает словарные значения слова через Free Dictionary API"""
        try:            
            # Очищаем слово от лишних символов
            clean_word = re.sub(r'[^a-zA-Z\s-]', '', word.strip().lower())
            if not clean_word:
                return []
            
            # Не запрашиваем определения для фраз (больше одного слова)
            if ' ' in clean_word:
                return []
            
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                meanings = []
                
                # Извлекаем определения из API ответа
                for entry in data[:2]:  # Первые 2 записи
                    for meaning in entry.get('meanings', [])[:2]:  # Первые 2 значения
                        part_of_speech = meaning.get('partOfSpeech', '')
                        for definition in meaning.get('definitions', [])[:1]:  # Первое определение
                            def_text = definition.get('definition', '')
                            if def_text:
                                # Переводим определение на русский
                                russian_def = self._translate_definition_sync(def_text)
                                meanings.append(russian_def)
                
                return meanings[:3] if meanings else []
            else:
                return []
                        
        except Exception as e:
            return []

    def _translate_definition_sync(self, definition: str) -> str:
        """Переводит английское определение на русский через Yandex Translate (синхронно)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.iam_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "folderId": self.folder_id,
                "texts": [definition],
                "sourceLanguageCode": "en",
                "targetLanguageCode": "ru"
            }
            
            response = requests.post(
                "https://translate.api.cloud.yandex.net/translate/v2/translate",
                headers=headers, 
                json=data, 
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                translation = result["translations"][0]["text"]
                return translation
            else:
                return definition  # Возвращаем оригинал если перевод не удался
                
        except Exception as e:
            print(f"⚠️ Ошибка перевода определения: {e}", flush=True)
            return definition  # Возвращаем оригинал

    async def _translate_text(self, text: str) -> str:
        """Переводит текст через Yandex Translate"""
        try:
            # Пока возвращаем заглушку
            return f"[ПЕРЕВОД: {text}]"
            
        except Exception as e:
            print(f"⚠️ Ошибка Yandex Translate: {e}", flush=True)
            return f"[ПЕРЕВОД: {text}]"

def test_experimental_client():
    """Тест экспериментального клиента"""
    import asyncio
    
    async def run_test():
        print("🧪 ТЕСТ EXPERIMENTAL CLIENT")
        print("=" * 50)
        
        client = ExperimentalYandexAIClient()
        
        test_text = """
        Machine learning algorithms analyze complex patterns in massive datasets. 
        These sophisticated methods revolutionize artificial intelligence research.
        Scientists develop innovative approaches to solve computational problems.
        """
        
        result = await client.analyze_dual_highlights(test_text.strip())
        
        print(f"\n📚 Найдено {len(result['words'])} слов и {len(result['phrases'])} фраз:")
        
        print(f"\n🔤 СЛОВА ({len(result['words'])}):")
        for i, h in enumerate(result['words']):
            print(f"{i+1}. {h.highlight}")
        
        print(f"\n💬 ФРАЗЫ ({len(result['phrases'])}):")
        for i, h in enumerate(result['phrases']):
            print(f"{i+1}. {h.highlight}")
        
        print("\n✅ Тест завершен!")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_experimental_client()