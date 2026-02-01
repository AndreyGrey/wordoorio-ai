#!/usr/bin/env python3
"""
YouTubeService - сервис для извлечения транскриптов из YouTube видео
Использует TranscriptAPI.com
"""

import re
import os
import logging
import aiohttp
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class YouTubeService:
    """Сервис для работы с YouTube транскриптами через TranscriptAPI"""

    BASE_URL = "https://transcriptapi.com/api/v2"

    URL_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]

    def __init__(self):
        self.api_key = os.getenv('TRANSCRIPT_API_KEY', '')
        if not self.api_key:
            logger.warning("[YouTubeService] TRANSCRIPT_API_KEY не установлен!")

    def extract_video_id(self, url: str) -> Optional[str]:
        """Извлечь video_id из YouTube URL"""
        url = url.strip()
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def get_transcript(self, video_id: str, language: str = 'en') -> Dict:
        """
        Получить транскрипт видео через TranscriptAPI

        Args:
            video_id: ID видео YouTube
            language: Предпочитаемый язык (en, ru, etc.)

        Returns:
            Dict с результатом: success, text, language, video_id или error
        """
        logger.info(f"[YouTubeService] Запрос транскрипта для video_id={video_id}")

        if not self.api_key:
            return {
                'success': False,
                'error': 'API ключ не настроен'
            }

        try:
            url = f"{self.BASE_URL}/youtube/transcript"
            params = {
                'video_url': video_id,
                'format': 'text',  # Получаем чистый текст
                'include_timestamp': 'false',
                'send_metadata': 'true'
            }
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Извлекаем текст транскрипта
                        transcript_text = data.get('transcript', '')

                        # Если transcript это список сегментов
                        if isinstance(transcript_text, list):
                            transcript_text = ' '.join(
                                seg.get('text', '') for seg in transcript_text
                            )

                        # Метаданные
                        metadata = data.get('metadata', {})
                        detected_lang = metadata.get('language', language)

                        logger.info(f"[YouTubeService] Получен транскрипт, длина={len(transcript_text)}")

                        return {
                            'success': True,
                            'video_id': video_id,
                            'text': transcript_text,
                            'language': detected_lang,
                            'title': metadata.get('title', ''),
                            'duration': metadata.get('duration', 0)
                        }

                    elif response.status == 401:
                        return {'success': False, 'error': 'Неверный API ключ'}

                    elif response.status == 402:
                        return {'success': False, 'error': 'Закончились кредиты API'}

                    elif response.status == 404:
                        return {'success': False, 'error': 'Видео не найдено или субтитры недоступны'}

                    elif response.status == 429:
                        return {'success': False, 'error': 'Превышен лимит запросов'}

                    else:
                        error_text = await response.text()
                        logger.error(f"[YouTubeService] Ошибка API: {response.status} - {error_text}")
                        return {'success': False, 'error': f'Ошибка API: {response.status}'}

        except aiohttp.ClientError as e:
            logger.error(f"[YouTubeService] Ошибка сети: {e}")
            return {'success': False, 'error': f'Ошибка сети: {str(e)}'}

        except Exception as e:
            logger.error(f"[YouTubeService] Неизвестная ошибка: {e}")
            return {'success': False, 'error': str(e)}

    async def get_transcript_from_url(self, url: str, language: str = 'en') -> Dict:
        """Получить транскрипт по URL"""
        video_id = self.extract_video_id(url)

        if not video_id:
            return {
                'success': False,
                'error': 'Неверный формат YouTube URL'
            }

        return await self.get_transcript(video_id, language)
