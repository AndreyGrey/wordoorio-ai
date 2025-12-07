# 🔗 INTEGRATION GUIDE - Интеграция новой архитектуры

## Что создано

### 1. Контракты (`contracts/analysis_contracts.py`)
Единые интерфейсы для всей системы:
- `Highlight` - стандартный формат хайлайта
- `AnalysisRequest` - запрос на анализ
- `AnalysisResult` - результат анализа
- `PromptStrategy` - интерфейс для версий промптов
- `DeduplicationService` - интерфейс для дедупликации

### 2. Версионирование промптов
**core/prompts/versions/**
- `v1_basic.py` - оригинальная версия (stable)
- `v2_dual.py` - экспериментальная dual-prompt версия

**core/prompts/prompt_manager.py**
- Центральный реестр всех версий промптов
- `get_prompt(version_id)` - получить стратегию
- `list_versions()` - список всех версий
- `get_stable_version()` - стабильная версия

### 3. Дедупликация (`core/services/deduplication_service.py`)
- Удаление точных дубликатов
- Морфологические варианты (walk/walking/walked)
- Семантически схожие слова (big/large/huge)
- Частичные перекрытия фраз

### 4. Универсальная анимация (`interface/components/loading_animation.js`)
- Единая анимация загрузки для всех страниц
- Извлекает слова из текста пользователя
- Настраиваемые интервалы и стили

### 5. Интеграционный сервис (`core/analysis_service.py`)
- Объединяет все компоненты
- Единый API для анализа
- Автоматическая дедупликация
- Маппинг page_id -> prompt_version

---

## Как мигрировать

### СТАРЫЙ КОД (web_app.py)

```python
# Два разных endpoint'а для разных версий

@app.route('/analyze', methods=['POST'])
def analyze_text():
    from agents.agent_2 import AIVocabularyAnalyzer
    analyzer = AIVocabularyAnalyzer()
    result = analyzer.analyze_text(text)
    # ...

@app.route('/experimental/analyze', methods=['POST'])
def experimental_analyze():
    from core.experimental_ai_client import ExperimentalYandexAIClient
    client = ExperimentalYandexAIClient()
    result = loop.run_until_complete(client.analyze_dual_highlights(text))
    # ...
```

### НОВЫЙ КОД (unified)

```python
from core.analysis_service import get_analysis_service
from contracts.analysis_contracts import AnalysisRequest
from core.yandex_ai_client import YandexAIClient
import asyncio

# Единый endpoint для всех версий
@app.route('/api/analyze', methods=['POST'])
def unified_analyze():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        page_id = data.get('page_id', 'main')  # "main" или "experimental"

        # Создаем запрос
        analysis_request = AnalysisRequest(
            text=text,
            page_id=page_id,
            user_session=session.get('session_id')
        )

        # Валидация
        error = analysis_request.validate()
        if error:
            return jsonify({'error': error})

        # Получаем сервис и AI клиент
        service = get_analysis_service()
        ai_client = YandexAIClient()

        # Анализируем (сервис сам выберет нужный промпт и применит дедупликацию)
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            service.analyze_text(analysis_request, ai_client)
        )

        # Возвращаем результат
        if result.success:
            return jsonify(result.to_json_dict())
        else:
            return jsonify({'error': result.error})

    except Exception as e:
        return jsonify({'error': f'Критическая ошибка: {str(e)}'})
```

---

## Преимущества новой архитектуры

### ✅ Единый endpoint
- Раньше: `/analyze` и `/experimental/analyze`
- Теперь: `/api/analyze?page_id=main` или `page_id=experimental`

### ✅ Параллельная разработка
- **AI логика**: Добавляешь новый файл `v3_advanced.py` в `core/prompts/versions/`
- **UI**: Создаешь новую страницу и просто указываешь `page_id -> prompt_version`
- Никак не зависят друг от друга!

### ✅ Простое добавление новой версии

**Шаг 1**: Создай новый промпт
```python
# core/prompts/versions/v3_advanced.py
class AdvancedPromptV3(PromptStrategy):
    def get_metadata(self):
        return PromptMetadata(
            id="v3_advanced",
            name="Advanced Version",
            description="Deep analysis with context",
            is_stable=False,
            performance_score=95.0,
            estimated_cost=1.2
        )

    async def analyze_text(self, text, ai_client):
        # твоя логика анализа
        pass
```

**Шаг 2**: Зарегистрируй страницу
```python
from core.analysis_service import get_analysis_service

service = get_analysis_service()
service.register_page('advanced', 'v3_advanced')
```

**Готово!** Теперь можно использовать:
```javascript
fetch('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({
        text: userText,
        page_id: 'advanced'  // Будет использовать v3_advanced
    })
})
```

### ✅ Автоматическая дедупликация
Все результаты автоматически проходят через деdup сервис - повторы исчезают сами.

### ✅ Единая анимация
```javascript
// В любой HTML странице
<script src="/interface/components/loading_animation.js"></script>
<script>
const animation = new WordoorioLoadingAnimation('#results-container');
animation.show(userText, "Анализирую текст...");

// Когда получен результат
animation.hide();
</script>
```

---

## Пример: Добавить новую страницу "Pro"

### 1. Создать промпт (если нужен новый)
```python
# core/prompts/versions/v3_pro.py
from contracts.analysis_contracts import PromptStrategy, PromptMetadata

class ProPromptV3(PromptStrategy):
    # ... реализация
```

### 2. Зарегистрировать в PromptManager
Автоматически подхватится при импорте! Просто импортируй в `prompt_manager.py`:
```python
from .versions.v3_pro import ProPromptV3
```

### 3. Добавить маппинг в AnalysisService
```python
# В core/analysis_service.py
self.page_to_prompt = {
    'main': 'v1_basic',
    'experimental': 'v2_dual',
    'pro': 'v3_pro'  # ← Добавили
}
```

### 4. Создать HTML страницу
```html
<!-- templates/pro.html -->
<script>
fetch('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({
        text: userText,
        page_id: 'pro'  // Использует v3_pro автоматически
    })
})
</script>
```

**Вот и всё!** Никаких изменений в остальном коде.

---

## Следующие шаги

### 1. Протестировать новую архитектуру
```bash
cd /Users/andrewkondakow/Documents/Projects/Wordoorio
python3 -c "
from core.analysis_service import get_analysis_service
service = get_analysis_service()
print('✅ AnalysisService работает')
print(f'📋 Доступные страницы: {service.get_available_pages()}')
"
```

### 2. Постепенная миграция
1. Оставь старые endpoint'ы как есть (работающий код не трогаем)
2. Добавь новый `/api/v2/analyze` с новой архитектурой
3. Протестируй параллельно
4. Когда убедишься что работает - переключи фронтенд

### 3. Добавить больше версий промптов
- `v3_context_aware` - с учетом контекста всего текста
- `v4_interactive` - интерактивный режим
- `v5_multi_language` - мультиязычная поддержка

---

## FAQ

**Q: Нужно ли менять существующий код?**
A: Нет! Новая архитектура работает параллельно. Можешь не трогать web_app.py.

**Q: Как дебажить новую систему?**
A: Все компоненты выводят подробные логи в stdout. Просто смотри консоль.

**Q: Что если хочу отключить дедупликацию?**
A: Пока автоматическая. Можно добавить параметр в PageConfig позже.

**Q: Можно ли использовать разные AI клиенты?**
A: Да! Просто передай другой клиент в `service.analyze_text(request, your_client)`

**Q: Как посмотреть все доступные версии промптов?**
```python
from core.prompts.prompt_manager import get_prompt_manager
manager = get_prompt_manager()
for version in manager.list_versions():
    print(f"{version.id}: {version.name} (score: {version.performance_score})")
```

---

## Структура новой архитектуры

```
Wordoorio/
├── contracts/
│   └── analysis_contracts.py       # 📋 Единые интерфейсы
├── core/
│   ├── analysis_service.py         # 🎯 Интеграционный слой
│   ├── prompts/
│   │   ├── prompt_manager.py       # 🗂️  Реестр версий
│   │   └── versions/
│   │       ├── v1_basic.py         # 📦 Базовая версия
│   │       ├── v2_dual.py          # 📦 Dual-prompt
│   │       └── v3_*.py             # 📦 Будущие версии
│   └── services/
│       └── deduplication_service.py # 🔍 Удаление дубликатов
├── interface/
│   ├── components/
│   │   └── loading_animation.js    # ⏳ Универсальная анимация
│   └── pages/
│       └── page_configs.py         # ⚙️  Конфигурации страниц
└── web_app.py                      # 🌐 Flask app (можно мигрировать)
```

---

**Готово!** Теперь можно работать над AI логикой и UI независимо 🚀
