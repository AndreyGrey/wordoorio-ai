#!/usr/bin/env python3
"""
YouTubeService - сервис для извлечения транскриптов из YouTube видео
Использует yt-dlp как основной метод, youtube-transcript-api как fallback
"""

import re
import os
import json
import tempfile
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class YouTubeService:
    """Сервис для работы с YouTube транскриптами"""

    # Регулярные выражения для извлечения video_id
    URL_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Просто video_id
    ]

    def extract_video_id(self, url: str) -> Optional[str]:
        """Извлечь video_id из YouTube URL"""
        url = url.strip()

        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_transcript(self, video_id: str, languages: List[str] = None) -> Dict:
        """
        Получить транскрипт видео

        Стратегия:
        1. Пробуем yt-dlp (более устойчив к блокировкам)
        2. Если не сработало — пробуем youtube-transcript-api
        """
        if languages is None:
            languages = ['en', 'ru']

        logger.info(f"[YouTubeService] Запрос транскрипта для video_id={video_id}")

        # Метод 1: yt-dlp
        result = self._get_transcript_ytdlp(video_id, languages)
        if result['success']:
            return result

        logger.info(f"[YouTubeService] yt-dlp не сработал, пробуем youtube-transcript-api")

        # Метод 2: youtube-transcript-api (fallback)
        result = self._get_transcript_api(video_id, languages)
        return result

    def _get_transcript_ytdlp(self, video_id: str, languages: List[str]) -> Dict:
        """Получить транскрипт через yt-dlp"""
        try:
            import yt_dlp

            url = f"https://www.youtube.com/watch?v={video_id}"

            # Создаем временную директорию для субтитров
            with tempfile.TemporaryDirectory() as tmpdir:
                subtitle_file = os.path.join(tmpdir, 'subs')

                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': languages,
                    'subtitlesformat': 'json3',
                    'outtmpl': subtitle_file,
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                # Ищем файл субтитров
                for lang in languages:
                    # yt-dlp создает файлы вида: subs.en.json3
                    possible_files = [
                        os.path.join(tmpdir, f'subs.{lang}.json3'),
                        os.path.join(tmpdir, f'{video_id}.{lang}.json3'),
                    ]

                    for sub_file in possible_files:
                        if os.path.exists(sub_file):
                            text = self._parse_json3_subtitles(sub_file)
                            if text:
                                logger.info(f"[YouTubeService] yt-dlp: получен транскрипт, язык={lang}, длина={len(text)}")
                                return {
                                    'success': True,
                                    'video_id': video_id,
                                    'text': text,
                                    'segments': [],
                                    'language': lang,
                                    'method': 'yt-dlp'
                                }

                # Проверяем все файлы в директории
                files = os.listdir(tmpdir)
                logger.info(f"[YouTubeService] yt-dlp: файлы в tmpdir: {files}")

                for f in files:
                    if f.endswith('.json3'):
                        filepath = os.path.join(tmpdir, f)
                        text = self._parse_json3_subtitles(filepath)
                        if text:
                            # Извлекаем язык из имени файла
                            lang = f.split('.')[-2] if '.' in f else 'unknown'
                            logger.info(f"[YouTubeService] yt-dlp: найден файл {f}, длина={len(text)}")
                            return {
                                'success': True,
                                'video_id': video_id,
                                'text': text,
                                'segments': [],
                                'language': lang,
                                'method': 'yt-dlp'
                            }

                return {
                    'success': False,
                    'error': 'yt-dlp: субтитры не найдены'
                }

        except Exception as e:
            import traceback
            logger.warning(f"[YouTubeService] yt-dlp ошибка: {e}")
            logger.debug(traceback.format_exc())
            return {
                'success': False,
                'error': f'yt-dlp: {str(e)}'
            }

    def _parse_json3_subtitles(self, filepath: str) -> Optional[str]:
        """Парсинг JSON3 формата субтитров"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON3 формат: {"events": [{"segs": [{"utf8": "text"}]}]}
            texts = []
            for event in data.get('events', []):
                for seg in event.get('segs', []):
                    text = seg.get('utf8', '').strip()
                    if text and text != '\n':
                        texts.append(text)

            return ' '.join(texts) if texts else None

        except Exception as e:
            logger.warning(f"[YouTubeService] Ошибка парсинга JSON3: {e}")
            return None

    def _get_transcript_api(self, video_id: str, languages: List[str]) -> Dict:
        """Получить транскрипт через youtube-transcript-api"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled,
                NoTranscriptFound,
                VideoUnavailable
            )

            try:
                segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                text = ' '.join(segment['text'] for segment in segments)

                logger.info(f"[YouTubeService] API: получен транскрипт, длина={len(text)}")

                return {
                    'success': True,
                    'video_id': video_id,
                    'text': text,
                    'segments': segments,
                    'language': languages[0],
                    'method': 'youtube-transcript-api'
                }

            except NoTranscriptFound:
                return {
                    'success': False,
                    'error': 'Субтитры не найдены для указанных языков'
                }

            except TranscriptsDisabled:
                return {
                    'success': False,
                    'error': 'Субтитры отключены или YouTube блокирует запросы'
                }

            except VideoUnavailable:
                return {
                    'success': False,
                    'error': 'Видео недоступно'
                }

        except Exception as e:
            import traceback
            logger.error(f"[YouTubeService] API ошибка: {e}")
            logger.debug(traceback.format_exc())
            return {
                'success': False,
                'error': f'API: {str(e)}'
            }

    def get_transcript_from_url(self, url: str, languages: List[str] = None) -> Dict:
        """Получить транскрипт по URL"""
        video_id = self.extract_video_id(url)

        if not video_id:
            return {
                'success': False,
                'error': 'Неверный формат YouTube URL'
            }

        return self.get_transcript(video_id, languages)
