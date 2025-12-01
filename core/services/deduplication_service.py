#!/usr/bin/env python3
"""
🔍 DEDUPLICATION SERVICE - Устранение дубликатов

Интеллектуальная система удаления дубликатов и схожих хайлайтов
с учетом семантической близости и морфологических вариантов.
"""

import re
import difflib
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from contracts.analysis_contracts import Highlight

class SimilarityType(Enum):
    """Типы схожести"""
    EXACT_DUPLICATE = "exact_duplicate"
    MORPHOLOGICAL = "morphological"  # walk/walking/walked
    SEMANTIC = "semantic"           # big/large/huge
    PARTIAL_OVERLAP = "partial_overlap"  # "make decision" vs "decision making"

@dataclass
class DuplicationInfo:
    """Информация о дублировании"""
    original_index: int
    duplicate_index: int
    similarity_score: float
    similarity_type: SimilarityType
    explanation: str

class DeduplicationService:
    """Сервис для устранения дубликатов хайлайтов"""
    
    def __init__(self):
        # Настройки дедупликации
        self.similarity_threshold = 0.8
        self.partial_overlap_threshold = 0.6
        self.morphological_threshold = 0.85
        
        # Кэш для оптимизации
        self._similarity_cache: Dict[Tuple[str, str], float] = {}
        
        # Паттерны для определения морфологических вариантов
        self.morphological_patterns = [
            (r'(\w+)ing$', r'\1'),      # walking -> walk
            (r'(\w+)ed$', r'\1'),       # walked -> walk
            (r'(\w+)s$', r'\1'),        # makes -> make
            (r'(\w+)er$', r'\1'),       # bigger -> big
            (r'(\w+)est$', r'\1'),      # biggest -> big
            (r'(\w+)ly$', r'\1'),       # quickly -> quick
        ]
        
        # Семантически схожие группы слов
        self.semantic_groups = {
            'big': ['large', 'huge', 'massive', 'enormous', 'giant', 'vast'],
            'small': ['tiny', 'little', 'minimal', 'minor', 'compact'],
            'good': ['excellent', 'great', 'wonderful', 'fantastic', 'amazing'],
            'bad': ['terrible', 'awful', 'horrible', 'poor', 'dreadful'],
            'fast': ['quick', 'rapid', 'swift', 'speedy', 'hasty'],
            'slow': ['sluggish', 'gradual', 'delayed', 'leisurely'],
            'smart': ['intelligent', 'clever', 'brilliant', 'wise', 'bright'],
            'important': ['crucial', 'vital', 'essential', 'critical', 'significant'],
            'easy': ['simple', 'effortless', 'straightforward', 'basic'],
            'difficult': ['hard', 'challenging', 'complex', 'tough', 'demanding']
        }
        
    def deduplicate_highlights(self, highlights: List[Highlight]) -> Tuple[List[Highlight], List[DuplicationInfo]]:
        """
        Удаляет дубликаты из списка хайлайтов
        
        Returns:
            Tuple[List[Highlight], List[DuplicationInfo]]: 
                Очищенные хайлайты и информация о найденных дубликатах
        """
        if not highlights:
            return [], []
        
        print(f"🔍 Начинаем дедупликацию {len(highlights)} хайлайтов...", flush=True)
        
        duplications = []
        indices_to_remove = set()
        
        # Сравниваем каждый хайлайт с каждым
        for i in range(len(highlights)):
            if i in indices_to_remove:
                continue
                
            for j in range(i + 1, len(highlights)):
                if j in indices_to_remove:
                    continue
                
                dup_info = self._check_similarity(highlights[i], highlights[j], i, j)
                
                if dup_info:
                    duplications.append(dup_info)
                    # Удаляем хайлайт с меньшим importance_score
                    if highlights[i].importance_score >= highlights[j].importance_score:
                        indices_to_remove.add(j)
                        print(f"🗑️  Удаляем дубликат: '{highlights[j].highlight}' (схож с '{highlights[i].highlight}')", flush=True)
                    else:
                        indices_to_remove.add(i)
                        print(f"🗑️  Удаляем дубликат: '{highlights[i].highlight}' (схож с '{highlights[j].highlight}')", flush=True)
                        break  # Выходим из внутреннего цикла, так как i уже помечен для удаления
        
        # Создаем новый список без дубликатов
        clean_highlights = [
            highlights[i] for i in range(len(highlights)) 
            if i not in indices_to_remove
        ]
        
        print(f"✅ Дедупликация завершена: {len(highlights)} -> {len(clean_highlights)} хайлайтов", flush=True)
        print(f"🔍 Найдено и удалено {len(indices_to_remove)} дубликатов", flush=True)
        
        return clean_highlights, duplications
    
    def _check_similarity(self, h1: Highlight, h2: Highlight, idx1: int, idx2: int) -> DuplicationInfo:
        """Проверяет схожесть двух хайлайтов"""
        text1 = h1.highlight.lower().strip()
        text2 = h2.highlight.lower().strip()
        
        # Точные дубликаты
        if text1 == text2:
            return DuplicationInfo(
                original_index=idx1,
                duplicate_index=idx2,
                similarity_score=1.0,
                similarity_type=SimilarityType.EXACT_DUPLICATE,
                explanation=f"Точный дубликат: '{text1}'"
            )
        
        # Морфологические варианты
        morph_score = self._calculate_morphological_similarity(text1, text2)
        if morph_score >= self.morphological_threshold:
            return DuplicationInfo(
                original_index=idx1,
                duplicate_index=idx2,
                similarity_score=morph_score,
                similarity_type=SimilarityType.MORPHOLOGICAL,
                explanation=f"Морфологические варианты: '{text1}' и '{text2}'"
            )
        
        # Семантическая схожесть
        semantic_score = self._calculate_semantic_similarity(text1, text2)
        if semantic_score >= self.similarity_threshold:
            return DuplicationInfo(
                original_index=idx1,
                duplicate_index=idx2,
                similarity_score=semantic_score,
                similarity_type=SimilarityType.SEMANTIC,
                explanation=f"Семантически схожие: '{text1}' и '{text2}'"
            )
        
        # Частичное перекрытие для фраз
        if ' ' in text1 or ' ' in text2:
            overlap_score = self._calculate_partial_overlap(text1, text2)
            if overlap_score >= self.partial_overlap_threshold:
                return DuplicationInfo(
                    original_index=idx1,
                    duplicate_index=idx2,
                    similarity_score=overlap_score,
                    similarity_type=SimilarityType.PARTIAL_OVERLAP,
                    explanation=f"Частичное перекрытие: '{text1}' и '{text2}'"
                )
        
        return None
    
    def _calculate_morphological_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет морфологическую схожесть"""
        # Проверяем кэш
        cache_key = (text1, text2) if text1 < text2 else (text2, text1)
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]
        
        # Убираем морфологические окончания
        stem1 = self._get_word_stem(text1)
        stem2 = self._get_word_stem(text2)
        
        # Если основы совпадают - высокая схожесть
        if stem1 == stem2 and len(stem1) > 3:
            score = 0.95
        else:
            # Используем difflib для сравнения
            score = difflib.SequenceMatcher(None, stem1, stem2).ratio()
        
        self._similarity_cache[cache_key] = score
        return score
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет семантическую схожесть"""
        # Ищем в предопределенных группах
        for group_words in self.semantic_groups.values():
            if text1 in group_words and text2 in group_words:
                return 0.9
        
        # Для фраз - проверяем пересечение ключевых слов
        if ' ' in text1 and ' ' in text2:
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Исключаем служебные слова
            stop_words = {'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words1 = words1 - stop_words
            words2 = words2 - stop_words
            
            if words1 and words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                return intersection / union if union > 0 else 0
        
        # Базовое сравнение строк
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _calculate_partial_overlap(self, text1: str, text2: str) -> float:
        """Вычисляет частичное перекрытие для фраз"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Проверяем, содержит ли одна фраза другую
        if words1.issubset(words2) or words2.issubset(words1):
            return 0.8
        
        # Вычисляем коэффициент Жаккара
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0
        
        jaccard_score = intersection / union
        
        # Бонус за порядок слов
        if self._check_word_order_similarity(text1, text2):
            jaccard_score += 0.1
        
        return min(jaccard_score, 1.0)
    
    def _get_word_stem(self, word: str) -> str:
        """Получает основу слова, убирая морфологические окончания"""
        for pattern, replacement in self.morphological_patterns:
            match = re.match(pattern, word)
            if match:
                return match.group(1)
        return word
    
    def _check_word_order_similarity(self, text1: str, text2: str) -> bool:
        """Проверяет схожесть порядка слов в фразах"""
        words1 = text1.split()
        words2 = text2.split()
        
        # Ищем общие слова в схожих позициях
        common_positions = 0
        for i, word1 in enumerate(words1):
            for j, word2 in enumerate(words2):
                if word1 == word2 and abs(i - j) <= 1:  # Слово в той же или соседней позиции
                    common_positions += 1
                    break
        
        return common_positions >= min(len(words1), len(words2)) * 0.5
    
    def analyze_duplications(self, duplications: List[DuplicationInfo]) -> Dict[str, any]:
        """Анализирует найденные дубликаты"""
        if not duplications:
            return {
                'total_duplicates': 0,
                'by_type': {},
                'average_similarity': 0,
                'recommendations': []
            }
        
        by_type = {}
        total_similarity = 0
        
        for dup in duplications:
            dup_type = dup.similarity_type.value
            if dup_type not in by_type:
                by_type[dup_type] = 0
            by_type[dup_type] += 1
            total_similarity += dup.similarity_score
        
        average_similarity = total_similarity / len(duplications)
        
        # Рекомендации
        recommendations = []
        if by_type.get('exact_duplicate', 0) > 0:
            recommendations.append("Найдены точные дубликаты - проверьте логику извлечения")
        if by_type.get('morphological', 0) > 3:
            recommendations.append("Много морфологических вариантов - рассмотрите стемминг")
        if by_type.get('semantic', 0) > 2:
            recommendations.append("Найдены семантически схожие слова - возможно улучшить промпт")
        
        return {
            'total_duplicates': len(duplications),
            'by_type': by_type,
            'average_similarity': round(average_similarity, 3),
            'recommendations': recommendations
        }
    
    def get_statistics(self, original_count: int, final_count: int, duplications: List[DuplicationInfo]) -> Dict[str, any]:
        """Получить статистику дедупликации"""
        removed_count = original_count - final_count
        removal_percentage = (removed_count / original_count * 100) if original_count > 0 else 0
        
        return {
            'original_count': original_count,
            'final_count': final_count,
            'removed_count': removed_count,
            'removal_percentage': round(removal_percentage, 1),
            'duplications_found': len(duplications),
            'quality_improvement': self._estimate_quality_improvement(duplications)
        }
    
    def _estimate_quality_improvement(self, duplications: List[DuplicationInfo]) -> str:
        """Оценивает улучшение качества"""
        if not duplications:
            return "no_change"
        
        high_similarity_count = sum(1 for dup in duplications if dup.similarity_score > 0.9)
        
        if high_similarity_count >= len(duplications) * 0.7:
            return "significant"
        elif high_similarity_count >= len(duplications) * 0.4:
            return "moderate"
        else:
            return "minor"

# Глобальный экземпляр сервиса
_deduplication_service = None

def get_deduplication_service() -> DeduplicationService:
    """Получить глобальный экземпляр DeduplicationService (Singleton)"""
    global _deduplication_service
    if _deduplication_service is None:
        _deduplication_service = DeduplicationService()
    return _deduplication_service