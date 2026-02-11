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
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Импортируем контракты
from contracts.analysis_contracts import AgentResponse

# Настройка логирования
logger = logging.getLogger(__name__)

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
                logger.info("IAM токен получен через Metadata Service (авто-обновление)")
                return iam_token

        except Exception as e:
            # Это нормально для локальной разработки - Metadata Service недоступен
            pass

        # FALLBACK: проверяем переменную окружения (только для локальной разработки)
        env_token = os.getenv('YANDEX_IAM_TOKEN', '')
        if env_token:
            logger.warning("Используется IAM токен из .env (локальная разработка). Токены истекают через 12 часов!")
            return env_token

        logger.error("IAM токен не найден ни в Metadata Service, ни в environment variables")
        return ''

    async def translate_text(self, text: str, target_lang: str = "ru") -> str:
        """Публичный метод для перевода (для новой архитектуры)"""
        return await self._translate_text(text)

    async def call_agent(self, agent_id: str, user_input: str) -> AgentResponse:
        """
        Вызов агента через Yandex AI Studio Assistant API (прямой REST API)

        Использует прямой REST API вызов через aiohttp, без SDK.
        Это избегает конфликтов зависимостей с другими пакетами.

        Args:
            agent_id: ID ассистента/агента в AI Studio (например, "fvt3bjtu1ehmg0v8tss3")
            user_input: Входные данные для агента (обычно JSON строка)

        Returns:
            AgentResponse: Распарсенный ответ от агента

        Raises:
            Exception: При ошибках сети или парсинга
        """
        logger.info(f"Вызов агента {agent_id[:10]}...")

        # Получаем API ключ (приоритет: YANDEX_CLOUD_API_KEY > IAM токен)
        api_key = os.getenv('YANDEX_CLOUD_API_KEY', self.iam_token)

        if not api_key:
            raise Exception("Для AI анализа нужны токены Yandex GPT")

        # Диагностика
        logger.debug(f"api_key starts with: {api_key[:10] if api_key else 'None'}...")
        logger.debug(f"folder_id: {self.folder_id}")

        # API endpoint для Yandex AI Studio Assistants
        url = "https://rest-assistant.api.cloud.yandex.net/v1/responses"

        # Подготовка headers
        headers = {
            "Authorization": f"Api-Key {api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        # Тело запроса согласно документации Yandex AI Studio
        payload = {
            "prompt": {
                "id": agent_id
            },
            "input": user_input
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Yandex API returned {response.status}: {error_text}")

                    result = await response.json()

                    # Извлекаем текст ответа из структуры
                    # Формат: result.output[0].content[0].text
                    response_text = None
                    if 'output' in result and result['output']:
                        if isinstance(result['output'], list) and len(result['output']) > 0:
                            content = result['output'][0].get('content', [])
                            if isinstance(content, list) and len(content) > 0:
                                response_text = content[0].get('text', '')

                    if not response_text:
                        raise Exception(f"Пустой ответ от агента. Структура: {json.dumps(result)[:200]}")

                    logger.info(f"Агент ответил: {len(response_text)} символов")

                    # Парсим JSON ответ агента в AgentResponse
                    try:
                        agent_data = json.loads(response_text)
                        return AgentResponse.from_dict(agent_data)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Не удалось распарсить JSON от агента: {e}. Ответ: {response_text[:200]}")

        except Exception as e:
            logger.error(f"ERROR in call_agent: {type(e).__name__}: {str(e)}", exc_info=True)
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
            logger.warning(f"Ошибка получения переводов: {e}")
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

                    # Парсим ответ Yandex Dictionary — все переводы
                    translations = []
                    if 'def' in data and data['def']:
                        for definition in data['def']:
                            if 'tr' in definition:
                                for translation in definition['tr']:
                                    translations.append(translation.get('text', ''))

                    return translations
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

    async def generate_test_options(self, words_with_translations: List[Dict[str, str]]) -> Dict:
        """
        Генерация неправильных вариантов ответов для тестов через Агент #3

        Args:
            words_with_translations: Список словарей с полями:
                - word: английское слово
                - correct_translation: правильный перевод

        Returns:
            {
                "tests": [
                    {
                        "word": "sophisticated",
                        "correct_translation": "утончённый",
                        "wrong_options": ["сложный", "изощренный", "продвинутый"]
                    },
                    ...
                ]
            }

        Raises:
            Exception: если запрос не удался
        """
        # ID Агента #3 для генерации тестов (создан в Yandex AI Studio)
        agent_id = "fvtludf1115lb39bei78"

        # Подготавливаем входные данные (СТРОКА JSON, как в call_agent!)
        input_data = json.dumps({"words": words_with_translations}, ensure_ascii=False)

        logger.info(f"[generate_test_options] Вызываем агент {agent_id} с {len(words_with_translations)} словами")
        logger.info(f"[generate_test_options] input_data: {input_data[:200]}...")

        try:
            # Используем общий метод call_agent (как Agent #1 и #2)
            # НО: call_agent парсит ответ в AgentResponse, а нам нужен сырой dict
            # Поэтому извлекаем JSON из response_text напрямую

            # Получаем API ключ (точно так же как в call_agent)
            api_key = os.getenv('YANDEX_CLOUD_API_KEY', self.iam_token)
            if not api_key:
                raise Exception("Для генерации тестов нужен API ключ Yandex AI")

            url = "https://rest-assistant.api.cloud.yandex.net/v1/responses"
            headers = {
                "Authorization": f"Api-Key {api_key}",
                "x-folder-id": self.folder_id,
                "Content-Type": "application/json"
            }

            payload = {
                "prompt": {"id": agent_id},
                "input": input_data  # Передаем СТРОКУ JSON, как в call_agent!
            }

            logger.info(f"[generate_test_options] FULL payload: {json.dumps(payload, ensure_ascii=False)[:1000]}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    logger.info(f"[generate_test_options] HTTP status: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[generate_test_options] API error {response.status}: {error_text}")
                        raise Exception(f"Agent API error {response.status}: {error_text}")

                    result = await response.json()
                    logger.info(f"[generate_test_options] RAW response: {json.dumps(result, ensure_ascii=False)[:2000]}")

                    # Извлекаем текст ответа (точно так же как в call_agent)
                    response_text = None

                    # DEBUG: пошаговая проверка структуры
                    logger.info(f"[generate_test_options] Проверка структуры: 'output' in result = {'output' in result}")

                    if 'output' in result and result['output']:
                        logger.info(f"[generate_test_options] result['output'] type: {type(result['output'])}, len: {len(result['output']) if isinstance(result['output'], list) else 'N/A'}")

                        if isinstance(result['output'], list) and len(result['output']) > 0:
                            # output[0] - это reasoning/summary, output[1] - это message с content
                            # Ищем элемент с type='message' и полем content
                            for output_item in result['output']:
                                if isinstance(output_item, dict):
                                    logger.info(f"[generate_test_options] output_item keys: {output_item.keys()}, type: {output_item.get('type')}")

                                    if output_item.get('type') == 'message' and 'content' in output_item:
                                        content = output_item.get('content', [])
                                        logger.info(f"[generate_test_options] Found message! content type: {type(content)}, len: {len(content) if isinstance(content, list) else 'N/A'}")

                                        if isinstance(content, list) and len(content) > 0:
                                            first_content = content[0]
                                            logger.info(f"[generate_test_options] first_content keys: {first_content.keys() if isinstance(first_content, dict) else 'NOT_DICT'}")
                                            logger.info(f"[generate_test_options] first_content RAW: {json.dumps(first_content, ensure_ascii=False)[:500]}")
                                            response_text = first_content.get('text', '')
                                            logger.info(f"[generate_test_options] Extracted text length: {len(response_text) if response_text else 0}")
                                            logger.info(f"[generate_test_options] Extracted text preview: {response_text[:500]}")
                                            break

                    if not response_text:
                        logger.error(f"[generate_test_options] Пустой response_text. Полная структура: {json.dumps(result, ensure_ascii=False)[:3000]}")
                        raise Exception(f"Пустой ответ от агента")

                    logger.info(f"[generate_test_options] response_text длина: {len(response_text)} символов")

                    # Парсим JSON из ответа
                    return json.loads(response_text)

        except asyncio.TimeoutError:
            raise Exception("Timeout при генерации тестов (120s)")
        except json.JSONDecodeError as e:
            logger.error(f"[generate_test_options] JSONDecodeError: {e}, response_text: {response_text[:200] if response_text else 'None'}")
            raise Exception(f"Не удалось распарсить ответ агента: {e}")
        except Exception as e:
            logger.error(f"[generate_test_options] Exception: {type(e).__name__}: {str(e)}")
            raise Exception(f"Ошибка при генерации тестов: {e}")

    async def generate_reverse_test_options(self, words_with_translations: List[Dict[str, str]]) -> Dict:
        """
        Генерация неправильных английских вариантов для обратных тестов через Агент #4

        Обратный режим: показываем русское слово, выбираем английское

        Args:
            words_with_translations: Список словарей с полями:
                - word: английское слово (правильный ответ)
                - correct_translation: русский перевод (показываем пользователю)

        Returns:
            {
                "tests": [
                    {
                        "word": "threshold",
                        "correct_translation": "порог",
                        "wrong_options": ["doorframe", "hinges", "latch"]
                    },
                    ...
                ]
            }

        Raises:
            Exception: если запрос не удался
        """
        # ID Агента #4 для обратных тестов (создан в Yandex AI Studio)
        agent_id = "fvtknc1676vb5ru06i1b"

        # Подготавливаем входные данные
        input_data = json.dumps({"words": words_with_translations}, ensure_ascii=False)

        logger.info(f"[generate_reverse_test_options] Вызываем агент {agent_id} с {len(words_with_translations)} словами")

        try:
            api_key = os.getenv('YANDEX_CLOUD_API_KEY', self.iam_token)
            if not api_key:
                raise Exception("Для генерации тестов нужен API ключ Yandex AI")

            url = "https://rest-assistant.api.cloud.yandex.net/v1/responses"
            headers = {
                "Authorization": f"Api-Key {api_key}",
                "x-folder-id": self.folder_id,
                "Content-Type": "application/json"
            }

            payload = {
                "prompt": {"id": agent_id},
                "input": input_data
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    logger.info(f"[generate_reverse_test_options] HTTP status: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[generate_reverse_test_options] API error {response.status}: {error_text}")
                        raise Exception(f"Agent API error {response.status}: {error_text}")

                    result = await response.json()
                    response_text = None

                    if 'output' in result and result['output']:
                        if isinstance(result['output'], list) and len(result['output']) > 0:
                            for output_item in result['output']:
                                if isinstance(output_item, dict):
                                    if output_item.get('type') == 'message' and 'content' in output_item:
                                        content = output_item.get('content', [])
                                        if isinstance(content, list) and len(content) > 0:
                                            response_text = content[0].get('text', '')
                                            break

                    if not response_text:
                        logger.error(f"[generate_reverse_test_options] Пустой response_text")
                        raise Exception(f"Пустой ответ от агента")

                    logger.info(f"[generate_reverse_test_options] response_text длина: {len(response_text)} символов")
                    return json.loads(response_text)

        except asyncio.TimeoutError:
            raise Exception("Timeout при генерации обратных тестов (120s)")
        except json.JSONDecodeError as e:
            logger.error(f"[generate_reverse_test_options] JSONDecodeError: {e}")
            raise Exception(f"Не удалось распарсить ответ агента: {e}")
        except Exception as e:
            logger.error(f"[generate_reverse_test_options] Exception: {type(e).__name__}: {str(e)}")
            raise Exception(f"Ошибка при генерации обратных тестов: {e}")

    def _is_primitive_word(self, word: str) -> bool:
        """Проверка, является ли слово примитивным/базовым"""
        return word.lower() in self.PRIMITIVE_WORDS
