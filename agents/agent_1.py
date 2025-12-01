#!/usr/bin/env python3
"""
🎬 Agent 1: YouTube Content Processor

Извлекает субтитры и текстовый контент из YouTube видео
для последующего анализа лексики через Agent 2.

СТАТУС: FUTURE FEATURE - не используется в текущей версии
"""

import re
import os
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs


class YouTubeProcessor:
    """Процессор YouTube контента для извлечения текста"""
    
    def __init__(self):
        """Инициализация с API ключом из переменных окружения"""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.api_base_url = "https://www.googleapis.com/youtube/v3"
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Извлекает video ID из YouTube URL"""
        try:
            # Различные форматы YouTube URLs
            patterns = [
                r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]+)',
                r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]+)',
                r'(?:youtu\.be\/)([a-zA-Z0-9_-]+)',
                r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Если URL уже является video_id
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
                
            return None
            
        except Exception as e:
            print(f"❌ Ошибка извлечения video ID: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Получает метаданные видео через YouTube API"""
        try:
            if not self.youtube_api_key:
                return {"error": "YouTube API key не найден в .env"}
            
            url = f"{self.api_base_url}/videos"
            params = {
                "part": "snippet,contentDetails,statistics",
                "id": video_id,
                "key": self.youtube_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('items'):
                    item = data['items'][0]
                    snippet = item.get('snippet', {})
                    
                    return {
                        "title": snippet.get('title', 'Неизвестное видео'),
                        "description": snippet.get('description', ''),
                        "channel": snippet.get('channelTitle', 'Неизвестный канал'),
                        "duration": item.get('contentDetails', {}).get('duration', ''),
                        "view_count": item.get('statistics', {}).get('viewCount', 0),
                        "language": snippet.get('defaultLanguage', 'en')
                    }
                else:
                    return {"error": "Видео не найдено"}
            else:
                return {"error": f"YouTube API ошибка: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Ошибка получения метаданных: {e}")
            return {"error": str(e)}
    
    def extract_subtitles(self, video_id: str) -> Dict[str, Any]:
        """Извлекает субтитры из YouTube видео"""
        try:
            # Импортируем youtube-transcript-api только при необходимости
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Пытаемся получить английские субтитры
            languages = ['en', 'en-US', 'en-GB']
            
            for lang in languages:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    
                    # Объединяем текст субтитров
                    full_text = ' '.join([item['text'] for item in transcript])
                    
                    # Очищаем текст от лишних символов
                    clean_text = re.sub(r'\[.*?\]', '', full_text)  # Убираем [Music], [Applause]
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Нормализуем пробелы
                    
                    return {
                        "success": True,
                        "text": clean_text,
                        "language": lang,
                        "word_count": len(clean_text.split()),
                        "duration_seconds": transcript[-1]['start'] + transcript[-1]['duration'] if transcript else 0
                    }
                    
                except Exception as lang_error:
                    continue
            
            return {
                "success": False,
                "error": "Субтитры на английском языке недоступны",
                "text": ""
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "youtube-transcript-api не установлен",
                "text": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка извлечения субтитров: {str(e)}",
                "text": ""
            }
    
    def process_youtube_content(self, url: str) -> Dict[str, Any]:
        """
        Главный метод обработки YouTube контента
        Возвращает текст для анализа Agent 2
        """
        print(f"🎬 Обработка YouTube: {url}")
        
        # Извлекаем video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            return {
                "success": False,
                "error": "Невалидный YouTube URL",
                "text": ""
            }
        
        # Получаем метаданные
        metadata = self.get_video_metadata(video_id)
        if "error" in metadata:
            print(f"⚠️ Не удалось получить метаданные: {metadata['error']}")
        
        # Извлекаем субтитры
        subtitles_result = self.extract_subtitles(video_id)
        
        if subtitles_result["success"]:
            # Объединяем заголовок и текст субтитров для анализа
            title = metadata.get("title", "") if "error" not in metadata else ""
            description = metadata.get("description", "")[:500]  # Первые 500 символов описания
            
            combined_text = f"{title}. {description}. {subtitles_result['text']}"
            
            return {
                "success": True,
                "text": combined_text.strip(),
                "metadata": metadata if "error" not in metadata else {},
                "source": "youtube",
                "video_id": video_id,
                "url": url,
                "word_count": len(combined_text.split()),
                "subtitle_info": {
                    "language": subtitles_result.get("language", "en"),
                    "duration": subtitles_result.get("duration_seconds", 0)
                }
            }
        else:
            return {
                "success": False,
                "error": subtitles_result["error"],
                "text": ""
            }


if __name__ == "__main__":
    print("🎬 YouTube Agent 1 - Тестирование")
    
    processor = YouTubeProcessor()
    
    # Тест с примером URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = processor.process_youtube_content(test_url)
    
    if result["success"]:
        print(f"✅ Обработано: {result['word_count']} слов")
        print(f"📄 Текст: {result['text'][:200]}...")
    else:
        print(f"❌ Ошибка: {result['error']}")