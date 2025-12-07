"""
🎬 YOUTUBE TRANSCRIPT AGENT (Agent 1)

Извлечение транскриптов из YouTube видео для анализа английской лексики.

Стратегия:
1. Основной метод: youtube-transcript-api (быстро, ~2-3 сек)
2. Fallback: yt-dlp если субтитры недоступны
3. Валидация URL и извлечение video_id
4. Детальная обработка ошибок

@version 1.0.0
@author Wordoorio Team
"""

import re
import requests
import json
import subprocess
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    IpBlocked
)


class YouTubeTranscriptAgent:
    """
    Agent 1: Извлечение транскриптов YouTube видео

    Использует youtube-transcript-api для получения английских субтитров.
    Обрабатывает различные форматы YouTube URL.
    """

    def __init__(self, cookies=None):
        """
        Инициализация агента

        Args:
            cookies: Путь к файлу cookies для обхода блокировок YouTube (опционально)
        """
        self.ytt_api = YouTubeTranscriptApi()
        self.cookies = cookies

    def get_video_title(self, video_id: str) -> Optional[str]:
        """
        Получить название видео через YouTube oEmbed API

        Args:
            video_id: YouTube video ID

        Returns:
            Название видео или None если не удалось получить
        """
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('title')
        except Exception:
            pass
        return None

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Извлечь video_id из YouTube URL

        Поддерживаемые форматы:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - youtube.com/watch?v=VIDEO_ID&t=123

        Args:
            url: YouTube URL или video_id

        Returns:
            video_id или None если невалидный URL
        """
        # Если уже video_id (11 символов, только буквы/цифры/-/_)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url

        # Паттерны для различных форматов YouTube URL
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def extract_transcript(self, video_url: str) -> Dict:
        """
        Извлечь транскрипт с метаданными

        Args:
            video_url: YouTube URL или video_id

        Returns:
            {
                'success': bool,
                'video_id': str,
                'transcript': str,       # Полный текст
                'segments': list,         # С таймстампами [{start, text}]
                'word_count': int,        # Количество слов
                'duration': float,        # Длительность в секундах
                'method': str,            # 'youtube-transcript-api'
                'language': str,          # Код языка (en, en-US, etc)
                'error': str | None
            }
        """
        # Валидация и извлечение video_id
        video_id = self.extract_video_id(video_url)

        if not video_id:
            return {
                'success': False,
                'video_id': None,
                'transcript': None,
                'segments': None,
                'word_count': 0,
                'duration': 0,
                'method': None,
                'language': None,
                'error': 'Невалидный YouTube URL. Поддерживаемые форматы: youtube.com/watch?v=..., youtu.be/...'
            }

        # Попытка получить транскрипт через youtube-transcript-api
        try:
            # Запрос английских субтитров (с fallback на разные варианты)
            # Добавляем поддержку cookies для обхода блокировок
            kwargs = {'languages': ['en', 'en-US', 'en-GB']}
            if self.cookies:
                kwargs['cookies'] = self.cookies

            transcript_data = self.ytt_api.fetch(video_id, **kwargs)

            # Форматируем сегменты
            segments = []
            for entry in transcript_data:
                segments.append({
                    'start': entry.start,
                    'duration': entry.duration,
                    'text': entry.text
                })

            # Формируем полный текст
            full_text = " ".join([seg['text'] for seg in segments])

            # Подсчет слов
            word_count = len(full_text.split())

            # Длительность (последний сегмент start + duration)
            duration = segments[-1]['start'] + segments[-1]['duration'] if segments else 0

            # Получаем название видео
            video_title = self.get_video_title(video_id)

            return {
                'success': True,
                'video_id': video_id,
                'video_title': video_title,
                'transcript': full_text,
                'segments': segments,
                'word_count': word_count,
                'duration': duration,
                'method': 'youtube-transcript-api',
                'language': 'en',  # Всегда английский, так как запрашиваем en*
                'error': None
            }

        except TranscriptsDisabled:
            return {
                'success': False,
                'video_id': video_id,
                'transcript': None,
                'segments': None,
                'word_count': 0,
                'duration': 0,
                'method': 'youtube-transcript-api',
                'language': None,
                'error': 'Субтитры отключены для этого видео'
            }

        except VideoUnavailable:
            return {
                'success': False,
                'video_id': video_id,
                'transcript': None,
                'segments': None,
                'word_count': 0,
                'duration': 0,
                'method': 'youtube-transcript-api',
                'language': None,
                'error': 'Видео недоступно (приватное или удалено)'
            }

        except (RequestBlocked, IpBlocked):
            return {
                'success': False,
                'video_id': video_id,
                'transcript': None,
                'segments': None,
                'word_count': 0,
                'duration': 0,
                'method': 'youtube-transcript-api',
                'language': None,
                'error': 'Слишком много запросов. Попробуйте через несколько минут'
            }

        except Exception as e:
            # Общая ошибка
            return {
                'success': False,
                'video_id': video_id,
                'transcript': None,
                'segments': None,
                'word_count': 0,
                'duration': 0,
                'method': 'youtube-transcript-api',
                'language': None,
                'error': f'Ошибка получения транскрипта: {str(e)}'
            }

    def get_available_languages(self, video_url: str) -> Dict:
        """
        Получить список доступных языков субтитров

        Args:
            video_url: YouTube URL или video_id

        Returns:
            {
                'success': bool,
                'video_id': str,
                'languages': list,  # [{'code': 'en', 'name': 'English', 'auto': bool}]
                'error': str | None
            }
        """
        video_id = self.extract_video_id(video_url)

        if not video_id:
            return {
                'success': False,
                'video_id': None,
                'languages': [],
                'error': 'Невалидный YouTube URL'
            }

        try:
            # Получаем список доступных транскриптов
            transcript_list = self.ytt_api.list(video_id)

            languages = []
            for transcript in transcript_list:
                languages.append({
                    'code': transcript.language_code,
                    'name': transcript.language,
                    'auto': transcript.is_generated
                })

            return {
                'success': True,
                'video_id': video_id,
                'languages': languages,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'video_id': video_id,
                'languages': [],
                'error': str(e)
            }


# Для тестирования
if __name__ == '__main__':
    agent = YouTubeTranscriptAgent()

    # Тест 1: Популярное видео с субтитрами
    print("=== Test 1: Rick Astley - Never Gonna Give You Up ===")
    result = agent.extract_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print(f"Success: {result['success']}")
    print(f"Video ID: {result['video_id']}")
    print(f"Word count: {result['word_count']}")
    print(f"Duration: {result['duration']:.1f}s")
    print(f"Language: {result['language']}")
    if result['success']:
        print(f"First 200 chars: {result['transcript'][:200]}...")
    else:
        print(f"Error: {result['error']}")

    print("\n=== Test 2: Check available languages ===")
    langs = agent.get_available_languages("dQw4w9WgXcQ")
    print(f"Available languages: {langs['languages']}")
