#!/usr/bin/env python3
"""
YouTubeService - сервис для извлечения транскриптов из YouTube видео
Использует yt-dlp
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

    URL_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
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
        """Получить транскрипт видео через yt-dlp"""
        if languages is None:
            languages = ['en', 'ru']

        logger.info(f"[YouTubeService] Запрос транскрипта для video_id={video_id}")

        try:
            import yt_dlp

            url = f"https://www.youtube.com/watch?v={video_id}"

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
                    ydl.extract_info(url, download=True)

                # Ищем файл субтитров
                for lang in languages:
                    possible_files = [
                        os.path.join(tmpdir, f'subs.{lang}.json3'),
                        os.path.join(tmpdir, f'{video_id}.{lang}.json3'),
                    ]

                    for sub_file in possible_files:
                        if os.path.exists(sub_file):
                            text = self._parse_json3_subtitles(sub_file)
                            if text:
                                logger.info(f"[YouTubeService] Получен транскрипт, язык={lang}, длина={len(text)}")
                                return {
                                    'success': True,
                                    'video_id': video_id,
                                    'text': text,
                                    'segments': [],
                                    'language': lang
                                }

                # Проверяем все файлы в директории
                files = os.listdir(tmpdir)
                logger.info(f"[YouTubeService] Файлы в tmpdir: {files}")

                for f in files:
                    if f.endswith('.json3'):
                        filepath = os.path.join(tmpdir, f)
                        text = self._parse_json3_subtitles(filepath)
                        if text:
                            lang = f.split('.')[-2] if '.' in f else 'unknown'
                            logger.info(f"[YouTubeService] Найден файл {f}, длина={len(text)}")
                            return {
                                'success': True,
                                'video_id': video_id,
                                'text': text,
                                'segments': [],
                                'language': lang
                            }

                return {
                    'success': False,
                    'error': 'Субтитры не найдены'
                }

        except Exception as e:
            import traceback
            logger.error(f"[YouTubeService] Ошибка: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_json3_subtitles(self, filepath: str) -> Optional[str]:
        """Парсинг JSON3 формата субтитров"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            texts = []
            for event in data.get('events', []):
                for seg in event.get('segs', []):
                    text = seg.get('utf8', '').strip()
                    if text and text != '\n':
                        texts.append(text)

            return ' '.join(texts) if texts else None

        except Exception as e:
            logger.warning(f"[YouTubeService] Ошибка парсинга: {e}")
            return None

    def get_transcript_from_url(self, url: str, languages: List[str] = None) -> Dict:
        """Получить транскрипт по URL"""
        video_id = self.extract_video_id(url)

        if not video_id:
            return {
                'success': False,
                'error': 'Неверный формат YouTube URL'
            }

        return self.get_transcript(video_id, languages)
