#!/usr/bin/env python3
"""
Клиент для Yandex AI Studio API
Поддержка Yandex GPT и Yandex Translate
"""

import os
import re
import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Импортируем контракты
from contracts.analysis_contracts import AgentResponse

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
        self.agent_atelier_url = "https://agent-atelier.api.cloud.yandex.net/agent-atelier/v1"
        self.translate_url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        self.dict_url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"

    def _get_iam_token(self) -> str:
        """Получает IAM токен для Yandex Cloud

        Приоритет (ИНВЕРТИРОВАН для надежности):
        1. Metadata Service (для продакшн/Serverless Container) - ВСЕГДА свежий токен
        2. Environment variable (fallback для локальной разработки)
        """
        # СНАЧАЛА пытаемся получить токен через Metadata Service (продакшн)
        try:
            metadata_url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
            headers = {'Metadata-Flavor': 'Google'}  # Yandex Cloud использует совместимый с GCP формат

            response = requests.get(metadata_url, headers=headers, timeout=2)

            if response.status_code == 200:
                token_data = response.json()
                iam_token = token_data.get('access_token', '')
                print(f"✅ IAM токен получен через Metadata Service (авто-обновление)", flush=True)
                return iam_token

        except Exception as e:
            # Это нормально для локальной разработки - Metadata Service недоступен
            pass

        # FALLBACK: проверяем переменную окружения (только для локальной разработки)
        env_token = os.getenv('YANDEX_IAM_TOKEN', '')
        if env_token:
            print(f"⚠️ Используется IAM токен из .env (локальная разработка). Токены истекают через 12 часов!", flush=True)
            return env_token

        print(f"❌ IAM токен не найден ни в Metadata Service, ни в environment variables", flush=True)
        return ''

    async def translate_text(self, text: str, target_lang: str = "ru") -> str:
        """Публичный метод для перевода (для новой архитектуры)"""
        return await self._translate_text(text)

    async def call_agent(self, agent_id: str, user_input: str) -> AgentResponse:
        """
        Вызов агента через Yandex AI Studio Assistant API

        Использует официальный SDK yandex-cloud-ml-sdk, т.к. стандартная
        библиотека openai не поддерживает Yandex AI Studio Assistants.

        Args:
            agent_id: ID ассистента/агента в AI Studio (например, "fvt3bjtu1ehmg0v8tss3")
            user_input: Входные данные для агента (обычно JSON строка)

        Returns:
            AgentResponse: Распарсенный ответ от агента

        Raises:
            Exception: При ошибках сети или парсинга
        """
        from yandex_cloud_ml_sdk import YCloudML
        from yandex_cloud_ml_sdk.auth import APIKeyAuth

        print(f"🤖 Вызов агента {agent_id[:10]}...", flush=True)

        # Получаем API ключ (приоритет: YANDEX_CLOUD_API_KEY > IAM токен)
        api_key = os.getenv('YANDEX_CLOUD_API_KEY', self.iam_token)

        if not api_key:
            raise Exception("Для AI анализа нужны токены Yandex GPT")

        # Диагностика
        print(f"DEBUG: api_key starts with: {api_key[:10] if api_key else 'None'}...", flush=True)
        print(f"DEBUG: folder_id: {self.folder_id}", flush=True)

        try:
            # Инициализируем SDK с API ключом
            sdk = YCloudML(
                folder_id=self.folder_id,
                auth=APIKeyAuth(api_key)
            )

            # Получаем ассистента
            assistant = await sdk.assistants.get(agent_id)

            # Вызываем агента с входными данными
            result = await assistant.run(user_input)

            # Получаем текст ответа
            response_text = result.text if hasattr(result, 'text') else str(result)

            if not response_text:
                raise Exception("Пустой ответ от агента")

            print(f"✅ Агент ответил: {len(response_text)} символов", flush=True)

            # Парсим JSON ответ агента в AgentResponse
            try:
                agent_data = json.loads(response_text)
                return AgentResponse.from_dict(agent_data)
            except json.JSONDecodeError as e:
                raise Exception(f"Не удалось распарсить JSON от агента: {e}. Ответ: {response_text[:200]}")

        except Exception as e:
            print(f"❌ ERROR in call_agent: {type(e).__name__}: {str(e)}", flush=True)
            import traceback
            print(f"Traceback: {traceback.format_exc()}", flush=True)
            raise Exception(f"Ошибка вызова агента: {str(e)}")

    async def get_dictionary_meanings(self, word: str) -> List[str]:
        """
        Получить словарные значения слова из Yandex Dictionary API (async)

        Args:
            word: Слово для поиска

        Returns:
            List[str]: Список переводов/значений
        """
        try:
            return await self._get_dictionary_meanings(word)
        except Exception as e:
            print(f"⚠️ Ошибка получения переводов: {e}", flush=True)
            return []

    async def _get_dictionary_meanings(self, word: str) -> List[str]:
        """Получить значения из Yandex Dictionary для слова или фразы (async)"""

        # Для составных фраз разбиваем на слова
        words = word.strip().split()

        if len(words) > 1:
            # Для фраз запрашиваем параллельно значения для каждого сложного слова
            complex_words = [w for w in words if not self._is_primitive_word(w)]

            if not complex_words:
                return []

            # Параллельные запросы
            tasks = [self._get_yandex_dict_translations(w) for w in complex_words]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Собираем результаты
            all_meanings = []
            for result in results:
                if not isinstance(result, Exception):
                    all_meanings.extend(result)

            # Уникальные значения
            return list(dict.fromkeys(all_meanings))[:5]
        else:
            # Для одного слова
            if self._is_primitive_word(word.lower()):
                return []

            return await self._get_yandex_dict_translations(word)

    async def _get_yandex_dict_translations(self, word: str) -> List[str]:
        """Запрос к Yandex Dictionary API (async)"""

        if not self.dict_api_key:
            return []

        params = {
            'key': self.dict_api_key,
            'lang': 'en-ru',
            'text': word.lower()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.dict_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()

                    # Парсим ответ Yandex Dictionary
                    translations = []
                    if 'def' in data and data['def']:
                        for definition in data['def']:
                            if 'tr' in definition:
                                for translation in definition['tr'][:3]:  # Первые 3 перевода
                                    translations.append(translation.get('text', ''))

                    return translations[:5]
        except Exception as e:
            return []

    async def _translate_text(self, text: str) -> str:
        """Перевод текста через Yandex Translate API (async)"""

        if not self.iam_token:
            return text

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }

        data = {
            "folderId": self.folder_id,
            "texts": [text],
            "targetLanguageCode": "ru"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.translate_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return text

                    result = await response.json()

                    if 'translations' in result and result['translations']:
                        return result['translations'][0].get('text', text)

                    return text
        except Exception as e:
            return text

    def _is_primitive_word(self, word: str) -> bool:
        """Проверка, является ли слово примитивным/базовым"""
        return word.lower() in self.PRIMITIVE_WORDS
