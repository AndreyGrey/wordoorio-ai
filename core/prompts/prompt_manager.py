#!/usr/bin/env python3
"""
🔄 PROMPT MANAGER - Управление версиями промптов

Центральная система для регистрации, получения и управления 
различными версиями промптов в Wordoorio.
"""

from typing import Dict, List, Optional
from contracts.analysis_contracts import PromptStrategy, PromptMetadata, PromptVersion


class PromptManager:
    """Центральное управление версиями промптов"""
    
    def __init__(self):
        self._strategies: Dict[str, PromptStrategy] = {}
        self._register_all_prompts()
    
    def _register_all_prompts(self):
        """Автоматическая регистрация всех доступных промптов"""
        try:
            # Импортируем и регистрируем все версии
            from core.prompts.versions.v1_basic import BasicPromptV1
            from core.prompts.versions.v2_dual import DualPromptV2
            
            self.register_prompt(BasicPromptV1())
            self.register_prompt(DualPromptV2())
            
            print(f"✅ Зарегистрировано {len(self._strategies)} версий промптов", flush=True)
            
        except ImportError as e:
            print(f"⚠️ Ошибка импорта версий промптов: {e}", flush=True)
    
    def register_prompt(self, strategy: PromptStrategy):
        """Регистрирует новую версию промпта"""
        metadata = strategy.get_metadata()
        self._strategies[metadata.id] = strategy
        print(f"📋 Зарегистрирован промпт: {metadata.id} - {metadata.name}", flush=True)
    
    def get_prompt(self, version_id: str) -> PromptStrategy:
        """Получить промпт по ID версии"""
        if version_id not in self._strategies:
            available = list(self._strategies.keys())
            raise ValueError(f"Промпт '{version_id}' не найден. Доступные: {available}")
        
        return self._strategies[version_id]
    
    def get_prompt_by_enum(self, version: PromptVersion) -> PromptStrategy:
        """Получить промпт по enum значению"""
        return self.get_prompt(version.value)
    
    def list_versions(self) -> List[PromptMetadata]:
        """Получить метаданные всех версий"""
        return [strategy.get_metadata() for strategy in self._strategies.values()]
    
    def get_stable_version(self) -> PromptStrategy:
        """Получить текущую стабильную версию"""
        for strategy in self._strategies.values():
            if strategy.get_metadata().is_stable:
                return strategy
        
        # Если стабильной нет, возвращаем первую доступную
        if self._strategies:
            return next(iter(self._strategies.values()))
        
        raise ValueError("Нет доступных промптов")
    
    def get_version_info(self, version_id: str) -> Optional[PromptMetadata]:
        """Получить информацию о версии"""
        if version_id in self._strategies:
            return self._strategies[version_id].get_metadata()
        return None
    
    def validate_version(self, version_id: str) -> bool:
        """Проверить существует ли версия"""
        return version_id in self._strategies
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Получить статистику производительности всех версий"""
        stats = {}
        for strategy in self._strategies.values():
            metadata = strategy.get_metadata()
            stats[metadata.id] = {
                'performance_score': metadata.performance_score,
                'estimated_cost': metadata.estimated_cost,
                'is_stable': metadata.is_stable
            }
        return stats
    
    def recommend_version(self, requirements: Dict[str, any]) -> str:
        """Рекомендовать версию на основе требований"""
        # Простая логика рекомендаций
        need_stability = requirements.get('stability', True)
        max_cost = requirements.get('max_cost', float('inf'))
        min_performance = requirements.get('min_performance', 0)
        
        candidates = []
        
        for strategy in self._strategies.values():
            metadata = strategy.get_metadata()
            
            # Проверяем требования
            if need_stability and not metadata.is_stable:
                continue
            if metadata.estimated_cost > max_cost:
                continue
            if metadata.performance_score < min_performance:
                continue
            
            candidates.append((metadata.id, metadata.performance_score))
        
        if not candidates:
            # Возвращаем стабильную версию как fallback
            return self.get_stable_version().get_metadata().id
        
        # Сортируем по производительности и возвращаем лучший
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]


# Глобальный экземпляр менеджера
_prompt_manager_instance = None

def get_prompt_manager() -> PromptManager:
    """Получить глобальный экземпляр PromptManager (Singleton)"""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance