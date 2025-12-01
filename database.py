"""
Модуль для работы с базой данных Wordoorio
Сохраняет историю анализов текстов и результатов
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class WordoorioDatabase:
    def __init__(self, db_path: str = "wordoorio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица для сохранения анализов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_highlights INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    session_id TEXT,
                    ip_address TEXT
                )
            """)
            
            # Таблица для сохранения найденных хайлайтов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS highlights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    highlight_word TEXT NOT NULL,
                    context TEXT NOT NULL,
                    context_translation TEXT NOT NULL,
                    dictionary_meanings TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
            """)
            
            # Индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analyses(analysis_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_highlight_word ON highlights(highlight_word)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_id ON highlights(analysis_id)")
            
            conn.commit()
    
    def save_analysis(self, 
                     original_text: str, 
                     highlights: List[Dict], 
                     stats: Dict,
                     session_id: str = None,
                     ip_address: str = None) -> int:
        """
        Сохранение результата анализа в базу данных
        
        Args:
            original_text: Исходный текст для анализа
            highlights: Список найденных хайлайтов
            stats: Статистика анализа (total_highlights, total_words)
            session_id: ID сессии пользователя
            ip_address: IP адрес пользователя
            
        Returns:
            ID созданного анализа
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Сохраняем основную запись анализа
            # Убираем переносы строк для компактного отображения
            cleaned_text = original_text.replace('\n', ' ').replace('\r', ' ')
            # Убираем множественные пробелы
            cleaned_text = ' '.join(cleaned_text.split())
            
            cursor.execute("""
                INSERT INTO analyses 
                (original_text, total_highlights, total_words, session_id, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cleaned_text,
                stats.get('total_highlights', 0),
                stats.get('total_words', 0),
                session_id,
                ip_address
            ))
            
            analysis_id = cursor.lastrowid
            
            # Сохраняем каждый хайлайт
            for highlight in highlights:
                cursor.execute("""
                    INSERT INTO highlights 
                    (analysis_id, highlight_word, context, context_translation, dictionary_meanings)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    highlight['highlight'],
                    highlight['context'],
                    highlight['context_translation'],
                    json.dumps(highlight.get('dictionary_meanings', []))
                ))
            
            conn.commit()
            return analysis_id
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Получение последних анализов"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, original_text, analysis_date, total_highlights, total_words
                FROM analyses 
                ORDER BY analysis_date DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'original_text': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                    'analysis_date': row[2],
                    'total_highlights': row[3],
                    'total_words': row[4]
                })
            
            return results
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Получение полного анализа по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем основную информацию
            cursor.execute("""
                SELECT original_text, analysis_date, total_highlights, total_words
                FROM analyses 
                WHERE id = ?
            """, (analysis_id,))
            
            analysis_row = cursor.fetchone()
            if not analysis_row:
                return None
            
            # Получаем хайлайты
            cursor.execute("""
                SELECT highlight_word, context, context_translation, dictionary_meanings
                FROM highlights 
                WHERE analysis_id = ?
            """, (analysis_id,))
            
            highlights = []
            for row in cursor.fetchall():
                highlights.append({
                    'highlight': row[0],
                    'context': row[1],
                    'context_translation': row[2],
                    'dictionary_meanings': json.loads(row[3]) if row[3] else []
                })
            
            return {
                'id': analysis_id,
                'original_text': analysis_row[0],
                'analysis_date': analysis_row[1],
                'stats': {
                    'total_highlights': analysis_row[2],
                    'total_words': analysis_row[3]
                },
                'highlights': highlights
            }
    
    def search_by_word(self, word: str, limit: int = 20) -> List[Dict]:
        """Поиск анализов по конкретному слову"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT a.id, a.original_text, a.analysis_date, h.highlight_word, h.context
                FROM analyses a
                JOIN highlights h ON a.id = h.analysis_id
                WHERE h.highlight_word LIKE ?
                ORDER BY a.analysis_date DESC
                LIMIT ?
            """, (f'%{word}%', limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'analysis_id': row[0],
                    'text_preview': row[1][:80] + '...' if len(row[1]) > 80 else row[1],
                    'date': row[2],
                    'highlight_word': row[3],
                    'context': row[4]
                })
            
            return results
    
    def get_stats(self) -> Dict:
        """Получение общей статистики"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Общее количество анализов
            cursor.execute("SELECT COUNT(*) FROM analyses")
            total_analyses = cursor.fetchone()[0]
            
            # Общее количество хайлайтов
            cursor.execute("SELECT COUNT(*) FROM highlights")
            total_highlights = cursor.fetchone()[0]
            
            # Самые популярные слова
            cursor.execute("""
                SELECT highlight_word, COUNT(*) as count
                FROM highlights 
                GROUP BY highlight_word 
                ORDER BY count DESC 
                LIMIT 10
            """)
            popular_words = [{'word': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return {
                'total_analyses': total_analyses,
                'total_highlights': total_highlights,
                'popular_words': popular_words
            }