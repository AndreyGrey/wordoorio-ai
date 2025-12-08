#!/usr/bin/env python3
"""
📋 КОНТРАКТЫ СИСТЕМЫ WORDOORIO

Единые интерфейсы для всех компонентов системы.
Изменение этих контрактов влияет на всю архитектуру!
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from enum import Enum


class PromptVersion(Enum):
    """Доступные версии промптов"""
    V1_BASIC = "v1_basic"
    V2_DUAL = "v2_dual"
    V3_ENHANCED = "v3_enhanced"


@dataclass
class Highlight:
    """Стандартный хайлайт во всей системе"""
    highlight: str                    # Найденное слово/фраза
    context: str                     # Контекст из текста
    highlight_translation: str       # Перевод слова/фразы (контекстный)
    cefr_level: str = "C1"          # Уровень сложности
    importance_score: int = 85       # Важность 0-100
    dictionary_meanings: List[str] = field(default_factory=list)
    why_interesting: str = ""        # Почему интересен

    # V3 новые поля (опциональные, не влияют на V1/V2):
    type: str = "word"               # "word", "expression", "pattern"
    pattern_template: str = ""       # Шаблон для patterns: "the way [subject] [verb] it"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        return {
            'highlight': self.highlight,
            'context': self.context,
            'highlight_translation': self.highlight_translation,
            'dictionary_meanings': self.dictionary_meanings,
            'cefr_level': self.cefr_level,
            'importance_score': self.importance_score,
            'why_interesting': self.why_interesting,
            'type': self.type,
            'pattern_template': self.pattern_template
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Highlight':
        """Создание из словаря"""
        return cls(
            highlight=data['highlight'],
            context=data['context'],
            highlight_translation=data.get('highlight_translation', ''),
            cefr_level=data.get('cefr_level', 'C1'),
            importance_score=data.get('importance_score', 85),
            dictionary_meanings=data.get('dictionary_meanings', []),
            why_interesting=data.get('why_interesting', ''),
            type=data.get('type', 'word'),
            pattern_template=data.get('pattern_template', '')
        )


@dataclass
class AnalysisRequest:
    """Запрос на анализ текста"""
    text: str                        # Текст для анализа
    page_id: str = "main"           # ID страницы: "main", "experimental", "future"
    user_session: Optional[str] = None
    
    def validate(self) -> Optional[str]:
        """Валидация запроса. Возвращает ошибку или None"""
        if not self.text.strip():
            return "Текст не может быть пустым"
        if len(self.text.split()) < 5:
            return "Текст слишком короткий (минимум 5 слов)"
        if len(self.text) > 100000:
            return "Текст слишком длинный (максимум 100000 символов)"
        return None


@dataclass
class AnalysisResult:
    """Результат анализа текста"""
    success: bool
    highlights: List[Highlight] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None
    performance: Optional[Dict[str, Any]] = None  # Метрики производительности
    
    def get_stats(self) -> Dict[str, int]:
        """Получить статистику анализа"""
        return {
            'total_highlights': len(self.highlights),
            'total_words': self.stats.get('total_words', 0),
            'success': 1 if self.success else 0
        }
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Преобразование в JSON для API ответа"""
        return {
            'success': self.success,
            'highlights': [h.to_dict() for h in self.highlights],
            'stats': self.get_stats(),
            'error': self.error,
            'performance': self.performance
        }


@dataclass
class PageConfig:
    """Конфигурация страницы анализа"""
    id: str                          # Уникальный ID страницы
    title: str                       # Заголовок страницы
    description: str                 # Описание
    prompt_version: PromptVersion    # Версия промпта для анализа
    ui_features: Dict[str, bool] = field(default_factory=dict)  # Включенные UI фичи
    max_text_length: int = 5000     # Лимит символов
    timeout_seconds: int = 60       # Таймаут анализа
    branding: Dict[str, str] = field(default_factory=dict)  # Цвета, логотип
    analytics_enabled: bool = True   # Сохранять ли в БД


@dataclass
class PromptMetadata:
    """Метаданные версии промпта"""
    id: str                         # "v1_basic", "v2_dual" 
    name: str                       # "Базовая версия"
    description: str                # Описание промпта
    is_stable: bool                 # Стабильная версия?
    created_at: str                 # Дата создания
    performance_score: float = 0.0  # Качество результатов (0-100)
    estimated_cost: float = 0.0     # Примерная стоимость за запрос в рублях


# ============================================================================
# АБСТРАКТНЫЕ ИНТЕРФЕЙСЫ (контракты для реализации)
# ============================================================================

class PromptStrategy(ABC):
    """Интерфейс для всех стратегий промптов"""
    
    @abstractmethod
    def get_metadata(self) -> PromptMetadata:
        """Получить метаданные версии промпта"""
        pass
    
    @abstractmethod
    async def analyze_text(self, text: str, ai_client) -> List[Highlight]:
        """Анализировать текст и вернуть хайлайты"""
        pass


class AIClient(ABC):
    """Интерфейс для AI клиентов (Yandex GPT, OpenAI, etc.)"""
    
    @abstractmethod
    async def request_gpt(self, prompt: str) -> str:
        """Отправить запрос к AI и получить ответ"""
        pass
    
    @abstractmethod
    async def translate_text(self, text: str, target_lang: str = "ru") -> str:
        """Перевести текст"""
        pass


class AnalysisRepository(ABC):
    """Интерфейс для сохранения результатов анализа"""
    
    @abstractmethod
    def save_analysis(self, request: AnalysisRequest, result: AnalysisResult) -> int:
        """Сохранить результат анализа. Возвращает ID"""
        pass
    
    @abstractmethod
    def get_analysis_by_id(self, analysis_id: int) -> Optional[AnalysisResult]:
        """Получить анализ по ID"""
        pass
    
    @abstractmethod
    def search_by_word(self, word: str) -> List[Dict]:
        """Найти анализы содержащие слово"""
        pass


class DeduplicationService(ABC):
    """Интерфейс для удаления дубликатов"""
    
    @abstractmethod
    def remove_duplicates(self, highlights: List[Highlight]) -> List[Highlight]:
        """Убрать дубликаты из списка хайлайтов"""
        pass


# ============================================================================
# УТИЛИТЫ
# ============================================================================

def create_error_result(error_message: str) -> AnalysisResult:
    """Создать результат с ошибкой"""
    return AnalysisResult(
        success=False,
        error=error_message,
        stats={'total_words': 0, 'total_highlights': 0}
    )


def create_success_result(highlights: List[Highlight], 
                         total_words: int,
                         performance: Optional[Dict] = None) -> AnalysisResult:
    """Создать успешный результат"""
    return AnalysisResult(
        success=True,
        highlights=highlights,
        stats={'total_words': total_words, 'total_highlights': len(highlights)},
        performance=performance
    )