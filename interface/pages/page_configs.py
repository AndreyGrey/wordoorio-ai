#!/usr/bin/env python3
"""
🎨 PAGE CONFIGURATIONS - Настройки страниц Wordoorio

Централизованное управление конфигурациями страниц,
включая настройки анимации, промптов и UI компонентов.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class PageType(Enum):
    """Типы страниц приложения"""
    MAIN = "main"
    ANALYSIS = "analysis"
    RESULTS = "results"
    SETTINGS = "settings"

class AnalysisMode(Enum):
    """Режимы анализа"""
    QUICK = "quick"
    DETAILED = "detailed"
    PROFESSIONAL = "professional"

@dataclass
class LoadingConfig:
    """Конфигурация анимации загрузки"""
    enable_animation: bool = True
    word_change_interval: int = 800  # мс
    max_words_to_show: int = 20
    min_word_length: int = 3
    progress_max_percent: int = 90
    fallback_words: List[str] = None
    
    def __post_init__(self):
        if self.fallback_words is None:
            self.fallback_words = [
                'analyzing', 'processing', 'thinking', 'working', 'parsing',
                'examining', 'exploring', 'discovering', 'evaluating', 'reviewing'
            ]

@dataclass
class PromptConfig:
    """Конфигурация промптов для страницы"""
    default_version: str = "v1_basic"
    enable_experimentation: bool = False
    fallback_version: str = "v1_basic"
    auto_select_best: bool = True
    performance_threshold: float = 80.0

@dataclass
class UIConfig:
    """Конфигурация UI элементов"""
    enable_dark_mode: bool = False
    animation_duration: int = 300  # мс
    debounce_input: int = 500  # мс
    max_text_length: int = 5000
    show_progress_bar: bool = True
    enable_sound_effects: bool = False

@dataclass
class PageConfig:
    """Основная конфигурация страницы"""
    page_type: PageType
    title: str
    description: str
    loading_config: LoadingConfig
    prompt_config: PromptConfig
    ui_config: UIConfig
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}

class PageConfigManager:
    """Менеджер конфигураций страниц"""
    
    def __init__(self):
        self._configs: Dict[PageType, PageConfig] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Настройка конфигураций по умолчанию"""
        
        # Главная страница
        self._configs[PageType.MAIN] = PageConfig(
            page_type=PageType.MAIN,
            title="Wordoorio - Изучай английский стильно",
            description="Находи выразительную лексику в любом тексте",
            loading_config=LoadingConfig(
                enable_animation=True,
                word_change_interval=1000,
                fallback_words=['welcome', 'explore', 'discover', 'learn', 'improve']
            ),
            prompt_config=PromptConfig(
                default_version="v1_basic",
                enable_experimentation=False,
                auto_select_best=False
            ),
            ui_config=UIConfig(
                animation_duration=500,
                max_text_length=3000,
                show_progress_bar=False
            )
        )
        
        # Страница анализа
        self._configs[PageType.ANALYSIS] = PageConfig(
            page_type=PageType.ANALYSIS,
            title="Анализ текста",
            description="Анализируем выразительную лексику",
            loading_config=LoadingConfig(
                enable_animation=True,
                word_change_interval=800,
                max_words_to_show=25,
                progress_max_percent=85
            ),
            prompt_config=PromptConfig(
                default_version="v1_basic",
                enable_experimentation=True,
                auto_select_best=True,
                performance_threshold=85.0
            ),
            ui_config=UIConfig(
                animation_duration=300,
                debounce_input=800,
                max_text_length=5000,
                show_progress_bar=True
            ),
            custom_settings={
                'enable_real_time_analysis': False,
                'show_word_count': True,
                'highlight_similar_words': True
            }
        )
        
        # Страница результатов
        self._configs[PageType.RESULTS] = PageConfig(
            page_type=PageType.RESULTS,
            title="Результаты анализа",
            description="Найденная выразительная лексика",
            loading_config=LoadingConfig(
                enable_animation=False
            ),
            prompt_config=PromptConfig(
                default_version="v1_basic",
                enable_experimentation=False
            ),
            ui_config=UIConfig(
                animation_duration=200,
                show_progress_bar=False
            ),
            custom_settings={
                'items_per_page': 20,
                'enable_export': True,
                'show_statistics': True,
                'enable_filtering': True
            }
        )
        
        # Страница настроек
        self._configs[PageType.SETTINGS] = PageConfig(
            page_type=PageType.SETTINGS,
            title="Настройки Wordoorio",
            description="Персонализируй свой опыт изучения",
            loading_config=LoadingConfig(
                enable_animation=False
            ),
            prompt_config=PromptConfig(
                default_version="v1_basic",
                enable_experimentation=True
            ),
            ui_config=UIConfig(
                animation_duration=300,
                enable_dark_mode=True
            ),
            custom_settings={
                'save_preferences': True,
                'sync_across_devices': False,
                'export_user_data': True
            }
        )
    
    def get_config(self, page_type: PageType) -> PageConfig:
        """Получить конфигурацию страницы"""
        if page_type not in self._configs:
            raise ValueError(f"Конфигурация для страницы {page_type} не найдена")
        return self._configs[page_type]
    
    def update_config(self, page_type: PageType, **kwargs):
        """Обновить конфигурацию страницы"""
        if page_type not in self._configs:
            raise ValueError(f"Конфигурация для страницы {page_type} не найдена")
        
        config = self._configs[page_type]
        
        # Обновляем настройки загрузки
        if 'loading_config' in kwargs:
            loading_updates = kwargs['loading_config']
            for key, value in loading_updates.items():
                if hasattr(config.loading_config, key):
                    setattr(config.loading_config, key, value)
        
        # Обновляем настройки промптов
        if 'prompt_config' in kwargs:
            prompt_updates = kwargs['prompt_config']
            for key, value in prompt_updates.items():
                if hasattr(config.prompt_config, key):
                    setattr(config.prompt_config, key, value)
        
        # Обновляем настройки UI
        if 'ui_config' in kwargs:
            ui_updates = kwargs['ui_config']
            for key, value in ui_updates.items():
                if hasattr(config.ui_config, key):
                    setattr(config.ui_config, key, value)
        
        # Обновляем кастомные настройки
        if 'custom_settings' in kwargs:
            config.custom_settings.update(kwargs['custom_settings'])
    
    def get_loading_config(self, page_type: PageType) -> LoadingConfig:
        """Получить конфигурацию загрузки для страницы"""
        return self.get_config(page_type).loading_config
    
    def get_prompt_config(self, page_type: PageType) -> PromptConfig:
        """Получить конфигурацию промптов для страницы"""
        return self.get_config(page_type).prompt_config
    
    def get_ui_config(self, page_type: PageType) -> UIConfig:
        """Получить конфигурацию UI для страницы"""
        return self.get_config(page_type).ui_config
    
    def get_analysis_mode_config(self, mode: AnalysisMode) -> Dict[str, Any]:
        """Получить конфигурацию для режима анализа"""
        mode_configs = {
            AnalysisMode.QUICK: {
                'prompt_version': 'v1_basic',
                'max_highlights': 10,
                'target_time': 5,  # секунды
                'enable_translations': True,
                'enable_examples': False
            },
            AnalysisMode.DETAILED: {
                'prompt_version': 'v2_dual',
                'max_highlights': 25,
                'target_time': 15,
                'enable_translations': True,
                'enable_examples': True
            },
            AnalysisMode.PROFESSIONAL: {
                'prompt_version': 'v2_dual',
                'max_highlights': 50,
                'target_time': 30,
                'enable_translations': True,
                'enable_examples': True,
                'enable_detailed_analysis': True
            }
        }
        
        return mode_configs.get(mode, mode_configs[AnalysisMode.QUICK])
    
    def export_config(self, page_type: PageType) -> Dict[str, Any]:
        """Экспортировать конфигурацию в словарь"""
        config = self.get_config(page_type)
        return {
            'page_type': config.page_type.value,
            'title': config.title,
            'description': config.description,
            'loading_config': {
                'enable_animation': config.loading_config.enable_animation,
                'word_change_interval': config.loading_config.word_change_interval,
                'max_words_to_show': config.loading_config.max_words_to_show,
                'min_word_length': config.loading_config.min_word_length,
                'progress_max_percent': config.loading_config.progress_max_percent,
                'fallback_words': config.loading_config.fallback_words
            },
            'prompt_config': {
                'default_version': config.prompt_config.default_version,
                'enable_experimentation': config.prompt_config.enable_experimentation,
                'fallback_version': config.prompt_config.fallback_version,
                'auto_select_best': config.prompt_config.auto_select_best,
                'performance_threshold': config.prompt_config.performance_threshold
            },
            'ui_config': {
                'enable_dark_mode': config.ui_config.enable_dark_mode,
                'animation_duration': config.ui_config.animation_duration,
                'debounce_input': config.ui_config.debounce_input,
                'max_text_length': config.ui_config.max_text_length,
                'show_progress_bar': config.ui_config.show_progress_bar,
                'enable_sound_effects': config.ui_config.enable_sound_effects
            },
            'custom_settings': config.custom_settings
        }

# Глобальный экземпляр менеджера
_page_config_manager = None

def get_page_config_manager() -> PageConfigManager:
    """Получить глобальный экземпляр PageConfigManager (Singleton)"""
    global _page_config_manager
    if _page_config_manager is None:
        _page_config_manager = PageConfigManager()
    return _page_config_manager

# Удобные функции для быстрого доступа
def get_config(page_type: PageType) -> PageConfig:
    """Быстрое получение конфигурации страницы"""
    return get_page_config_manager().get_config(page_type)

def get_loading_settings(page_type: PageType) -> Dict[str, Any]:
    """Получить настройки загрузки для JavaScript"""
    config = get_page_config_manager().get_loading_config(page_type)
    return {
        'wordChangeInterval': config.word_change_interval,
        'maxWordsToShow': config.max_words_to_show,
        'minWordLength': config.min_word_length,
        'progressMaxPercent': config.progress_max_percent,
        'fallbackWords': config.fallback_words
    }