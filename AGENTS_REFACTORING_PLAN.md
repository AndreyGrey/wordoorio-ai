# План реорганизации системы агентов и промптов Wordoorio

**Дата:** 11 декабря 2024 (обновлено 16 декабря 2024)
**Статус:** Согласован, готов к реализации
**Версия:** 2.0 (актуализирован)

---

## 🚨 КЛЮЧЕВЫЕ УТОЧНЕНИЯ (версия 2.0)

### ✅ Согласовано и уточнено:

1. **Промпты в AI Studio**
   - ✅ Агенты УЖЕ созданы в Yandex AI Studio
   - ✅ Промпты УЖЕ написаны там (другие, не из v1/v2/v3)
   - ✅ Ничего НЕ переносим из кода - промпты уже готовы
   - ✅ Все дальнейшие работы с промптами только в AI Studio

2. **Асинхронность (async/await)**
   - ✅ Делаем СРАЗУ async (не sync → async потом)
   - ✅ Используем `aiohttp` вместо `requests`
   - ✅ Параллельные вызовы через `asyncio.gather()`
   - ✅ Выигрыш: в 2 раза быстрее для пользователя

3. **IAM токены**
   - ✅ Background task с обновлением каждые 11 часов
   - ✅ НЕ проверяем при каждом запросе (токен живёт 12 часов)
   - ✅ Простой и надёжный подход

4. **YouTube функционал**
   - ✅ Удаляем ПОЛНОСТЬЮ (endpoint + код + зависимости)
   - ✅ Не используется на фронтенде
   - ✅ Вернёмся к этому позже с нуля

5. **Порядок миграции**
   - ✅ Создать новый код → Протестировать → Удалить старый
   - ✅ НЕ удаляем старое до тестирования нового!

6. **Дедупликация**
   - ✅ Оставляем как есть, без усложнений
   - ✅ Если практика покажет проблемы - вернёмся к улучшению

7. **База данных**
   - ✅ Почистить БД от лишних полей (cefr_level, importance_score и т.д.)
   - ✅ Миграция для удаления неиспользуемых столбцов

---

## 📋 Оглавление

1. [Обзор проекта](#обзор-проекта)
2. [Текущее состояние](#текущее-состояние)
3. [Целевое состояние](#целевое-состояние)
4. [Что удалить](#что-удалить)
5. [Что создать](#что-создать)
6. [Что изменить](#что-изменить)
7. [Фронтенд: Чистка и оптимизация](#фронтенд-чистка-и-оптимизация)
8. [Новая архитектура](#новая-архитектура)
9. [JSON контракты](#json-контракты)
10. [Yandex AI Studio агенты](#yandex-ai-studio-агенты)
11. [Структура файлов](#структура-файлов)
12. [План миграции](#план-миграции-обновлён)
13. [Чек-лист зависимостей](#чек-лист-зависимостей)
14. [Тестирование](#тестирование)

---

## 📊 Обзор проекта

### Цель реорганизации

Упростить и оптимизировать систему анализа текста, перенеся логику промптов из Python кода в Yandex AI Studio.

### Ключевые изменения

1. **Промпты уходят в Yandex AI Studio** - больше не захардкожены в коде
2. **Агенты вместо стратегий** - вызовы к Yandex AI вместо версий промптов
3. **Упрощённая архитектура** - удаление PromptManager, версионирования, лишних слоёв
4. **Чистка кода** - удаление 33KB v3_adaptive.py и других огромных файлов

---

## 📸 Текущее состояние

### Проблемы текущей архитектуры

```
❌ ПРОБЛЕМЫ:

1. Промпты захардкожены в Python коде
   - v1_basic.py: 198 строк
   - v2_dual.py: ~300 строк
   - v3_adaptive.py: 33KB! (огромный файл)

2. Дублирование логики
   - Все v1/v2/v3 парсят JSON
   - Все валидируют данные
   - Все получают dictionary meanings

3. Путаница терминов
   - "Агент 1" на самом деле не агент
   - "Промпты" называются агентами

4. Сложное версионирование
   - PromptManager
   - Маппинг страниц на версии
   - Метаданные промптов

5. YouTube Agent не работает
   - 311 строк мёртвого кода
```

### Текущая структура файлов

```
/Wordoorio/
├── agents/
│   └── youtube_agent.py          ❌ УДАЛИТЬ (311 строк)
│
├── core/
│   ├── prompts/                   ❌ УДАЛИТЬ (весь каталог)
│   │   ├── prompt_manager.py      ❌ 132 строки
│   │   └── versions/
│   │       ├── v1_basic.py        ❌ 198 строк
│   │       ├── v2_dual.py         ❌ ~300 строк
│   │       └── v3_adaptive.py     ❌ 33KB!!!
│   │
│   ├── analysis_service.py        ⚠️  УПРОСТИТЬ
│   ├── yandex_ai_client.py        ⚠️  ИЗМЕНИТЬ
│   │
│   └── services/
│       └── deduplication_service.py  ✅ ОСТАВИТЬ
│
├── utils/
│   └── lemmatizer.py              ✅ ОСТАВИТЬ
│
└── contracts/
    └── analysis_contracts.py      ⚠️  УПРОСТИТЬ
```

**Итого удаляется:** ~35KB кода + весь каталог `/core/prompts/`

---

## 🎯 Целевое состояние

### Новая архитектура (упрощённая)

```
┌─────────────────────────────────────────────┐
│          WEB APP (Flask)                    │
│  /analyze, /youtube/analyze endpoints      │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│     ANALYSIS ORCHESTRATOR (упрощённый)      │
│                                              │
│  1. Получить текст                          │
│  2. Вызвать оба агента (параллельно)        │
│  3. Объединить результаты                   │
│  4. Определить type по агенту               │
│  5. Лемматизация                            │
│  6. Дедупликация                            │
│  7. Добавить dictionary_meanings            │
│  8. Вернуть результат                       │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│        YANDEX AI CLIENT (новый API)         │
│                                              │
│  async def analyze_words(text) → Agent 1    │
│  async def analyze_phrases(text) → Agent 2  │
│  async def generate_test_options(...) → 3   │
│                                              │
│  def get_dictionary_meanings(word) ✅       │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┬───────────────┐
        ↓                 ↓               ↓
┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│ Yandex Agent │  │ Yandex Agent │  │ Yandex Agent│
│  #1 (слова)  │  │ #2 (фразы)   │  │ #3 (тесты)  │
└──────────────┘  └──────────────┘  └─────────────┘
```

### Ключевые преимущества

✅ **Простота** - нет версионирования, нет стратегий, нет менеджеров
✅ **Гибкость** - промпты редактируются в Yandex AI Studio (без перекомпиляции)
✅ **Производительность** - параллельные вызовы агентов
✅ **Поддерживаемость** - меньше кода, меньше слоёв абстракции

---

## 🗑️ ЧТО УДАЛИТЬ

### Файлы на полное удаление

```bash
# 1. Удалить весь каталог agents/
rm -rf /Users/andrewkondakow/Documents/Projects/Wordoorio/agents/

# 2. Удалить весь каталог core/prompts/
rm -rf /Users/andrewkondakow/Documents/Projects/Wordoorio/core/prompts/

# Итого удалено:
# - agents/youtube_agent.py (311 строк)
# - core/prompts/prompt_manager.py (132 строки)
# - core/prompts/versions/v1_basic.py (198 строк)
# - core/prompts/versions/v2_dual.py (~300 строк)
# - core/prompts/versions/v3_adaptive.py (33KB!)
```

### Части кода на удаление

#### **`contracts/analysis_contracts.py`**

```python
# УДАЛИТЬ эти классы:

class PromptVersion(Enum):
    """Доступные версии промптов"""
    V1_BASIC = "v1_basic"
    V2_DUAL = "v2_dual"
    V3_ENHANCED = "v3_enhanced"

class PromptStrategy(ABC):
    """Базовый интерфейс стратегии"""
    @abstractmethod
    def get_metadata(self) -> PromptMetadata:
        pass

    @abstractmethod
    async def analyze_text(self, text: str, ai_client) -> List[Highlight]:
        pass

@dataclass
class PromptMetadata:
    id: str
    name: str
    description: str
    is_stable: bool
    created_at: str
    performance_score: float
    estimated_cost: float
```

#### **`contracts/analysis_contracts.py` - Highlight**

```python
# УДАЛИТЬ эти поля из @dataclass Highlight:

cefr_level: str = "C1"          # ❌ УДАЛИТЬ
importance_score: int = 85       # ❌ УДАЛИТЬ
why_interesting: str = ""        # ❌ УДАЛИТЬ
pattern_template: str = ""       # ❌ УДАЛИТЬ

# ИЗМЕНИТЬ поле type:
type: str = "word"  # ❌ Было так

# На:
from enum import Enum

class HighlightType(Enum):
    WORD = "word"
    EXPRESSION = "expression"

type: HighlightType = HighlightType.WORD  # ✅ Стало так
```

#### **`core/yandex_ai_client.py`**

```python
# УДАЛИТЬ метод:

async def translate_text(self, text: str, target_lang: str = "ru") -> str:
    """Перевод текста через Yandex Translate"""
    # ...удалить весь метод...

async def _translate_text(self, text: str) -> str:
    """Внутренний метод перевода"""
    # ...удалить весь метод...
```

---

## ✨ ЧТО СОЗДАТЬ

### 1. Новый Enum для типа Highlight

**Файл:** `/contracts/analysis_contracts.py`

```python
from enum import Enum

class HighlightType(Enum):
    """Тип найденного элемента"""
    WORD = "word"          # Отдельное слово
    EXPRESSION = "expression"  # Фраза, выражение
```

### 2. Новые методы в YandexAIClient

**Файл:** `/core/yandex_ai_client.py`

```python
class YandexAIClient:
    # Константы URI агентов
    AGENT_WORDS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
    AGENT_WORDS_ID = "fvt3bjtu1ehmg0v8tss3"

    AGENT_PHRASES_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
    AGENT_PHRASES_ID = "fvt6j0ev2cgf1q2itfr6"

    AGENT_TESTS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/gpt-oss-120b/latest"
    AGENT_TESTS_ID = "fvtludf1115lb39bei78"

    async def analyze_words(self, text: str) -> List[Dict]:
        """
        Вызов Агента #1 (анализ слов) в Yandex AI Studio

        Args:
            text: Английский текст для анализа

        Returns:
            [
                {
                    "highlight": "sophisticated",
                    "context": "This is a sophisticated approach.",
                    "translation": "утончённый"
                },
                ...
            ]
        """
        pass

    async def analyze_phrases(self, text: str) -> List[Dict]:
        """
        Вызов Агента #2 (анализ фраз) в Yandex AI Studio

        Args:
            text: Английский текст для анализа

        Returns:
            [
                {
                    "highlight": "break down",
                    "context": "Let me break down this concept.",
                    "translation": "разобрать, объяснить"
                },
                ...
            ]
        """
        pass

    async def generate_test_options(
        self,
        words_with_translations: List[Dict]
    ) -> Dict:
        """
        Вызов Агента #3 (генерация тестов) в Yandex AI Studio

        Args:
            words_with_translations: [
                {"word": "sophisticated", "correct_translation": "утончённый"},
                ...
            ]

        Returns:
            {
                "tests": [
                    {
                        "word": "sophisticated",
                        "correct_translation": "утончённый",
                        "wrong_options": ["сложный", "изощренный", "продвинутый"]
                    }
                ]
            }
        """
        pass
```

### 3. Упрощённый AnalysisOrchestrator

**Файл:** `/core/analysis_orchestrator.py` (переименовать из analysis_service.py)

```python
#!/usr/bin/env python3
"""
🎯 ANALYSIS ORCHESTRATOR - Оркестратор анализа текста
Упрощённая версия без версионирования промптов
"""

import time
import asyncio
from typing import List
from contracts.analysis_contracts import (
    AnalysisRequest,
    AnalysisResult,
    Highlight,
    HighlightType,
    create_error_result,
    create_success_result
)
from core.yandex_ai_client import YandexAIClient
from core.services.deduplication_service import get_deduplication_service
from utils.lemmatizer import lemmatize, lemmatize_russian


class AnalysisOrchestrator:
    """
    Оркестратор анализа текста
    Вызывает агенты Yandex AI Studio и обрабатывает результаты
    """

    def __init__(self):
        self.ai_client = YandexAIClient()
        self.deduplication_service = get_deduplication_service()

    async def analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Главный метод анализа текста

        Workflow:
        1. Валидация запроса
        2. Параллельный вызов агентов (слова + фразы)
        3. Объединение результатов
        4. Определение type по агенту
        5. Лемматизация
        6. Дедупликация
        7. Добавление dictionary_meanings
        8. Формирование результата
        """
        print(f"\n{'='*60}")
        print(f"🎯 ЗАПУСК АНАЛИЗА")
        print(f"{'='*60}\n", flush=True)

        start_time = time.time()

        # 1. Валидация
        validation_error = request.validate()
        if validation_error:
            return create_error_result(validation_error)

        try:
            # 2. Параллельный вызов агентов
            print("📡 Вызываем агенты Yandex AI Studio...", flush=True)

            words_task = self.ai_client.analyze_words(request.text)
            phrases_task = self.ai_client.analyze_phrases(request.text)

            words_data, phrases_data = await asyncio.gather(
                words_task,
                phrases_task
            )

            print(f"✅ Агент #1 (слова): {len(words_data)} элементов", flush=True)
            print(f"✅ Агент #2 (фразы): {len(phrases_data)} элементов", flush=True)

            # 3. Преобразуем в Highlight объекты
            highlights = []

            # Слова
            for item in words_data:
                highlight = self._create_highlight_from_agent_response(
                    item,
                    HighlightType.WORD
                )
                highlights.append(highlight)

            # Фразы
            for item in phrases_data:
                highlight = self._create_highlight_from_agent_response(
                    item,
                    HighlightType.EXPRESSION
                )
                highlights.append(highlight)

            print(f"📊 Всего хайлайтов до обработки: {len(highlights)}", flush=True)

            # 4. Лемматизация
            print("\n🔤 Лемматизация...", flush=True)
            highlights = self._lemmatize_highlights(highlights)

            # 5. Дедупликация
            print("\n🔍 Дедупликация...", flush=True)
            highlights, duplications = self.deduplication_service.deduplicate_highlights(
                highlights
            )
            print(f"✅ После дедупликации: {len(highlights)} хайлайтов", flush=True)

            # 6. Добавляем dictionary meanings (только для слов!)
            print("\n📚 Получение dictionary meanings...", flush=True)
            highlights = await self._add_dictionary_meanings(highlights)

            # 7. Формируем результат
            end_time = time.time()
            performance = {
                'duration_seconds': round(end_time - start_time, 2),
                'highlights_before_dedup': len(highlights) + len(duplications),
                'highlights_after_dedup': len(highlights),
                'words_count': len([h for h in highlights if h.type == HighlightType.WORD]),
                'expressions_count': len([h for h in highlights if h.type == HighlightType.EXPRESSION])
            }

            result = create_success_result(
                highlights=highlights,
                total_words=len(request.text.split()),
                performance=performance
            )

            print(f"\n{'='*60}")
            print(f"✅ АНАЛИЗ ЗАВЕРШЕН")
            print(f"⏱️  Время: {performance['duration_seconds']}с")
            print(f"📊 Хайлайтов: {len(highlights)}")
            print(f"   - Слов: {performance['words_count']}")
            print(f"   - Фраз: {performance['expressions_count']}")
            print(f"{'='*60}\n", flush=True)

            return result

        except Exception as e:
            print(f"\n❌ ОШИБКА: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return create_error_result(f"Ошибка анализа: {str(e)}")

    def _create_highlight_from_agent_response(
        self,
        data: Dict,
        highlight_type: HighlightType
    ) -> Highlight:
        """Создаёт Highlight из ответа агента"""
        return Highlight(
            highlight=data['highlight'],
            context=data['context'],
            highlight_translation=data['translation'],
            type=highlight_type,
            dictionary_meanings=[]  # Добавим позже
        )

    def _lemmatize_highlights(self, highlights: List[Highlight]) -> List[Highlight]:
        """Лемматизация слов и переводов"""
        for highlight in highlights:
            # Лемматизация английского слова/фразы
            if highlight.type == HighlightType.WORD:
                highlight.highlight = lemmatize(highlight.highlight)

            # Лемматизация русского перевода
            highlight.highlight_translation = lemmatize_russian(
                highlight.highlight_translation
            )

        return highlights

    async def _add_dictionary_meanings(
        self,
        highlights: List[Highlight]
    ) -> List[Highlight]:
        """Добавляет словарные значения (только для отдельных слов!)"""
        for highlight in highlights:
            # Только для одиночных слов
            if highlight.type == HighlightType.WORD:
                try:
                    meanings = self.ai_client.get_dictionary_meanings(
                        highlight.highlight
                    )

                    # Фильтруем - убираем основной перевод
                    main_translation = highlight.highlight_translation.lower().strip()
                    filtered_meanings = [
                        m for m in meanings
                        if m.lower().strip() != main_translation
                    ]

                    highlight.dictionary_meanings = filtered_meanings

                except Exception as e:
                    print(f"⚠️  Ошибка получения meanings для '{highlight.highlight}': {e}", flush=True)

        return highlights


# Глобальный синглтон
_orchestrator_instance = None

def get_analysis_orchestrator() -> AnalysisOrchestrator:
    """Получить глобальный экземпляр AnalysisOrchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AnalysisOrchestrator()
    return _orchestrator_instance
```

---

## ⚙️ ЧТО ИЗМЕНИТЬ

### 1. `contracts/analysis_contracts.py`

**Изменения:**

```python
# БЫЛО:
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from enum import Enum

class PromptVersion(Enum):  # ❌ УДАЛИТЬ
    ...

class PromptStrategy(ABC):  # ❌ УДАЛИТЬ
    ...

@dataclass
class PromptMetadata:  # ❌ УДАЛИТЬ
    ...

@dataclass
class Highlight:
    highlight: str
    context: str
    highlight_translation: str
    cefr_level: str = "C1"          # ❌ УДАЛИТЬ
    importance_score: int = 85       # ❌ УДАЛИТЬ
    dictionary_meanings: List[str] = field(default_factory=list)
    why_interesting: str = ""        # ❌ УДАЛИТЬ
    type: str = "word"              # ❌ ИЗМЕНИТЬ
    pattern_template: str = ""       # ❌ УДАЛИТЬ

# СТАЛО:
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class HighlightType(Enum):  # ✅ НОВЫЙ
    """Тип найденного элемента"""
    WORD = "word"
    EXPRESSION = "expression"

@dataclass
class Highlight:
    """Стандартный хайлайт во всей системе"""
    highlight: str                    # Найденное слово/фраза
    context: str                     # Контекст из текста
    highlight_translation: str       # Перевод (контекстный от агента)
    type: HighlightType = HighlightType.WORD  # ✅ ИЗМЕНЕНО
    dictionary_meanings: List[str] = field(default_factory=list)  # ✅ ОСТАВЛЕНО

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON"""
        return {
            'highlight': self.highlight,
            'context': self.context,
            'highlight_translation': self.highlight_translation,
            'type': self.type.value,  # ✅ ИЗМЕНЕНО
            'dictionary_meanings': self.dictionary_meanings
        }
```

### 2. `core/yandex_ai_client.py`

**Добавить методы:**

```python
async def analyze_words(self, text: str) -> List[Dict]:
    """
    Вызов Агента #1 (анализ слов) в Yandex AI Studio

    Args:
        text: Английский текст для анализа

    Returns:
        List[Dict]: [
            {
                "highlight": "sophisticated",
                "context": "This is a sophisticated approach.",
                "translation": "утончённый"
            },
            ...
        ]
    """
    try:
        print(f"📡 Вызов Агента #1 (слова)...", flush=True)

        # Формируем запрос
        request_data = {
            "modelUri": self.AGENT_WORDS_URI,
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=request_data,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Yandex API error: {response.status_code} - {response.text}")

        result = response.json()

        # Парсим ответ агента (JSON)
        response_text = result['result']['alternatives'][0]['message']['text']
        highlights_data = json.loads(response_text)

        print(f"✅ Агент #1: получено {len(highlights_data)} слов", flush=True)

        return highlights_data

    except Exception as e:
        print(f"❌ Ошибка вызова Агента #1: {e}", flush=True)
        return []

async def analyze_phrases(self, text: str) -> List[Dict]:
    """
    Вызов Агента #2 (анализ фраз) в Yandex AI Studio

    Args:
        text: Английский текст для анализа

    Returns:
        List[Dict]: [
            {
                "highlight": "break down",
                "context": "Let me break down this concept.",
                "translation": "разобрать"
            },
            ...
        ]
    """
    try:
        print(f"📡 Вызов Агента #2 (фразы)...", flush=True)

        # Аналогично analyze_words, но с AGENT_PHRASES_URI
        request_data = {
            "modelUri": self.AGENT_PHRASES_URI,
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=request_data,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Yandex API error: {response.status_code} - {response.text}")

        result = response.json()

        # Парсим ответ агента (JSON)
        response_text = result['result']['alternatives'][0]['message']['text']
        highlights_data = json.loads(response_text)

        print(f"✅ Агент #2: получено {len(highlights_data)} фраз", flush=True)

        return highlights_data

    except Exception as e:
        print(f"❌ Ошибка вызова Агента #2: {e}", flush=True)
        return []

async def generate_test_options(
    self,
    words_with_translations: List[Dict]
) -> Dict:
    """
    Вызов Агента #3 (генерация тестов) в Yandex AI Studio

    Args:
        words_with_translations: [
            {"word": "sophisticated", "correct_translation": "утончённый"},
            ...
        ]

    Returns:
        {
            "tests": [
                {
                    "word": "sophisticated",
                    "correct_translation": "утончённый",
                    "wrong_options": ["сложный", "изощренный", "продвинутый"]
                }
            ]
        }
    """
    try:
        print(f"📡 Вызов Агента #3 (тесты) для {len(words_with_translations)} слов...", flush=True)

        # Формируем JSON запрос
        input_json = json.dumps({"words": words_with_translations}, ensure_ascii=False)

        request_data = {
            "modelUri": self.AGENT_TESTS_URI,
            "completionOptions": {
                "stream": False,
                "temperature": 0.5,
                "maxTokens": 3000
            },
            "messages": [
                {
                    "role": "user",
                    "text": input_json
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=request_data,
            timeout=180
        )

        if response.status_code != 200:
            raise Exception(f"Yandex API error: {response.status_code} - {response.text}")

        result = response.json()

        # Парсим ответ агента
        response_text = result['result']['alternatives'][0]['message']['text']
        tests_data = json.loads(response_text)

        print(f"✅ Агент #3: сгенерировано {len(tests_data.get('tests', []))} тестов", flush=True)

        return tests_data

    except Exception as e:
        print(f"❌ Ошибка вызова Агента #3: {e}", flush=True)
        return {"tests": []}
```

**Удалить методы:**

```python
# ❌ УДАЛИТЬ
async def translate_text(self, text: str, target_lang: str = "ru") -> str:
    ...

async def _translate_text(self, text: str) -> str:
    ...
```

**Оставить методы:**

```python
# ✅ ОСТАВИТЬ (важно!)
def get_dictionary_meanings(self, highlight_text: str) -> List[str]:
    """Получает альтернативные переводы через Yandex Dictionary API"""
    return self._get_dictionary_meanings(highlight_text)

def _get_dictionary_meanings(self, word: str) -> List[str]:
    """Реализация получения переводов"""
    # ...существующий код...
```

### 3. `web_app.py`

**Изменить импорты и использование:**

```python
# БЫЛО:
from core.analysis_service import get_analysis_service

@app.route('/analyze', methods=['POST'])
async def analyze():
    service = get_analysis_service()
    # ...

# СТАЛО:
from core.analysis_orchestrator import get_analysis_orchestrator

@app.route('/analyze', methods=['POST'])
async def analyze():
    orchestrator = get_analysis_orchestrator()

    request_data = request.get_json()
    analysis_request = AnalysisRequest(
        text=request_data['text'],
        page_id="main"  # Больше не имеет значения, одна логика
    )

    result = await orchestrator.analyze_text(analysis_request)

    # ... остальное без изменений
```

**Удалить логику выбора версии промпта:**

```python
# ❌ УДАЛИТЬ все упоминания:
# - page_id mapping
# - prompt version selection
# - experimental/v3 endpoints (или оставить, но они теперь ничем не отличаются)
```

---

## 🎨 ФРОНТЕНД: Чистка и оптимизация

### Обзор фронтенда

**Текущее состояние:**
- 6 HTML страниц (2 legacy experimental)
- 9 JS компонентов (1 использует удалённые поля)
- Компонентная архитектура (переиспользуемые модули)
- Адаптивный дизайн

**Проблема:**
- `experimental.html` и `v3.html` - legacy страницы для тестирования промптов
- `PatternCard.js` - компонент зависит от удалённых полей `pattern_template`, `why_interesting`
- Дублирование функционала между index.html и experimental.html

**Решение:** Удалить legacy код, оставить чистую компонентную архитектуру.

---

### 🗑️ Фронтенд: Что удалить

#### 1. HTML страницы (Legacy)

**experimental.html**
- **Путь:** `/templates/experimental.html`
- **Размер:** ~607 строк
- **Причина:** Дублирует index.html, использовала v2_dual промпт (удаляется)

**v3.html**
- **Путь:** `/templates/v3.html`
- **Размер:** ~578 строк
- **Причина:** Роут не существует, использовала v3_adaptive промпт (удаляется), зависит от PatternCard

---

#### 2. JS компоненты (Legacy)

**PatternCard.js**
- **Путь:** `/static/components/PatternCard.js`
- **Размер:** 70 строк
- **Проблема:** Использует `pattern.pattern_template` и `pattern.why_interesting` (удалённые поля)
- **Где используется:** Только в v3.html (удаляется)

```javascript
// Код компонента (ПРОБЛЕМА):
function createPatternCard(pattern, index) {
    return `
        <div class="pattern-template">
            ${pattern.pattern_template}  // ❌ поле удалено
        </div>
        <div class="pattern-explanation">
            ${pattern.why_interesting}   // ❌ поле удалено
        </div>
    `;
}
```

**PatternCard.css**
- **Путь:** `/static/components/PatternCard.css`
- **Размер:** ~80 строк
- **Причина:** Стили для удалённого компонента

---

#### 3. Backend Routes (для experimental страниц)

**web_app.py - удалить routes:**

```python
# ❌ УДАЛИТЬ:

@app.route('/experimental')
def experimental_page():
    return render_template('experimental.html')

@app.route('/experimental/analyze', methods=['POST'])
def experimental_analyze():
    # ~100 строк dual-prompt анализа
    ...
```

---

### ✅ Фронтенд: Что остаётся

#### Рабочие страницы (4 шт)

| Страница | Route | Назначение |
|----------|-------|------------|
| `index.html` | `/` | Главная страница анализа |
| `my-highlights.html` | `/my-highlights` | Сохранённые хайлайты |
| `history.html` | `/history` | История анализов |
| `dictionary.html` | `/dictionary` | Словарь пользователя |

---

#### Рабочие компоненты (8 шт)

| Компонент | Назначение | Статус |
|-----------|------------|--------|
| `AnalysisForm.js` | Универсальная форма анализа | ✅ Без изменений |
| `HighlightCard.js` | Карточка слова/фразы | ✅ Без изменений (НЕ затронут) |
| `Header.js` | Универсальная шапка | ✅ Без изменений |
| `DictionaryWordRow.js` | Строка словаря | ✅ Без изменений |
| `HighlightsStorage.js` | LocalStorage менеджер | ✅ Без изменений |
| `DictionaryAPI.js` | API обёртка | ✅ Без изменений |
| `Auth.js` | Telegram авторизация | ✅ Без изменений |
| `LoadingAnimation.js` | Анимация загрузки | ✅ Без изменений |

---

### ✅ КРИТИЧЕСКАЯ ПРОВЕРКА: HighlightCard.js

**Вопрос:** Использует ли HighlightCard.js удалённые поля?

**Ответ:** ✅ **НЕТ, компонент НЕ затронут!**

```javascript
// HighlightCard.js - используемые поля:
✅ highlight              // KEEP
✅ context                // KEEP
✅ highlight_translation  // KEEP
✅ dictionary_meanings    // KEEP
✅ type                   // KEEP (станет Enum)

// НЕ использует удалённые поля:
❌ cefr_level            // НЕ используется ✅
❌ importance_score      // НЕ используется ✅
❌ why_interesting       // НЕ используется ✅ (только PatternCard)
❌ pattern_template      // НЕ используется ✅ (только PatternCard)
```

**Вердикт:** ✅ HighlightCard.js работает без изменений после удаления полей!

---

### 📊 Метрики чистки фронтенда

#### До чистки
```
HTML страницы:     6 файлов  (~3500 строк)
JS компоненты:     9 файлов  (~2200 строк)
CSS файлы:         1 файл    (~80 строк)
Backend routes:    ~600 строк

Итого: ~6380 строк фронтенд кода
```

#### После чистки
```
HTML страницы:     4 файла   (~2300 строк) ↓ -34%
JS компоненты:     8 файлов  (~2014 строк) ↓ -8%
CSS файлы:         0 файлов  (0 строк)     ↓ -100%
Backend routes:    ~400 строк              ↓ -33%

Итого: ~4714 строк фронтенд кода ↓ -26%
```

**Результат:** Уменьшение кодовой базы фронтенда на **26%** (~1666 строк).

---

### 📝 Детальный анализ фронтенда

**Полный анализ в отдельном документе:**
- 📄 См. `/FRONTEND_CLEANUP_ANALYSIS.md` (1200+ строк подробного разбора)

**Содержит:**
- ✅ Инвентаризация всех компонентов
- ✅ Архитектурные рекомендации
- ✅ Детальный анализ каждого компонента
- ✅ Проверка зависимостей от Highlight полей
- ✅ Рекомендации на будущее (CSS переменные, TypeScript, бандлинг)

---

### ✅ Чек-лист: Фронтенд чистка

**Файлы для удаления:**
- [ ] `/templates/experimental.html`
- [ ] `/templates/v3.html`
- [ ] `/static/components/PatternCard.js`
- [ ] `/static/components/PatternCard.css`

**Routes для удаления (web_app.py):**
- [ ] `@app.route('/experimental')` → `def experimental_page()`
- [ ] `@app.route('/experimental/analyze')` → `def experimental_analyze()`

**Проверки после удаления:**
- [ ] Все 4 рабочие страницы открываются без ошибок
- [ ] HighlightCard.js работает на всех страницах
- [ ] Сохранение/удаление хайлайтов работает
- [ ] Нет ссылок на `/experimental` или `/v3` в коде
- [ ] Нет импортов `PatternCard` в коде
- [ ] Нет console.error в браузере

---

## 🏗️ Новая архитектура

### Полная диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                     WEB APPLICATION (Flask)                      │
│                                                                   │
│  Routes:                                                          │
│  - POST /analyze                → Анализ текста                  │
│  - POST /youtube/analyze        → Анализ YouTube видео           │
│  - POST /api/dictionary/add     → Добавить в словарь             │
│  - GET  /my-highlights          → Личные хайлайты                │
│                                                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│            ANALYSIS ORCHESTRATOR (Оркестратор)                   │
│                                                                   │
│  Workflow:                                                        │
│  1️⃣  Валидация запроса (текст не пустой, 5+ слов)               │
│  2️⃣  Параллельный вызов агентов:                                 │
│      • analyze_words(text)   → Agent #1                          │
│      • analyze_phrases(text) → Agent #2                          │
│  3️⃣  Объединение результатов (words + phrases)                   │
│  4️⃣  Определение type по агенту (Agent 1 = WORD, 2 = EXPRESSION)│
│  5️⃣  Лемматизация (английский + русский)                         │
│  6️⃣  Дедупликация (удаление одинаковых)                          │
│  7️⃣  Dictionary meanings (только для WORD)                       │
│  8️⃣  Формирование результата                                     │
│                                                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ↓                         ↓
┌──────────────────┐      ┌──────────────────┐
│ LEMMATIZER       │      │ DEDUPLICATION    │
│                  │      │ SERVICE          │
│ - lemmatize()    │      │                  │
│ - lemmatize_ru() │      │ 4 типа дубликатов│
│                  │      │ - Exact          │
│ (spaCy +         │      │ - Morphological  │
│  pymorphy2)      │      │ - Semantic       │
│                  │      │ - Partial        │
└──────────────────┘      └──────────────────┘
         ↓
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                YANDEX AI CLIENT (API интеграция)                 │
│                                                                   │
│  Методы для агентов:                                              │
│  • async def analyze_words(text) → Agent #1                      │
│  • async def analyze_phrases(text) → Agent #2                    │
│  • async def generate_test_options(words) → Agent #3             │
│                                                                   │
│  Словарные методы:                                                │
│  • def get_dictionary_meanings(word) → Yandex Dictionary API     │
│                                                                   │
│  Константы:                                                       │
│  • AGENT_WORDS_URI / ID                                          │
│  • AGENT_PHRASES_URI / ID                                        │
│  • AGENT_TESTS_URI / ID                                          │
│                                                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                   YANDEX AI STUDIO (Агенты)                      │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Agent #1        │  │  Agent #2        │  │  Agent #3    │  │
│  │  Words Analysis  │  │  Phrases Analysis│  │  Test Gen    │  │
│  │                  │  │                  │  │              │  │
│  │  Model:          │  │  Model:          │  │  Model:      │  │
│  │  qwen3-235b      │  │  qwen3-235b      │  │  gpt-oss-120b│  │
│  │                  │  │                  │  │              │  │
│  │  Промпт в Studio │  │  Промпт в Studio │  │  Промпт в    │  │
│  │  (не в коде!)    │  │  (не в коде!)    │  │  Studio      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
│  URI формат: gpt://folder_id/model_name/latest                  │
│  Идентификатор: fvt...                                          │
└─────────────────────────────────────────────────────────────────┘
         │                         │                    │
         ↓                         ↓                    ↓
    Возвращает JSON          Возвращает JSON     Возвращает JSON
    с highlights             с highlights        с тестами
```

### Поток данных

```
┌──────────────────────────────────────────────────────────────────┐
│ STEP 1: Пользователь отправляет текст                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 2: AnalysisOrchestrator → Yandex AI Client                  │
│                                                                    │
│  Параллельные запросы:                                             │
│  • analyze_words("This is sophisticated...")                      │
│  • analyze_phrases("This is sophisticated...")                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ↓                     ↓
┌──────────────────────┐  ┌──────────────────────┐
│ Agent #1 (слова)     │  │ Agent #2 (фразы)     │
│                      │  │                      │
│ Возвращает:          │  │ Возвращает:          │
│ [                    │  │ [                    │
│   {                  │  │   {                  │
│     "highlight":     │  │     "highlight":     │
│       "sophisticated"│  │       "break down",  │
│     "context": "..." │  │     "context": "..." │
│     "translation":   │  │     "translation":   │
│       "утончённый"   │  │       "разобрать"    │
│   }                  │  │   }                  │
│ ]                    │  │ ]                    │
└──────────────────────┘  └──────────────────────┘
                │                     │
                └──────────┬──────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 3: Объединение результатов                                  │
│                                                                    │
│  highlights = []                                                  │
│  for item in words_data:                                          │
│      highlight = Highlight(                                       │
│          highlight=item['highlight'],                             │
│          context=item['context'],                                 │
│          highlight_translation=item['translation'],               │
│          type=HighlightType.WORD  ← определяем по агенту          │
│      )                                                            │
│      highlights.append(highlight)                                 │
│                                                                    │
│  for item in phrases_data:                                        │
│      highlight = Highlight(                                       │
│          ...                                                      │
│          type=HighlightType.EXPRESSION  ← определяем по агенту    │
│      )                                                            │
│      highlights.append(highlight)                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 4: Лемматизация                                              │
│                                                                    │
│  for highlight in highlights:                                     │
│      if highlight.type == WORD:                                   │
│          highlight.highlight = lemmatize(highlight.highlight)     │
│      highlight.highlight_translation = lemmatize_russian(...)     │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 5: Дедупликация                                              │
│                                                                    │
│  Удаляет:                                                         │
│  • Exact duplicates (break down = break down от обоих агентов)   │
│  • Morphological (walking = walk)                                 │
│  • Semantic (big = large)                                         │
│  • Partial (make decision ≈ decision making)                      │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 6: Dictionary meanings (только для WORD!)                    │
│                                                                    │
│  for highlight in highlights:                                     │
│      if highlight.type == HighlightType.WORD:                     │
│          meanings = get_dictionary_meanings(highlight.highlight)  │
│          highlight.dictionary_meanings = meanings                 │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 7: Возврат результата                                        │
│                                                                    │
│  {                                                                │
│    "success": true,                                               │
│    "highlights": [                                                │
│      {                                                            │
│        "highlight": "sophisticated",                              │
│        "context": "...",                                          │
│        "highlight_translation": "утончённый",                     │
│        "type": "word",                                            │
│        "dictionary_meanings": ["изощрённый", "сложный"]           │
│      },                                                           │
│      {                                                            │
│        "highlight": "break down",                                 │
│        "context": "...",                                          │
│        "highlight_translation": "разобрать",                      │
│        "type": "expression",                                      │
│        "dictionary_meanings": []  ← пусто для фраз                │
│      }                                                            │
│    ],                                                             │
│    "stats": { "total_words": 125, "total_highlights": 12 },      │
│    "performance": { "duration_seconds": 15.3, ... }               │
│  }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📡 JSON Контракты

### Запрос к агентам Yandex AI Studio

**Формат запроса к агентам #1 и #2:**

```json
{
  "modelUri": "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest",
  "completionOptions": {
    "stream": false,
    "temperature": 0.3,
    "maxTokens": 2000
  },
  "messages": [
    {
      "role": "user",
      "text": "This is a sophisticated approach to solving complex problems in modern software development."
    }
  ]
}
```

**Ответ от агентов #1 и #2:**

```json
{
  "result": {
    "alternatives": [
      {
        "message": {
          "role": "assistant",
          "text": "[{\"highlight\": \"sophisticated\", \"context\": \"This is a sophisticated approach to solving problems.\", \"translation\": \"утончённый\"}, {\"highlight\": \"compelling\", \"context\": \"A compelling argument for change.\", \"translation\": \"убедительный\"}]"
        },
        "status": "ALTERNATIVE_STATUS_FINAL"
      }
    ],
    "usage": {
      "inputTextTokens": "125",
      "completionTokens": "250",
      "totalTokens": "375"
    },
    "modelVersion": "06.12.2024"
  }
}
```

**Парсинг:**
```python
response_text = result['result']['alternatives'][0]['message']['text']
highlights_data = json.loads(response_text)

# highlights_data теперь:
[
    {
        "highlight": "sophisticated",
        "context": "This is a sophisticated approach to solving problems.",
        "translation": "утончённый"
    },
    {
        "highlight": "compelling",
        "context": "A compelling argument for change.",
        "translation": "убедительный"
    }
]
```

### Запрос к агенту #3 (генерация тестов)

**Формат запроса:**

```json
{
  "modelUri": "gpt://b1gcdpfvt5vkfn3o9nm1/gpt-oss-120b/latest",
  "completionOptions": {
    "stream": false,
    "temperature": 0.5,
    "maxTokens": 3000
  },
  "messages": [
    {
      "role": "user",
      "text": "{\"words\": [{\"word\": \"sophisticated\", \"correct_translation\": \"утончённый\"}, {\"word\": \"compelling\", \"correct_translation\": \"убедительный\"}]}"
    }
  ]
}
```

**Ответ:**

```json
{
  "result": {
    "alternatives": [
      {
        "message": {
          "role": "assistant",
          "text": "{\"tests\": [{\"word\": \"sophisticated\", \"correct_translation\": \"утончённый\", \"wrong_options\": [\"сложный\", \"изощрённый\", \"продвинутый\"]}, {\"word\": \"compelling\", \"correct_translation\": \"убедительный\", \"wrong_options\": [\"принудительный\", \"обязательный\", \"настойчивый\"]}]}"
        }
      }
    ]
  }
}
```

**Парсинг:**
```python
response_text = result['result']['alternatives'][0]['message']['text']
tests_data = json.loads(response_text)

# tests_data теперь:
{
    "tests": [
        {
            "word": "sophisticated",
            "correct_translation": "утончённый",
            "wrong_options": ["сложный", "изощрённый", "продвинутый"]
        },
        {
            "word": "compelling",
            "correct_translation": "убедительный",
            "wrong_options": ["принудительный", "обязательный", "настойчивый"]
        }
    ]
}
```

---

## 🔑 Yandex AI Studio Агенты

### Конфигурация агентов

```python
# В core/yandex_ai_client.py

class YandexAIClient:
    """
    Агенты в Yandex AI Studio
    Настроены через веб-интерфейс: https://ai.yandex.cloud/studio
    """

    # АГЕНТ #1: Анализ слов
    AGENT_WORDS_NAME = "get highlight words"
    AGENT_WORDS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
    AGENT_WORDS_ID = "fvt3bjtu1ehmg0v8tss3"

    # АГЕНТ #2: Анализ фраз
    AGENT_PHRASES_NAME = "get highlight phrases"
    AGENT_PHRASES_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
    AGENT_PHRASES_ID = "fvt6j0ev2cgf1q2itfr6"

    # АГЕНТ #3: Генерация тестов
    AGENT_TESTS_NAME = "generate test"
    AGENT_TESTS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/gpt-oss-120b/latest"
    AGENT_TESTS_ID = "fvtludf1115lb39bei78"
```

### Как вызывать агенты

**Общий паттерн:**

```python
async def _call_agent(self, agent_uri: str, text: str) -> List[Dict]:
    """Универсальный метод вызова агента"""
    try:
        request_data = {
            "modelUri": agent_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=request_data,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Agent error: {response.status_code}")

        result = response.json()
        response_text = result['result']['alternatives'][0]['message']['text']

        # Парсим JSON из ответа
        data = json.loads(response_text)

        return data

    except Exception as e:
        print(f"❌ Ошибка вызова агента: {e}", flush=True)
        return []
```

---

## 📁 Структура файлов (итоговая)

### До реорганизации

```
/Wordoorio/
├── agents/                        ❌ УДАЛИТЬ (весь каталог)
│   └── youtube_agent.py           ❌ 311 строк
│
├── core/
│   ├── prompts/                   ❌ УДАЛИТЬ (весь каталог)
│   │   ├── prompt_manager.py      ❌ 132 строки
│   │   └── versions/
│   │       ├── v1_basic.py        ❌ 198 строк
│   │       ├── v2_dual.py         ❌ ~300 строк
│   │       └── v3_adaptive.py     ❌ 33KB!!!
│   │
│   ├── analysis_service.py        ⚠️  ПЕРЕИМЕНОВАТЬ → analysis_orchestrator.py
│   ├── yandex_ai_client.py        ⚠️  ИЗМЕНИТЬ (добавить методы агентов)
│   │
│   └── services/
│       └── deduplication_service.py  ✅ ОСТАВИТЬ
│
├── utils/
│   └── lemmatizer.py              ✅ ОСТАВИТЬ
│
├── contracts/
│   └── analysis_contracts.py      ⚠️  УПРОСТИТЬ (удалить PromptStrategy и т.д.)
│
└── web_app.py                     ⚠️  ИЗМЕНИТЬ (использовать orchestrator)
```

### После реорганизации

```
/Wordoorio/
├── core/
│   ├── analysis_orchestrator.py   ✨ НОВЫЙ (упрощённый, без версионирования)
│   ├── yandex_ai_client.py        ✅ ИЗМЕНЁН (добавлены методы агентов)
│   │
│   └── services/
│       └── deduplication_service.py  ✅ БЕЗ ИЗМЕНЕНИЙ
│
├── utils/
│   └── lemmatizer.py              ✅ БЕЗ ИЗМЕНЕНИЙ
│
├── contracts/
│   └── analysis_contracts.py      ✅ УПРОЩЁН (удалены PromptStrategy, PromptMetadata)
│                                     ✅ Добавлен HighlightType(Enum)
│                                     ✅ Упрощён Highlight (удалены 4 поля)
│
└── web_app.py                     ✅ ИЗМЕНЁН (использует orchestrator)
```

**Итоговая экономия:**
- Удалено: ~35KB кода
- Удалено: 2 каталога целиком (`agents/`, `prompts/`)
- Упрощено: 3 файла (`contracts`, `web_app`, `yandex_ai_client`)
- Создано: 1 файл (`analysis_orchestrator.py`)

---

## 🔄 План миграции (ОБНОВЛЁН v2.0)

**⚠️ ВАЖНО:** Порядок изменён! Сначала создаём новое, тестируем, потом удаляем старое.

---

### Этап 0: Подготовка (30 мин)

**Шаги:**
1. ✅ Проверили web_app.py - нашли YouTube agent import (строка 501)
2. Создать git ветку `refactor/agents-cleanup`
3. Backup БД
4. Проверить Yandex AI Studio агенты

```bash
cd /Users/andrewkondakow/Documents/Projects/Wordoorio
git checkout -b refactor/agents-cleanup
git status  # проверить чистоту
cp wordoorio.db wordoorio.db.backup
```

**Коммит:** Не требуется

---

### Этап 1: Обновление contracts (30 мин)

**Файл:** `/contracts/analysis_contracts.py`

**Шаги:**
1. Удалить классы `PromptVersion`, `PromptStrategy`, `PromptMetadata`
2. Добавить `HighlightType(Enum)`
3. Упростить `Highlight` (удалить 4 поля)
4. Обновить `to_dict()` и `from_dict()`

```bash
# Открыть файл
nano contracts/analysis_contracts.py

# Применить изменения (см. раздел "Что изменить")

# Коммит
git add contracts/analysis_contracts.py
git commit -m "refactor: упрощён Highlight, добавлен HighlightType enum"
```

---

### Этап 3: Добавление async методов в YandexAIClient (2 часа)

**Файл:** `/core/yandex_ai_client.py`

**Что делаем:**
1. Добавить в `requirements.txt`: `aiohttp==3.9.1`
2. Установить: `pip install aiohttp`
3. Добавить константы агентов (URI, ID)
4. Создать `async def analyze_words(self, text)` с `aiohttp`
5. Создать `async def analyze_phrases(self, text)` с `aiohttp`
6. Создать `async def generate_test_options(self, words)` с `aiohttp`
7. Добавить Background task для IAM токенов (обновление каждые 11 часов)
8. **Протестировать каждый метод**

**Изменения:**
```python
# Добавить импорты
import aiohttp
import asyncio
import threading

# Добавить константы
AGENT_WORDS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
AGENT_WORDS_ID = "fvt3bjtu1ehmg0v8tss3"

AGENT_PHRASES_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/qwen3-235b-a22b-fp8/latest"
AGENT_PHRASES_ID = "fvt6j0ev2cgf1q2itfr6"

AGENT_TESTS_URI = "gpt://b1gcdpfvt5vkfn3o9nm1/gpt-oss-120b/latest"
AGENT_TESTS_ID = "fvtludf1115lb39bei78"

# Background task для токенов
def _token_refresher_thread(self):
    """Обновляет IAM токен каждые 11 часов"""
    while True:
        time.sleep(11 * 60 * 60)  # 11 часов
        self._refresh_iam_token()
        print("✅ IAM токен обновлён (background task)")

# В __init__:
threading.Thread(target=self._token_refresher_thread, daemon=True).start()

# async методы с aiohttp
async def analyze_words(self, text: str) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Bearer {self.iam_token}",
                "x-folder-id": self.folder_id,
                "Content-Type": "application/json"
            },
            json={
                "modelUri": self.AGENT_WORDS_URI,
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 2000
                },
                "messages": [{"role": "user", "text": text}]
            },
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status == 401:  # Токен истёк
                self._refresh_iam_token()
                # Повторный запрос (рекурсия)
                return await self.analyze_words(text)

            result = await response.json()
            response_text = result['result']['alternatives'][0]['message']['text']
            return json.loads(response_text)
```

**Тест:**
```python
# test_agents.py
import asyncio
from core.yandex_ai_client import YandexAIClient

async def test():
    client = YandexAIClient()
    words = await client.analyze_words("This is sophisticated.")
    print(f"Words: {words}")

    phrases = await client.analyze_phrases("Let me break down this concept.")
    print(f"Phrases: {phrases}")

asyncio.run(test())
```

**Коммит:**
```bash
git add core/yandex_ai_client.py requirements.txt
git commit -m "feat: добавлены async методы для Yandex AI Studio агентов + background token refresh"
```

---

### Этап 5: Создание AnalysisOrchestrator (2 часа)

**Файл:** `/core/analysis_orchestrator.py`

**Шаги:**
1. Скопировать `analysis_service.py` → `analysis_orchestrator.py`
2. Удалить всё связанное с `PromptManager`
3. Переписать `analyze_text()` (см. раздел "Что создать")
4. Добавить методы лемматизации и dictionary meanings
5. Протестировать

```bash
# Копирование
cp core/analysis_service.py core/analysis_orchestrator.py

# Редактирование
nano core/analysis_orchestrator.py

# Применить изменения (см. раздел "Что создать")

# Тест
python core/analysis_orchestrator.py  # если есть __main__

git add core/analysis_orchestrator.py
git commit -m "feat: создан упрощённый AnalysisOrchestrator без версионирования"
```

---

### Этап 5: Обновление web_app.py (1 час)

**Файл:** `/web_app.py`

**Что делаем:**
1. Изменить импорт `analysis_service` → `analysis_orchestrator`
2. Добавить `async` к endpoint `/analyze`
3. Добавить `await` к вызову orchestrator
4. **Закомментировать YouTube endpoint** (строки 485-520)
5. Тестировать через curl и браузер

**Изменения:**
```python
# ДО:
from core.analysis_service import get_analysis_service

@app.route('/analyze', methods=['POST'])
def analyze_text():
    service = get_analysis_service()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(service.analyze_text(request))
    ...

# ПОСЛЕ:
from core.analysis_orchestrator import get_analysis_orchestrator

@app.route('/analyze', methods=['POST'])
async def analyze_text():  # ← Добавили async
    orchestrator = get_analysis_orchestrator()
    result = await orchestrator.analyze_text(request_data)  # ← Используем await напрямую
    ...
```

**Закомментировать YouTube endpoint:**
```python
# Строки 485-520 (весь блок)
# @app.route('/youtube/analyze', methods=['POST'])
# def analyze_youtube():
#     """
#     TODO: Реализовать заново позже (без agents/)
#     """
#     return jsonify({
#         'success': False,
#         'error': 'YouTube функционал временно отключен'
#     }), 503
```

**Тест:**
```bash
# 1. Запустить приложение
python web_app.py

# 2. Тест через curl
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a sophisticated approach to solving problems."}'

# 3. Тест в браузере
open http://localhost:8080
```

**Коммит:**
```bash
git add web_app.py
git commit -m "refactor: web_app использует AnalysisOrchestrator + async + закомментирован YouTube endpoint"
```

---

### Этап 6: Удаление старого кода (15 мин)

**⚠️ ВАЖНО: Делать ТОЛЬКО ПОСЛЕ успешного тестирования Этапа 5!**

**Что удаляем:**
1. Каталог `agents/` (весь)
2. Каталог `core/prompts/` (весь)
3. Файл `core/analysis_service.py`
4. Зависимости из `requirements.txt`: `youtube-transcript-api`, `yt-dlp`

```bash
# 1. Удалить каталоги
rm -rf agents/
rm -rf core/prompts/

# 2. Удалить старый analysis_service.py
rm core/analysis_service.py

# 3. Удалить зависимости из requirements.txt
# Открыть файл и удалить строки:
# - youtube-transcript-api==1.2.3
# - yt-dlp==2024.12.3

# 4. Коммит
git add -A
git commit -m "refactor: удалены agents/, prompts/, old analysis_service, YouTube зависимости"
```

---

### Этап 7: Финальное тестирование (1 час)

**Чек-лист:**

- [ ] Flask запускается без ошибок
- [ ] POST /analyze работает
- [ ] Агенты возвращают корректные данные в правильном формате
- [ ] **Параллелизм работает** (анализ быстрее ~10-15 сек)
- [ ] Лемматизация работает
- [ ] Дедупликация работает
- [ ] Dictionary meanings добавляются (только для слов)
- [ ] Результаты отображаются в браузере
- [ ] Нет ошибок в логах
- [ ] Проверить с разными текстами:
  - [ ] Короткий текст (5-10 слов)
  - [ ] Средний текст (50-100 слов)
  - [ ] Длинный текст (500+ слов)
- [ ] IAM токен background task работает (проверить логи)

**Тестирование:**
```bash
# 1. Запуск
python web_app.py

# 2. Браузер
open http://localhost:8080

# 3. Проверить логи - должна быть строка про background task
# "Background task: IAM token refresher started"
```

---

### Этап 8: Финализация (15 мин)

```bash
# Проверить что всё работает
git status

# Пуш в origin
git push origin refactor/agents-cleanup

# Создать PR или мержить в main
git checkout main
git merge refactor/agents-cleanup
git push origin main
```

---

### Этап 9: Очистка (5 мин)

```bash
# Удалить бэкап БД (если всё работает)
rm wordoorio.db.backup

# Удалить старую ветку
git branch -d refactor/agents-cleanup
```

---

## ⏱️ ИТОГОВОЕ ВРЕМЯ (обновлено v2.0)

| Этап | Время |
|------|-------|
| Этап 0: Подготовка | 30 мин |
| Этап 1: Обновление contracts | 30 мин |
| Этап 2: Обновление БД | 30 мин |
| Этап 3: async методы в YandexAIClient | 2 часа |
| Этап 4: Создание AnalysisOrchestrator | 2 часа |
| Этап 5: Обновление web_app.py | 1 час |
| Этап 6: Удаление старого кода | 15 мин |
| Этап 7: Финальное тестирование | 1 час |
| Этап 8: Финализация | 15 мин |
| Этап 9: Очистка | 5 мин |
| **ИТОГО** | **~8 часов** |

**Изменения по сравнению с v1.0:**
- ❌ Удалено: синхронный вариант
- ✅ Добавлено: async сразу + background task для токенов
- ✅ Добавлено: удаление YouTube функционала
- ✅ Изменено: порядок миграции (создать→тест→удалить)
- 🎯 Результат: **на 6-12 часов быстрее** чем в оригинальном плане (14-20 часов)

---

## ✅ Чек-лист зависимостей

### Что сломается при удалении

#### **1. Удаление `agents/youtube_agent.py`**

**Сломается:**
- Импорт в `web_app.py`: `from agents.youtube_agent import YouTubeTranscriptAgent`

**Исправление:**
- Закомментировать импорт
- Закомментировать endpoint `/youtube/analyze` (или реализовать по-новому позже)

---

#### **2. Удаление `core/prompts/`**

**Сломается:**
- Импорт в `core/analysis_service.py`: `from core.prompts.prompt_manager import get_prompt_manager`
- Импорт в `web_app.py` (если есть прямые импорты промптов)

**Исправление:**
- Удалить весь `analysis_service.py` (заменён на `analysis_orchestrator.py`)
- В `web_app.py` использовать новый orchestrator

---

#### **3. Изменение `Highlight` в contracts**

**Сломается:**
- Все места где используются удалённые поля:
  - `highlight.cefr_level`
  - `highlight.importance_score`
  - `highlight.why_interesting`
  - `highlight.pattern_template`

**Исправление:**
- Найти все использования (grep)
- Удалить или заменить

```bash
# Поиск использований
grep -r "cefr_level" .
grep -r "importance_score" .
grep -r "why_interesting" .
grep -r "pattern_template" .
```

**Вероятные файлы:**
- `static/components/HighlightCard.js` - удалить отображение этих полей
- `templates/*.html` - удалить из шаблонов
- `database.py` - проверить сохранение в БД

---

#### **4. Удаление `translate_text()` метода**

**Сломается:**
- Все места где вызывается `ai_client.translate_text()`

**Исправление:**
- Найти использования
- Удалить вызовы (агенты теперь сами возвращают переводы)

```bash
grep -r "translate_text" .
```

---

#### **5. Изменение поля `type` на Enum**

**Сломается:**
- JavaScript код который проверяет `highlight.type === "word"`

**Исправление:**
- В `to_dict()` метод возвращает `.value` (строку), поэтому JavaScript не сломается
- Но в Python коде нужно использовать `HighlightType.WORD` вместо `"word"`

---

### Полный чек-лист перед запуском

**Перед миграцией:**
- [ ] Сделан backup БД
- [ ] Создана git ветка
- [ ] Все изменения закоммичены

**После миграции:**
- [ ] Нет ошибок импорта при запуске Flask
- [ ] POST /analyze работает
- [ ] Агенты вызываются корректно
- [ ] Результаты валидные (есть highlights)
- [ ] Лемматизация применяется
- [ ] Дедупликация работает
- [ ] Dictionary meanings добавляются (только для слов)
- [ ] HighlightCard отображается корректно
- [ ] Нет использований удалённых полей
- [ ] Логи чистые (нет ошибок)

---

## 🧪 Тестирование

### Юнит-тесты

**Создать:** `/tests/test_analysis_orchestrator.py`

```python
import pytest
import asyncio
from core.analysis_orchestrator import AnalysisOrchestrator
from contracts.analysis_contracts import AnalysisRequest, HighlightType

@pytest.mark.asyncio
async def test_analyze_simple_text():
    """Тест простого текста"""
    orchestrator = AnalysisOrchestrator()
    request = AnalysisRequest(
        text="This is a sophisticated approach to solving complex problems.",
        page_id="main"
    )

    result = await orchestrator.analyze_text(request)

    assert result.success == True
    assert len(result.highlights) > 0
    assert any(h.highlight == "sophisticated" for h in result.highlights)

@pytest.mark.asyncio
async def test_type_assignment():
    """Тест что type корректно определяется по агенту"""
    orchestrator = AnalysisOrchestrator()
    request = AnalysisRequest(
        text="This is a sophisticated approach. Let me break down this concept.",
        page_id="main"
    )

    result = await orchestrator.analyze_text(request)

    words = [h for h in result.highlights if h.type == HighlightType.WORD]
    expressions = [h for h in result.highlights if h.type == HighlightType.EXPRESSION]

    assert len(words) > 0
    assert len(expressions) > 0

@pytest.mark.asyncio
async def test_dictionary_meanings_only_for_words():
    """Тест что dictionary_meanings добавляются только для слов"""
    orchestrator = AnalysisOrchestrator()
    request = AnalysisRequest(
        text="This is sophisticated. Break down the concept.",
        page_id="main"
    )

    result = await orchestrator.analyze_text(request)

    for h in result.highlights:
        if h.type == HighlightType.WORD:
            # Слова должны иметь dictionary_meanings (может быть пустой список)
            assert isinstance(h.dictionary_meanings, list)
        elif h.type == HighlightType.EXPRESSION:
            # Фразы должны иметь пустой список
            assert h.dictionary_meanings == []

@pytest.mark.asyncio
async def test_deduplication():
    """Тест дедупликации (если оба агента вернут одно и то же)"""
    # Сложный тест - нужен мок агентов
    pass
```

### Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_full_workflow():
    """Полный workflow от текста до результата"""
    orchestrator = AnalysisOrchestrator()

    text = """
    This is a sophisticated approach to solving complex problems.
    The compelling argument made by the researcher was very convincing.
    Let me break down this concept for you.
    """

    request = AnalysisRequest(text=text, page_id="main")
    result = await orchestrator.analyze_text(request)

    # Проверки
    assert result.success == True
    assert len(result.highlights) >= 3  # Минимум 3 хайлайта
    assert result.stats['total_words'] > 20
    assert result.performance['duration_seconds'] < 60  # Не больше 1 минуты

    # Проверяем структуру хайлайтов
    for h in result.highlights:
        assert h.highlight
        assert h.context
        assert h.highlight_translation
        assert h.type in [HighlightType.WORD, HighlightType.EXPRESSION]
```

### Ручное тестирование

**Тест-кейсы:**

1. **Короткий текст (5-10 слов)**
```
Текст: "This is a sophisticated approach."
Ожидаем: 1-2 хайлайта (sophisticated, approach?)
```

2. **Средний текст (50-100 слов)**
```
Текст: Абзац из статьи
Ожидаем: 5-10 хайлайтов, микс слов и фраз
```

3. **Длинный текст (500+ слов)**
```
Текст: Целая статья
Ожидаем: 30-50 хайлайтов, работает быстро (< 60 сек)
```

4. **Текст с фразовыми глаголами**
```
Текст: "Let me break down this concept and figure out the solution."
Ожидаем: "break down", "figure out" как EXPRESSION
```

5. **Текст только с простыми словами**
```
Текст: "This is a good day. I am happy."
Ожидаем: 0-1 хайлайтов (всё слишком простое)
```

---

## 🎯 Критерии успеха

### Миграция успешна, если:

✅ **Код:**
- Удалено ~35KB кода
- Удалены каталоги `agents/` и `core/prompts/`
- Создан `analysis_orchestrator.py`
- Обновлён `yandex_ai_client.py`
- Упрощён `Highlight` (4 поля удалены)

✅ **Функционал:**
- POST /analyze работает корректно
- Агенты Yandex AI Studio вызываются
- Результаты валидные и полные
- Лемматизация работает
- Дедупликация работает
- Dictionary meanings добавляются

✅ **Производительность:**
- Анализ текста < 60 секунд
- Нет memory leaks
- Нет лишних запросов к API

✅ **Качество:**
- Нет ошибок в логах
- Все тесты проходят
- Frontend отображает результаты корректно
- Код читаемый и поддерживаемый

---

## 📝 Следующие шаги (после миграции)

### Фаза 2: Улучшения

1. **YouTube Extractor** - реализовать с нуля правильный подход
2. **Кэширование** - кэшировать результаты агентов (Redis?)
3. **Батчинг** - отправлять несколько текстов в один запрос к агенту
4. **Мониторинг** - логировать latency, стоимость, ошибки
5. **Fallback** - запасные агенты если основной не работает

### Фаза 3: Оптимизация

1. **Параллелизм** - улучшить параллельность запросов
2. **Streaming** - стриминг ответов от агентов (если поддерживается)
3. **Retry logic** - повторные попытки при ошибках
4. **Rate limiting** - лимиты на количество запросов

---

## 📞 Контакты и ресурсы

**Yandex AI Studio:**
- URL: https://ai.yandex.cloud/studio
- Документация: https://yandex.cloud/docs/foundation-models/

**Агенты:**
- Agent #1: `fvt3bjtu1ehmg0v8tss3` (слова)
- Agent #2: `fvt6j0ev2cgf1q2itfr6` (фразы)
- Agent #3: `fvtludf1115lb39bei78` (тесты)

**Модели:**
- qwen3-235b-a22b-fp8 (для анализа)
- gpt-oss-120b (для тестов)

---

**Дата создания:** 11 декабря 2024
**Автор:** Claude Code + Andrew Kondakov
**Статус:** Готов к реализации 🚀
