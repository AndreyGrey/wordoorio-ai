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
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

@dataclass
class LinguisticHighlight:
    """Лингвистический хайлайт (legacy - используйте Highlight из contracts)"""
    highlight: str              # Слово или фраза
    context: str               # Контекст из текста
    highlight_translation: str  # Перевод слова/фразы
    cefr_level: str           # A1-C2
    importance_score: int      # 0-100
    dictionary_meanings: List[str] = field(default_factory=list)  # Словарные значения
    why_interesting: str = ""  # Почему интересен для изучения
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        from dataclasses import asdict
        return asdict(self)

class YandexAIClient:
    """Клиент для работы с Yandex AI Studio"""

    # Список примитивных/базовых слов, которые не нужно проверять в словаре
    PRIMITIVE_WORDS = {
        # Артикли
        'a', 'an', 'the',
        # Предлоги
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'under', 'over', 'across', 'off', 'out', 'up', 'down',
        # Местоимения
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
        'this', 'that', 'these', 'those', 'who', 'what', 'which', 'whom', 'whose',
        # Базовые глаголы
        'be', 'is', 'are', 'was', 'were', 'been', 'being', 'am',
        'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'done',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must',
        'get', 'got', 'getting', 'go', 'goes', 'went', 'going', 'gone',
        'make', 'makes', 'made', 'making',
        'take', 'takes', 'took', 'taking', 'taken',
        'come', 'comes', 'came', 'coming',
        'give', 'gives', 'gave', 'giving', 'given',
        'know', 'knows', 'knew', 'knowing', 'known',
        'see', 'sees', 'saw', 'seeing', 'seen',
        'use', 'uses', 'used', 'using',
        'find', 'finds', 'found', 'finding',
        'tell', 'tells', 'told', 'telling',
        'ask', 'asks', 'asked', 'asking',
        'want', 'wants', 'wanted', 'wanting',
        'need', 'needs', 'needed', 'needing',
        'try', 'tries', 'tried', 'trying',
        'call', 'calls', 'called', 'calling',
        'put', 'puts', 'putting',
        'say', 'says', 'said', 'saying',
        'keep', 'keeps', 'kept', 'keeping',
        'let', 'lets', 'letting',
        'begin', 'begins', 'began', 'beginning', 'begun',
        'seem', 'seems', 'seemed', 'seeming',
        'help', 'helps', 'helped', 'helping',
        'talk', 'talks', 'talked', 'talking',
        'turn', 'turns', 'turned', 'turning',
        'start', 'starts', 'started', 'starting',
        'show', 'shows', 'showed', 'showing', 'shown',
        'hear', 'hears', 'heard', 'hearing',
        'play', 'plays', 'played', 'playing',
        'run', 'runs', 'ran', 'running',
        'move', 'moves', 'moved', 'moving',
        'like', 'likes', 'liked', 'liking',
        'live', 'lives', 'lived', 'living',
        'believe', 'believes', 'believed', 'believing',
        'bring', 'brings', 'brought', 'bringing',
        'happen', 'happens', 'happened', 'happening',
        'write', 'writes', 'wrote', 'writing', 'written',
        'sit', 'sits', 'sat', 'sitting',
        'stand', 'stands', 'stood', 'standing',
        'lose', 'loses', 'lost', 'losing',
        'pay', 'pays', 'paid', 'paying',
        'meet', 'meets', 'met', 'meeting',
        'include', 'includes', 'included', 'including',
        'continue', 'continues', 'continued', 'continuing',
        'set', 'sets', 'setting',
        'learn', 'learns', 'learned', 'learning', 'learnt',
        'change', 'changes', 'changed', 'changing',
        'lead', 'leads', 'led', 'leading',
        'understand', 'understands', 'understood', 'understanding',
        'watch', 'watches', 'watched', 'watching',
        'follow', 'follows', 'followed', 'following',
        'stop', 'stops', 'stopped', 'stopping',
        'create', 'creates', 'created', 'creating',
        'speak', 'speaks', 'spoke', 'speaking', 'spoken',
        'read', 'reads', 'reading',
        'spend', 'spends', 'spent', 'spending',
        'grow', 'grows', 'grew', 'growing', 'grown',
        'open', 'opens', 'opened', 'opening',
        'walk', 'walks', 'walked', 'walking',
        'win', 'wins', 'won', 'winning',
        'teach', 'teaches', 'taught', 'teaching',
        'offer', 'offers', 'offered', 'offering',
        'remember', 'remembers', 'remembered', 'remembering',
        'consider', 'considers', 'considered', 'considering',
        'appear', 'appears', 'appeared', 'appearing',
        'buy', 'buys', 'bought', 'buying',
        'serve', 'serves', 'served', 'serving',
        'die', 'dies', 'died', 'dying',
        'send', 'sends', 'sent', 'sending',
        'build', 'builds', 'built', 'building',
        'stay', 'stays', 'stayed', 'staying',
        'fall', 'falls', 'fell', 'falling', 'fallen',
        'cut', 'cuts', 'cutting',
        'reach', 'reaches', 'reached', 'reaching',
        'kill', 'kills', 'killed', 'killing',
        'raise', 'raises', 'raised', 'raising',
        'pass', 'passes', 'passed', 'passing',
        'sell', 'sells', 'sold', 'selling',
        'decide', 'decides', 'decided', 'deciding',
        'return', 'returns', 'returned', 'returning',
        'explain', 'explains', 'explained', 'explaining',
        'hope', 'hopes', 'hoped', 'hoping',
        'develop', 'develops', 'developed', 'developing',
        'carry', 'carries', 'carried', 'carrying',
        'break', 'breaks', 'broke', 'breaking', 'broken',
        # Базовые прилагательные
        'good', 'better', 'best', 'bad', 'worse', 'worst', 'big', 'bigger', 'biggest',
        'small', 'smaller', 'smallest', 'new', 'newer', 'newest', 'old', 'older', 'oldest',
        'great', 'greater', 'greatest', 'high', 'higher', 'highest', 'low', 'lower', 'lowest',
        'long', 'longer', 'longest', 'short', 'shorter', 'shortest', 'early', 'earlier', 'earliest',
        'late', 'later', 'latest', 'young', 'younger', 'youngest', 'important', 'more', 'most',
        'large', 'larger', 'largest', 'little', 'less', 'least', 'own', 'other', 'another',
        'same', 'few', 'public', 'able', 'such', 'only', 'first', 'last', 'next', 'different',
        'many', 'much', 'several', 'every', 'each', 'some', 'any', 'all', 'both', 'either',
        'neither', 'right', 'left', 'true', 'false', 'real', 'sure', 'full', 'half', 'whole',
        'free', 'ready', 'easy', 'hard', 'simple', 'clear', 'close', 'open', 'strong', 'weak',
        # Базовые наречия
        'very', 'too', 'so', 'just', 'now', 'then', 'here', 'there', 'where', 'when', 'why',
        'how', 'also', 'well', 'back', 'only', 'even', 'still', 'already', 'yet', 'again',
        'never', 'always', 'often', 'sometimes', 'usually', 'today', 'tomorrow', 'yesterday',
        'soon', 'far', 'away', 'together', 'however', 'perhaps', 'maybe', 'quite', 'rather',
        'almost', 'enough', 'too', 'nearly', 'probably', 'possibly', 'certainly', 'definitely',
        # Базовые существительные
        'time', 'year', 'day', 'way', 'man', 'woman', 'child', 'children', 'people', 'person',
        'thing', 'things', 'life', 'world', 'hand', 'part', 'place', 'case', 'week', 'company',
        'system', 'program', 'question', 'work', 'government', 'number', 'night', 'point', 'home',
        'water', 'room', 'mother', 'father', 'area', 'money', 'story', 'fact', 'month', 'lot',
        'right', 'study', 'book', 'eye', 'job', 'word', 'business', 'issue', 'side', 'kind',
        'head', 'house', 'service', 'friend', 'problem', 'power', 'end', 'member', 'law', 'car',
        'city', 'name', 'team', 'minute', 'idea', 'body', 'information', 'back', 'parent', 'face',
        'others', 'level', 'office', 'door', 'health', 'art', 'war', 'history', 'party', 'result',
        'change', 'morning', 'reason', 'research', 'girl', 'guy', 'moment', 'air', 'teacher', 'force',
        'education',
        # Союзы
        'and', 'or', 'but', 'so', 'because', 'if', 'when', 'while', 'although', 'though',
        'since', 'until', 'unless', 'than', 'whether', 'nor', 'yet',
        # Другие служебные слова
        'not', 'no', 'yes', 'ok', 'okay', 'please', 'thank', 'thanks', 'sorry', 'well',
    }

    def __init__(self):
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.iam_token = self._get_iam_token()
        self.dict_api_key = os.getenv('YANDEX_DICT_API_KEY', '')
        self.gpt_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.translate_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        self.dict_url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"

    def _get_iam_token(self) -> str:
        """Получает IAM токен для Yandex Cloud

        Приоритет:
        1. Environment variable (для локальной разработки)
        2. Metadata Service (для Serverless Container с Service Account)
        """
        # Сначала проверяем переменную окружения (для локальной разработки)
        env_token = os.getenv('YANDEX_IAM_TOKEN', '')
        if env_token:
            return env_token

        # Получаем токен через Metadata Service (для Serverless Container)
        try:
            metadata_url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
            headers = {'Metadata-Flavor': 'Google'}  # Yandex Cloud использует совместимый с GCP формат

            response = requests.get(metadata_url, headers=headers, timeout=5)

            if response.status_code == 200:
                token_data = response.json()
                iam_token = token_data.get('access_token', '')
                print(f"✅ IAM токен получен через Metadata Service", flush=True)
                return iam_token
            else:
                print(f"⚠️ Metadata Service недоступен: {response.status_code}", flush=True)
                return ''

        except Exception as e:
            print(f"⚠️ Не удалось получить токен через Metadata Service: {e}", flush=True)
            return ''
    
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

JSON формат: [{{"highlight": "фраза", "context": "предложение", "highlight_translation": "перевод фразы"}}]
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
- "highlight_translation" — это перевод ТОЛЬКО выбранного слова/выражения (кратко, без пояснений).

Формат ответа — только массив JSON:
[
  {{
    "highlight": "слово или выражение",
    "context": "одно предложение из текста",
    "highlight_translation": "перевод слова/выражения"
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
                    highlight_translation=item.get("highlight_translation", item.get("context_translation", "")),
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
        """Добавляет словарные значения через Yandex Translate (legacy method)"""
        for highlight in highlights:
            try:
                # Получаем словарные значения для слова
                dictionary_meanings = self._get_dictionary_meanings(highlight.highlight)
                highlight.dictionary_meanings = dictionary_meanings

            except Exception as e:
                print(f"⚠️ Ошибка получения словарных значений для '{highlight.highlight}': {e}", flush=True)
                highlight.dictionary_meanings = [f"Значение: {highlight.highlight}"]

        return highlights
    
    def _is_primitive_word(self, word: str) -> bool:
        """Проверяет является ли слово примитивным/базовым"""
        clean_word = word.strip().lower()

        # Проверяем в списке примитивных слов
        if clean_word in self.PRIMITIVE_WORDS:
            return True

        # Слишком короткие слова (меньше 4 букв) - примитивные
        if len(clean_word) < 4:
            return True

        return False

    # Старый метод Free Dictionary API удален - теперь используем Yandex Dictionary API

    def _get_yandex_dict_translations(self, word: str) -> List[str]:
        """Получает альтернативные русские переводы через Yandex Dictionary API"""
        try:
            # Очищаем слово
            clean_word = re.sub(r'[^a-zA-Z-]', '', word.strip().lower())
            if not clean_word or self._is_primitive_word(clean_word):
                return []

            # Параметры запроса
            params = {
                'key': self.dict_api_key,
                'lang': 'en-ru',
                'text': clean_word
            }

            response = requests.get(self.dict_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                translations = []

                # Извлекаем переводы из ответа
                for entry in data.get('def', [])[:3]:  # Первые 3 словарных статьи
                    for translation in entry.get('tr', [])[:3]:  # Первые 3 перевода
                        trans_text = translation.get('text', '')
                        if trans_text and trans_text not in translations:
                            translations.append(trans_text)

                return translations[:5]  # Максимум 5 уникальных переводов
            else:
                print(f"⚠️ Yandex Dict API error: {response.status_code}", flush=True)
                return []

        except Exception as e:
            print(f"⚠️ Dictionary API error: {e}", flush=True)
            return []

    def _get_dictionary_meanings(self, word: str) -> List[str]:
        """Получает русские переводы слова через Yandex Dictionary API

        Для фраз: разбивает на слова, фильтрует примитивные, возвращает переводы сложных слов
        Для одиночных слов: возвращает альтернативные переводы
        """
        try:
            # Проверяем наличие API ключа
            if not self.dict_api_key:
                print("⚠️ YANDEX_DICT_API_KEY не найден в .env", flush=True)
                return []

            # Очищаем от лишних символов
            clean_text = re.sub(r'[^a-zA-Z\s-]', '', word.strip().lower())
            if not clean_text:
                return []

            # Если фраза (несколько слов) - обрабатываем каждое слово
            if ' ' in clean_text:
                words = clean_text.split()
                all_translations = []

                for w in words:
                    # Пропускаем примитивные слова
                    if self._is_primitive_word(w):
                        continue

                    # Получаем переводы для сложного слова
                    translations = self._get_yandex_dict_translations(w)
                    if translations:
                        all_translations.extend(translations[:2])  # Максимум 2 перевода на слово

                return all_translations[:5]  # Всего максимум 5 переводов для фразы
            else:
                # Одиночное слово
                return self._get_yandex_dict_translations(clean_text)[:5]  # Максимум 5 переводов

        except Exception as e:
            print(f"⚠️ Ошибка получения переводов: {e}", flush=True)
            return []

    def get_dictionary_meanings(self, highlight_text: str) -> List[str]:
        """Публичный метод для получения словарных значений (для новой архитектуры)"""
        return self._get_dictionary_meanings(highlight_text)

    def _translate_definition_sync(self, definition: str) -> str:
        """Переводит английское определение на русский через Yandex Translate (синхронно)"""
        try:
            print(f"🔄 [TRANSLATE] Переводим: '{definition}'", flush=True)
            print(f"🔄 [TRANSLATE] IAM token: {self.iam_token[:20]}...", flush=True)
            print(f"🔄 [TRANSLATE] Folder ID: {self.folder_id}", flush=True)

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

            print(f"🔄 [TRANSLATE] Status: {response.status_code}", flush=True)

            if response.status_code == 200:
                result = response.json()
                print(f"🔄 [TRANSLATE] Response: {result}", flush=True)
                translation = result["translations"][0]["text"]
                print(f"✅ [TRANSLATE] Получен перевод: '{translation}'", flush=True)
                return translation
            else:
                print(f"❌ [TRANSLATE] Ошибка: {response.status_code} - {response.text}", flush=True)
                return definition  # Возвращаем оригинал если перевод не удался

        except Exception as e:
            print(f"❌ [TRANSLATE] Exception: {e}", flush=True)
            import traceback
            traceback.print_exc()
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
        try:
            # Используем синхронный метод в асинхронной обертке
            translation = self._translate_definition_sync(text)
            return translation
        except Exception as e:
            print(f"⚠️ Ошибка перевода текста: {e}", flush=True)
            return text  # Возвращаем оригинал при ошибке
    
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
                highlight_translation=f"Найдено в: ...{word}...",
                cefr_level="B2",
                importance_score=70,
                dictionary_meanings=[f"Значение слова {word}"],
                why_interesting=f"Длинное слово, потенциально интересное"
            )
            highlights.append(highlight)

        return highlights

    # Публичные методы для совместимости с новой архитектурой
    async def request_gpt(self, prompt: str) -> str:
        """Публичный метод для запроса к GPT (для новой архитектуры)"""
        result = await self._request_yandex_gpt(prompt)
        # Возвращаем текст ответа
        return result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")

    async def translate_text(self, text: str, target_lang: str = "ru") -> str:
        """Публичный метод для перевода (для новой архитектуры)"""
        return await self._translate_text(text)

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
            print(f"   🇷🇺 Перевод: {h.highlight_translation}")
            print(f"   💡 Почему интересен: {h.why_interesting}")
            print(f"   📊 Важность: {h.importance_score}/100")
        
        print("\n✅ Тест завершен!")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_yandex_ai_client()