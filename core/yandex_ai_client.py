#!/usr/bin/env python3
"""
Клиент для Yandex AI Studio API
Поддержка Yandex GPT и Yandex Translate
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

class YandexAIClient:
    """Клиент для работы с Yandex AI Studio"""
    
    def __init__(self):
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.iam_token = self._get_iam_token()
        self.gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.translate_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        
    def _get_iam_token(self) -> str:
        """Получает IAM токен для Yandex Cloud"""
        # Попробуем получить токен из переменной окружения
        # Пока используем заглушку
        return os.getenv('YANDEX_IAM_TOKEN', '')
    
    async def analyze_linguistic_highlights(self, text: str) -> List[LinguisticHighlight]:
        """
        Анализирует текст и выделяет 3-30 лингвистических хайлайтов
        """
        print(f"🧠 Анализирую лингвистические хайлайты в тексте...", flush=True)
        
        # Определяем количество хайлайтов в зависимости от длины текста
        word_count = len(text.split())
        if word_count < 20:
            target_count = "3-5"
        elif word_count < 50:
            target_count = "5-10"
        elif word_count < 100:
            target_count = "10-20"
        else:
            target_count = "15-30"
        
        prompt = self._create_highlights_prompt(text, target_count)
        
        try:
            # Запрос к Yandex GPT
            gpt_response = await self._request_yandex_gpt(prompt)
            
            # Парсим ответ и создаем хайлайты
            highlights = self._parse_gpt_response(gpt_response)
            
            # Добавляем переводы через Yandex Translate
            highlights = await self._add_translations(highlights)
            
            print(f"✅ Найдено {len(highlights)} хайлайтов", flush=True)
            return highlights
            
        except Exception as e:
            print(f"❌ Ошибка анализа хайлайтов: {e}", flush=True)
            # Fallback на простой анализ
            return self._fallback_analysis(text)
    
    def _create_phrases_prompt(self, text: str) -> str:
        """Создает промпт для анализа фраз и словосочетаний"""
        return f"""
Ты — эксперт по английскому языку. Найди интересные словосочетания и нативные обороты речи из текста — фразы, которые звучат естественно и профессионально.

Проанализируй этот английский текст:
"{text}"

БРАТЬ (только фразы 2+ слов):
- Естественные словосочетания, которые носители используют как единое целое
- Фразовые глаголы в контексте  
- Профессиональные термины и устойчивые сочетания
- Идиоматические обороты и связки
- Выразительные сочетания, характерные для качественного письма

НЕ БРАТЬ:
- Отдельные слова
- Случайные сочетания слов без устойчивости
- Простые предлогные фразы

Ищи фразы, которые изучающие английский захотели бы запомнить и использовать.

JSON формат: [{{"highlight": "фраза", "context": "предложение", "context_translation": "перевод фразы"}}]
"""
    
    def _create_highlights_prompt(self, text: str, target_count: str) -> str:
        """Создает промпт для анализа хайлайтов"""
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
                
                # Переводим пример
                highlight.russian_example = await self._translate_text(highlight.english_example)
                
            except Exception as e:
                print(f"⚠️ Ошибка получения словарных значений для '{highlight.highlight}': {e}", flush=True)
                highlight.dictionary_meanings = [f"Значение: {highlight.highlight}"]
                highlight.russian_example = f"Пример: {highlight.english_example}"
        
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

    async def _translate_definition(self, definition: str) -> str:
        """Переводит английское определение на русский через Yandex Translate"""
        try:
            # Используем реальный Yandex Translate API
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
        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "folderId": self.folder_id,
            "texts": [text],
            "sourceLanguageCode": "en",
            "targetLanguageCode": "ru"
        }
        
        try:
            # TODO: Заменить на реальный запрос
            # response = requests.post(self.translate_url, headers=headers, json=data)
            # result = response.json()
            # return result["translations"][0]["text"]
            
            # Пока возвращаем заглушку
            return f"[ПЕРЕВОД: {text}]"
            
        except Exception as e:
            print(f"⚠️ Ошибка Yandex Translate: {e}", flush=True)
            return f"[ПЕРЕВОД: {text}]"
    
    def _fallback_analysis(self, text: str) -> List[LinguisticHighlight]:
        """Fallback анализ если GPT недоступен"""
        print("🔄 Использую fallback анализ...", flush=True)
        
        # Простой анализ для демонстрации
        words = text.split()
        interesting_words = [w for w in words if len(w) > 6 and w.isalpha()][:5]
        
        highlights = []
        for word in interesting_words:
            highlight = LinguisticHighlight(
                highlight=word.lower(),
                context=f"Found in: ...{word}...",
                context_translation=f"Найдено в: ...{word}...",
                english_example=f"Example with {word}",
                russian_example=f"Пример с {word}",
                cefr_level="B2",
                importance_score=70,
                dictionary_meanings=[f"Значение слова {word}"],
                why_interesting=f"Длинное слово, потенциально интересное"
            )
            highlights.append(highlight)
        
        return highlights

def test_yandex_ai_client():
    """Тест клиента Yandex AI"""
    import asyncio
    
    async def run_test():
        print("🧪 ТЕСТ YANDEX AI CLIENT")
        print("=" * 50)
        
        client = YandexAIClient()
        
        test_text = """
        Machine learning algorithms analyze complex patterns in massive datasets. 
        These sophisticated methods revolutionize artificial intelligence research.
        Scientists develop innovative approaches to solve computational problems.
        """
        
        highlights = await client.analyze_linguistic_highlights(test_text.strip())
        
        print(f"\n📚 Найдено {len(highlights)} хайлайтов:")
        for i, h in enumerate(highlights):
            print(f"\n{i+1}. {h.highlight} ({h.cefr_level})")
            print(f"   📝 Контекст: {h.context}")
            print(f"   🇷🇺 Перевод: {h.context_translation}")
            print(f"   💡 Почему интересен: {h.why_interesting}")
            print(f"   📊 Важность: {h.importance_score}/100")
        
        print("\n✅ Тест завершен!")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_yandex_ai_client()