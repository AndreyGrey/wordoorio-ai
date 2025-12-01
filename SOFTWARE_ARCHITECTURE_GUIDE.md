# 🏗️ АРХИТЕКТУРА ПРОГРАММНОГО ОБЕСПЕЧЕНИЯ

**Руководство для разработчиков на примере Wordoorio AI**

---

## 🎯 ЧТО ТАКОЕ АРХИТЕКТУРА?

**Архитектура** — это способ организации кода так, чтобы:
- ✅ Код было легко изменять
- ✅ Разные люди могли работать параллельно
- ✅ Ошибки не ломали всю систему
- ✅ Новые функции добавлялись быстро

### Плохая архитектура (наша текущая):
```
web_app.py (1000 строк)
├── HTML шаблоны
├── AI логика с промптами  
├── База данных
├── API endpoints
└── Анимации в каждом шаблоне
```
**Проблемы:** 
- Промпты захардкожены в коде
- Анимации дублируются
- Создать новую страницу = переписать все

### Хорошая архитектура (цель):
```
📁 contracts/              # Форматы данных
📁 core/prompts/versions/   # Версионирование промптов
📁 interface/components/    # Переиспользуемые UI компоненты  
📁 interface/pages/         # Конфигурации страниц
📁 storage/                 # База данных
```
**Преимущества:** 
- Новый промпт = новый файл
- Новая страница = новая конфигурация 
- Одна анимация для всех

---

## 🧩 ОСНОВНЫЕ ПРИНЦИПЫ

### 1. **РАЗДЕЛЕНИЕ ОТВЕТСТВЕННОСТИ**
**Принцип:** каждый файл отвечает только за одну вещь.

❌ **Плохо:**
```python
# web_app.py - делает ВСЕ
def analyze():
    # Получает данные
    # Обрабатывает AI
    # Сохраняет в БД  
    # Возвращает HTML
```

✅ **Хорошо:**
```python
# ai_service.py - только AI
def analyze_text(text): ...

# database_service.py - только БД  
def save_analysis(data): ...

# web_controller.py - только HTTP
def handle_request(): ...
```

### 2. **КОНТРАКТЫ (ИНТЕРФЕЙСЫ)**
**Принцип:** договариваемся о формате данных заранее.

```python
# contracts.py
@dataclass
class AnalysisResult:
    success: bool
    highlights: List[Dict]
    error: str = None
```

**Теперь все знают:** AI должен вернуть `AnalysisResult`, веб получит `AnalysisResult`.

### 3. **СЛОИСТАЯ АРХИТЕКТУРА**
```
┌─────────────────┐  ← Пользователь видит
│   PRESENTATION  │    (веб-страницы, API)
├─────────────────┤  
│    BUSINESS     │  ← Логика приложения  
│     LOGIC       │    (AI анализ, правила)
├─────────────────┤
│   DATA ACCESS   │  ← Хранение данных
│     LAYER       │    (база, файлы)
└─────────────────┘
```

**Правило:** верхний слой может обращаться к нижнему, но НЕ наоборот.

---

## 🔗 ПАТТЕРНЫ ПРОЕКТИРОВАНИЯ

### 1. **STRATEGY PATTERN + VERSIONING**
Разные версии промптов как стратегии.

```python
class PromptStrategy:
    def analyze(self, text): pass

class BasicPromptV1(PromptStrategy):
    def analyze(self, text):
        # Оригинальный промпт
        return single_prompt_analysis(text)

class DualPromptV2(PromptStrategy):  
    def analyze(self, text):
        # Experimental dual-prompt
        return dual_prompt_analysis(text)

# Использование
prompt = PromptManager.get_prompt("v2_dual")
result = prompt.analyze(text)
```

### 2. **COMPONENT LIBRARY**
Переиспользуемые UI компоненты.

```python
class LoadingAnimation:
    def show(self, user_text):
        # Единая анимация для всех страниц
        words = extract_words(user_text)
        animate_with_words(words)
    
class ResultsFormatter:
    def format(self, highlights, config):
        # Форматирование по конфигурации страницы
        if config.show_importance_score:
            add_scores(highlights)
```

### 3. **CONFIGURATION-DRIVEN UI**
Интерфейс управляется конфигурацией.

```python
@dataclass
class PageConfig:
    prompt_version: str = "v1_basic"
    ui_features: Dict[str, bool] = field(default_factory=dict)
    timeout_seconds: int = 60

# Новая страница = новая конфигурация
experimental_page = PageConfig(
    prompt_version="v2_dual",
    ui_features={"show_word_tabs": True},
    timeout_seconds=180
)
```

### 4. **REGISTRY PATTERN**
Центральное управление компонентами.

```python
class PromptRegistry:
    def register(self, version_id, strategy):
        self.strategies[version_id] = strategy
        
    def get(self, version_id):
        return self.strategies[version_id]

# Автоматическая регистрация
@register_prompt("v3_enhanced")
class EnhancedPromptV3(PromptStrategy):
    pass
```

---

## 🚀 РЕФАКТОРИНГ WORDOORIO

### Текущая структура:
```
wordoorio/
├── web_app.py          # 🔴 Все вместе
├── agents/agent_2.py   # 🔴 AI + HTTP  
├── core/ai_client.py   # 🔴 AI + база
└── database.py         # 🟢 Только БД
```

### Новая структура:
```
wordoorio/
├── 📁 contracts/
│   └── analysis_contracts.py          # Общие интерфейсы
├── 📁 core/                           # Бизнес-логика  
│   ├── prompts/                       # 🔄 ВЕРСИОНИРОВАНИЕ ПРОМПТОВ
│   │   ├── prompt_manager.py          # Управление версиями
│   │   ├── versions/
│   │   │   ├── v1_basic.py           # Базовая версия
│   │   │   ├── v2_dual.py            # Dual-prompt
│   │   │   └── v3_enhanced.py        # Будущая версия
│   │   └── prompt_registry.py        # Реестр промптов
│   ├── services/
│   │   ├── analysis_service.py
│   │   └── deduplication_service.py
│   └── agents/
├── 📁 interface/                     # Веб-интерфейс
│   ├── components/                   # 🎨 ПЕРЕИСПОЛЬЗУЕМЫЕ КОМПОНЕНТЫ
│   │   ├── loading_animation.js      # Единая анимация
│   │   ├── results_formatter.js      # Форматирование 
│   │   └── highlight_display.js      # Отображение хайлайтов
│   ├── pages/                        # 📱 КОНФИГУРАЦИИ СТРАНИЦ
│   │   ├── main_page_config.py       # config: prompt="v1_basic"
│   │   ├── experimental_config.py    # config: prompt="v2_dual"
│   │   └── future_config.py          # config: prompt="v3_enhanced"
│   ├── controllers/
│   │   └── universal_controller.py   # Один контроллер для всех
│   └── templates/
│       └── universal_page.html       # Один шаблон для всех
├── 📁 storage/                       # Данные
│   ├── repositories/
│   └── models/
└── 📁 main.py                       # Точка входа
```

### Пример кода:

**contracts/analysis_contracts.py:**
```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class AnalysisRequest:
    text: str
    page_id: str = "main"  # "main", "experimental", "future"

@dataclass  
class Highlight:
    word: str
    context: str
    translation: str
    importance_score: int = 85
    
@dataclass
class AnalysisResult:
    success: bool
    highlights: List[Highlight]
    stats: Dict[str, int]
    error: Optional[str] = None
    performance: Optional[Dict] = None  # Для experimental метрик

@dataclass
class PageConfig:
    id: str
    prompt_version: str         # "v1_basic", "v2_dual" 
    ui_features: Dict[str, bool]
    timeout_seconds: int
    max_text_length: int
```

**core/prompts/prompt_manager.py:**
```python
class PromptStrategy:
    def get_version_id(self): pass
    def analyze(self, text, ai_client): pass

class PromptManager:
    def __init__(self):
        self.strategies = {}
        self._register_all()
    
    def register(self, strategy):
        version_id = strategy.get_version_id()
        self.strategies[version_id] = strategy
    
    def get_prompt(self, version_id):
        return self.strategies[version_id]
        
    def list_versions(self):
        return list(self.strategies.keys())
```

**interface/pages/page_config_manager.py:**
```python
class PageConfigManager:
    def get_config(self, page_id: str) -> PageConfig:
        configs = {
            "main": PageConfig(
                id="main",
                prompt_version="v1_basic",
                ui_features={"show_scores": True},
                timeout_seconds=60,
                max_text_length=5000
            ),
            "experimental": PageConfig(
                id="experimental", 
                prompt_version="v2_dual",
                ui_features={"show_tabs": True, "show_metrics": True},
                timeout_seconds=180,
                max_text_length=3000
            )
        }
        return configs.get(page_id, configs["main"])
```

**interface/controllers/universal_controller.py:**
```python
class UniversalPageController:
    def __init__(self, page_manager, prompt_manager, service):
        self.pages = page_manager
        self.prompts = prompt_manager  
        self.service = service
    
    def render_page(self, page_id):
        config = self.pages.get_config(page_id)
        return render_template('universal.html', config=config)
        
    def analyze_text(self, page_id, text):
        config = self.pages.get_config(page_id)
        prompt = self.prompts.get_prompt(config.prompt_version)
        
        result = self.service.analyze_with_strategy(text, prompt)
        return self._format_response(result, config)
```

---

## ✅ ПРЕИМУЩЕСТВА НОВОЙ АРХИТЕКТУРЫ

### 1. **Параллельная разработка**
- Один разработчик работает над AI агентами
- Другой улучшает веб-интерфейс
- Третий оптимизирует базу данных

### 2. **Легкое тестирование**  
```python
# Мокаем AI для тестов интерфейса
mock_agent = MockAIAgent()
service = AnalysisService(mock_agent, ...)
```

### 3. **Простое масштабирование**
- Добавить нового AI провайдера → только новый агент
- Изменить UI → только interface слой  
- Новая база → только storage слой

### 4. **Версионирование промптов**
```python
# Новый промпт = новый файл в core/prompts/versions/
@register_prompt("v3_semantic")
class SemanticPromptV3(PromptStrategy):
    def get_version_id(self):
        return "v3_semantic"
        
    def analyze(self, text, ai_client):
        # Семантический анализ с группировкой
        return advanced_semantic_analysis(text)

# Новая страница = новая конфигурация
semantic_page = PageConfig(
    id="semantic",
    prompt_version="v3_semantic",  # Указываем версию промпта
    ui_features={"show_semantic_groups": True},
    timeout_seconds=120
)
```

### 5. **Переиспользуемые компоненты**
```javascript
// Одна анимация для всех страниц
const loader = new WordoorioLoader('#loading-container');
loader.show(userText);  // Автоматически извлекает слова из текста

// Форматирование по конфигурации страницы
const formatter = new ResultsFormatter();
formatter.display(highlights, pageConfig);
```

### 6. **Убираем дубликаты**
```python
class DeduplicationService:
    def remove_duplicates(self, highlights):
        seen = set()
        unique = []
        for h in highlights:
            key = (h.word.lower(), h.context.lower())
            if key not in seen:
                seen.add(key)
                unique.append(h)
        return unique
```

---

## 🛠️ ИНСТРУМЕНТЫ АРХИТЕКТОРА

### 1. **Диаграммы**
```
User → Controller → Service → Repository → Database
                 ↓
               AI Agent
```

### 2. **Документация контрактов**
- Что принимает каждый сервис
- Что возвращает  
- Какие ошибки может выдать

### 3. **Тесты архитектуры**
```python
def test_service_layer_independence():
    # Сервисы не должны знать о веб-запросах
    assert not imports_flask(analysis_service)
```

---

## 📚 ДАЛЬНЕЙШЕЕ ИЗУЧЕНИЕ

### 📖 **Книги:**
- "Clean Architecture" - Robert Martin
- "Building Microservices" - Sam Newman
- "Domain-Driven Design" - Eric Evans

### 🎯 **Концепции для изучения:**
- **SOLID принципы** - основы хорошего кода
- **Strategy Pattern + Versioning** - версионирование алгоритмов
- **Component-Based Architecture** - переиспользуемые компоненты
- **Configuration-Driven Development** - управление через конфиг
- **Registry Pattern** - центральное управление компонентами  
- **Microservices** - разбиение на мелкие сервисы
- **API Design** - проектирование интерфейсов

### 🛠️ **Практика:**
1. Создание версий промптов как отдельных файлов
2. Написание переиспользуемых UI компонентов
3. Конфигурирование страниц через декларативные объекты  
4. Рефакторинг от монолита к слоистой архитектуре
5. Создание диаграмм взаимодействия компонентов
6. Написание контрактов перед кодом

### 💡 **Ключевые термины:**
- **🔄 Prompt Versioning** - версионирование промптов
- **🎨 Component Library** - библиотека переиспользуемых компонентов  
- **📱 Configuration-Driven UI** - интерфейс, управляемый конфигурацией
- **🏗️ Strategy Pattern** - паттерн стратегия для разных алгоритмов
- **📋 Contract-First Design** - проектирование от контрактов
- **🎯 Universal Controller** - один контроллер для всех страниц

---

## 🎉 ЗАКЛЮЧЕНИЕ

**Хорошая архитектура** — это инвестиция в будущее проекта. Потратив время на правильную организацию кода сейчас, вы сэкономите недели разработки потом.

### 🎯 **Главные принципы современной архитектуры:**

1. **🔄 Версионирование как отдельные файлы** - новый промпт не ломает старый
2. **🎨 Переиспользуемые компоненты** - одна анимация для всех страниц  
3. **📱 Конфигурационное управление** - новая страница = новый конфиг
4. **📋 Контракты между слоями** - четкие интерфейсы взаимодействия

### 💡 **Формула успеха:**
```
Новая фича = Новый файл + Новый конфиг
НЕ = Изменение существующего кода
```

**Следующий шаг:** реализовать версионирование промптов и переиспользуемые компоненты для Wordoorio! 🚀

---

**📚 Этот гид поможет вам:**
- Понять современные подходы к архитектуре
- Научиться создавать масштабируемые системы
- Применить принципы на практике в реальном проекте
- Подготовиться к позиции Software Architect