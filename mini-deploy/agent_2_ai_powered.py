#!/usr/bin/env python3
"""
🧠 Agent 2: AI-powered Vocabulary Intelligence Analyzer

Только Yandex GPT анализ, никаких примитивных алгоритмов.
"""

import re
import os
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from yandex_ai_client import LinguisticHighlight

class AIVocabularyAnalyzer:
    """AI-powered анализатор лексики - только через Yandex GPT"""
    
    def __init__(self):
        pass
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Анализ текста через Yandex GPT
        Никаких fallback алгоритмов - только AI или ошибка
        """
        print("🧠 AI-powered анализ через Yandex GPT...", flush=True)
        
        try:
            # Базовая статистика текста
            text_stats = self._calculate_text_stats(text)
            
            # AI хайлайты через Yandex GPT
            highlights = self._extract_ai_highlights(text)
            
            if not highlights:
                return {
                    'success': False,
                    'error': 'Yandex GPT недоступен или не настроен. Проверьте токены в .env файле.',
                    'highlights': [],
                    'stats': {
                        'total_words': text_stats.get('total_words', 0),
                        'total_highlights': 0
                    }
                }
            
            # Оценка сложности на основе AI хайлайтов
            difficulty_info = self._assess_difficulty(highlights, text_stats)
            
            return {
                'success': True,
                'highlights': [h.to_dict() for h in highlights],
                'stats': {
                    'total_words': text_stats.get('total_words', 0),
                    'total_highlights': len(highlights)
                }
            }
            
        except Exception as e:
            print(f"❌ Критическая ошибка AI анализа: {e}", flush=True)
            return {
                'success': False,
                'error': f'Ошибка AI анализа: {str(e)}',
                'highlights': [],
                'text_stats': {},
                'difficulty_info': {}
            }
    
    def _extract_ai_highlights(self, text: str) -> List[LinguisticHighlight]:
        """Использует только Yandex GPT для анализа"""
        try:
            from yandex_ai_client import YandexAIClient
            client = YandexAIClient()
            
            # Асинхронный вызов Yandex GPT
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            ai_highlights = loop.run_until_complete(client.analyze_linguistic_highlights(text))
            
            if ai_highlights:
                print(f"✅ Yandex GPT: найдено {len(ai_highlights)} AI хайлайтов", flush=True)
                return ai_highlights
            else:
                print("❌ Yandex GPT не вернул результатов", flush=True)
                return []
                
        except Exception as e:
            print(f"❌ Ошибка Yandex GPT: {e}", flush=True)
            return []
    
    def _calculate_text_stats(self, text: str) -> Dict[str, Any]:
        """Базовая статистика текста"""
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        unique_words = set(words)
        
        return {
            'total_words': len(words),
            'unique_words': len(unique_words),
            'sentences': len(sentences),
            'avg_words_per_sentence': len(words) / max(len(sentences), 1),
            'avg_word_length': sum(len(w) for w in words) / max(len(words), 1)
        }
    
    def _assess_difficulty(self, highlights: List[LinguisticHighlight], 
                          text_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка сложности на основе AI хайлайтов"""
        
        if not highlights:
            return {
                'overall_level': 'Unknown',
                'difficulty_score': 0,
                'recommendation': 'Невозможно определить без AI анализа'
            }
        
        # Анализируем уровни от Yandex GPT
        level_counts = {}
        total_score = 0
        
        for h in highlights:
            level = h.cefr_level
            level_counts[level] = level_counts.get(level, 0) + 1
            total_score += h.importance_score
        
        avg_score = total_score / len(highlights)
        
        # Определяем уровень на основе AI анализа
        if avg_score >= 80:
            overall_level = 'C1'
            recommendation = 'Продвинутый уровень - много специализированной лексики'
        elif avg_score >= 70:
            overall_level = 'B2'
            recommendation = 'Средне-продвинутый уровень - хороший для развития'
        elif avg_score >= 60:
            overall_level = 'B1'
            recommendation = 'Средний уровень - подходит для активного изучения'
        else:
            overall_level = 'A2'
            recommendation = 'Базовый уровень с элементами сложной лексики'
        
        return {
            'overall_level': overall_level,
            'difficulty_score': int(avg_score),
            'recommendation': recommendation,
            'level_breakdown': level_counts,
            'advanced_word_density': len(highlights) / max(text_stats.get('total_words', 1), 1) * 100
        }

if __name__ == "__main__":
    print("🧠 AI Agent 2 - только Yandex GPT анализ")
    print("Для работы нужны токены в .env файле:")
    print("YANDEX_IAM_TOKEN=...")
    print("YANDEX_FOLDER_ID=...")
    
    analyzer = AIVocabularyAnalyzer()
    test_text = "Machine learning algorithms revolutionize artificial intelligence."
    result = analyzer.analyze_text(test_text)
    
    if result['success']:
        print(f"✅ Найдено {len(result['highlights'])} хайлайтов")
    else:
        print(f"❌ {result['error']}")