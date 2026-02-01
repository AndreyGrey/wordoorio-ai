#!/usr/bin/env python3
"""
YouTubeService - сервис для извлечения транскриптов из YouTube видео
"""

import re
import logging
from typing import Optional, Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)

logger = logging.getLogger(__name__)


class YouTubeService:
    """Сервис для работы с YouTube транскриптами"""

    # Регулярные выражения для извлечения video_id
    URL_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Просто video_id
    ]

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Извлечь video_id из YouTube URL

        Поддерживаемые форматы:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - VIDEO_ID (просто ID)

        Args:
            url: YouTube URL или video_id

        Returns:
            video_id или None если не удалось извлечь
        """
        url = url.strip()

        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_transcript(self, video_id: str, languages: List[str] = None) -> Dict:
        """
        Получить транскрипт видео

        Args:
            video_id: ID видео
            languages: Список языков в порядке приоритета (по умолчанию ['en', 'ru'])

        Returns:
            {
                'success': True,
                'video_id': 'xxx',
                'text': 'полный текст транскрипта',
                'segments': [...],  # оригинальные сегменты с таймкодами
                'language': 'en'
            }
            или
            {
                'success': False,
                'error': 'описание ошибки'
            }
        """
        if languages is None:
            languages = ['en', 'ru']

        try:
            logger.info(f"[YouTubeService] Запрос транскрипта для video_id={video_id}, languages={languages}")

            # Простой подход: сразу запрашиваем транскрипт
            # Это работает лучше, чем list_transcripts на некоторых серверах
            try:
                segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                used_language = languages[0]  # Предполагаем первый язык

                # Объединяем в текст
                text = ' '.join(segment['text'] for segment in segments)

                logger.info(f"[YouTubeService] Получен транскрипт для {video_id}, длина: {len(text)}")

                return {
                    'success': True,
                    'video_id': video_id,
                    'text': text,
                    'segments': segments,
                    'language': used_language
                }

            except NoTranscriptFound:
                # Пробуем автоматические субтитры
                logger.info(f"[YouTubeService] Ручные субтитры не найдены, пробуем автоматические")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # Ищем любой доступный транскрипт
                for transcript in transcript_list:
                    logger.info(f"[YouTubeService] Найден транскрипт: {transcript.language_code}, auto={transcript.is_generated}")

                # Пробуем автоматически сгенерированные
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        segments = transcript.fetch()
                        text = ' '.join(segment['text'] for segment in segments)

                        logger.info(f"[YouTubeService] Получен auto-транскрипт для {video_id}, язык: {lang}")

                        return {
                            'success': True,
                            'video_id': video_id,
                            'text': text,
                            'segments': segments,
                            'language': lang
                        }
                    except NoTranscriptFound:
                        continue

                return {
                    'success': False,
                    'error': 'Субтитры не найдены для указанных языков'
                }

        except TranscriptsDisabled as e:
            logger.warning(f"[YouTubeService] TranscriptsDisabled для {video_id}: {e}")
            return {
                'success': False,
                'error': f'Субтитры отключены или недоступны. Возможно, YouTube блокирует запросы с сервера.'
            }

        except VideoUnavailable as e:
            logger.warning(f"[YouTubeService] VideoUnavailable для {video_id}: {e}")
            return {
                'success': False,
                'error': 'Видео недоступно (удалено или приватное)'
            }

        except Exception as e:
            import traceback
            error_type = type(e).__name__
            logger.error(f"[YouTubeService] {error_type} для {video_id}: {e}")
            logger.error(f"[YouTubeService] Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'{error_type}: {str(e)}'
            }

    def get_transcript_from_url(self, url: str, languages: List[str] = None) -> Dict:
        """
        Получить транскрипт по URL

        Args:
            url: YouTube URL
            languages: Список языков

        Returns:
            Результат get_transcript() или ошибка
        """
        video_id = self.extract_video_id(url)

        if not video_id:
            return {
                'success': False,
                'error': 'Неверный формат YouTube URL'
            }

        return self.get_transcript(video_id, languages)
