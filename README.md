# Wordoorio

**AI-powered анализ выразительной английской лексики** для изучающих язык. Система находит "живые", стильные слова и выражения, которые делают речь натуральной и выразительной.

## Возможности

- **Интеллектуальный анализ текста** через специализированных AI-агентов Yandex AI Studio
- **Определение сложных слов и фраз** с учетом контекста
- **Автоматические переводы** на русский язык
- **Словарные значения** из Yandex Dictionary API
- **Лемматизация** для удаления дубликатов (amplify/amplifying/amplified = одно слово)
- **Веб-интерфейс** для удобной работы
- **База данных**: YDB (Yandex Database) - serverless NoSQL/SQL база данных

## Архитектура

### Агентная система (Yandex AI Studio)

Система использует два специализированных AI-агента:

1. **Agent #1 (Words)** - `fvt3bjtulehmg0v8tss3`
   - Анализирует отдельные сложные слова
   - Модель: Qwen3-235B-A22B-FP8

2. **Agent #2 (Phrases)** - `fvt6j0ev2cgf1q2itfr6`
   - Анализирует устойчивые выражения и коллокации
   - Модель: Qwen3-235B-A22B-FP8

### Подключение агентов

⚠️ **Important:** Do NOT use `openai` or `yandex-cloud-ml-sdk` libraries (dependency conflicts).

Агенты вызываются через **прямой REST API**:

```python
import aiohttp

url = "https://rest-assistant.api.cloud.yandex.net/v1/responses"
headers = {
    "Authorization": f"Api-Key {api_key}",
    "x-folder-id": folder_id,
    "Content-Type": "application/json"
}
payload = {
    "prompt": {"id": agent_id},
    "input": user_input
}

async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload,
                           timeout=aiohttp.ClientTimeout(total=120)) as response:
        result = await response.json()
        text = result['output'][0]['content'][0]['text']
```

See full implementation: `core/yandex_ai_client.py:207-288`

**Важно**: Агенты должны быть настроены с JSON Schema для возврата структурированных данных:

```json
{
  "type": "object",
  "properties": {
    "highlights": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "highlight": {"type": "string"},
          "highlight_translation": {"type": "string"},
          "context": {"type": "string"}
        },
        "required": ["highlight", "highlight_translation", "context"]
      }
    }
  },
  "required": ["highlights"]
}
```

### Обработка результатов

```
User Text
    ↓
AnalysisOrchestrator
    ↓
┌─────────────┬─────────────┐
│  Agent #1   │  Agent #2   │  (параллельно)
│   Words     │   Phrases   │
└─────────────┴─────────────┘
    ↓
Lemmatization (spaCy)
    ↓
Dictionary API (async)
    ↓
Remove Duplicates
    ↓
Highlights → Frontend
```

## Технологии

- **Backend**: Python 3.9+, Flask, asyncio
- **AI**: Yandex AI Studio (Assistant API via REST)
- **HTTP Client**: aiohttp
- **NLP**: spaCy (лемматизация), pymorphy2
- **Dictionary**: Yandex Dictionary API
- **Database**: YDB (Yandex Database) - serverless NoSQL/SQL database
- **Deploy**: Yandex Serverless Containers (stateless)
- **Frontend**: Vanilla JS

## Установка и запуск

### 1. Клонирование и установка зависимостей

```bash
git clone <repo-url>
cd Wordoorio

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Загрузка модели spaCy для английского
python -m spacy download en_core_web_sm
```

### 2. Настройка окружения

Создайте файл `.env`:

```bash
# Yandex Cloud (обязательно)
YANDEX_CLOUD_API_KEY=<ваш_yandex_cloud_api_key>
YANDEX_FOLDER_ID=<ваш_folder_id>

# Yandex Dictionary API (обязательно)
YANDEX_DICT_API_KEY=<ваш_dict_api_ключ>

# YDB (Yandex Database) настройки (обязательно)
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/<ваш_folder_id>/<ваш_database_id>

# Telegram Bot для авторизации (обязательно)
TELEGRAM_BOT_TOKEN=<ваш_telegram_bot_token>
TELEGRAM_BOT_USERNAME=<ваш_bot_username>

# Приложение
DEBUG=true
```

**Получение токенов и настройка YDB:**

- **Yandex Cloud API Key**: Создайте API ключ для сервисного аккаунта с ролью `ai.languageModels.user`
- **Dictionary API**: https://yandex.ru/dev/dictionary/
- **Telegram Bot**: https://t.me/BotFather -> /newbot
- **YDB**:
  1. Создайте serverless YDB базу в Yandex Cloud Console
  2. Скопируйте `Эндпоинт` и `База данных` из настроек YDB
  3. Запустите схему: `python create_ydb_schema.py` (требуется IAM токен)

### 3. Запуск

```bash
# Локальная разработка
python web_app.py

# Открыть в браузере
open http://localhost:8081
```

## Структура проекта

```
Wordoorio/
├── web_app.py                 # Flask веб-сервер
├── database.py                # YDB (Yandex Database) операции
├── requirements.txt           # Зависимости Python
│
├── core/
│   ├── yandex_ai_client.py    # Клиент для Yandex AI (agents + dictionary)
│   └── analysis_orchestrator.py # Координатор анализа
│
├── contracts/
│   └── analysis_contracts.py   # Типы данных (AgentResponse, Highlight, etc.)
│
├── utils/
│   └── lemmatizer.py          # Лемматизация через spaCy
│
├── static/
│   ├── components/            # Компоненты UI
│   └── js/                    # JavaScript модули
│
└── tests/
    ├── test_basic_gpt.py      # Тест базовой модели
    ├── test_qwen_agent.py     # Тест агентов
    └── test_orchestrator.py   # Тест оркестратора
```

## Тестирование

```bash
# Базовая модель YandexGPT
python test_basic_gpt.py

# Агенты через Assistant API
python test_qwen_agent.py

# Оркестратор + лемматизация
python test_orchestrator.py
```

## Развертывание (Production)

Приложение развертывается в **Yandex Serverless Containers** через GitHub Actions.

### Требования:

1. **Сервисный аккаунт** с ролями:
   - `ai.languageModels.user` (для YandexGPT)
   - `ydb.editor` (для YDB)
   - `container-registry.images.puller` (для Container Registry)

2. **GitHub Secrets**:
   - `YANDEX_CLOUD_API_KEY` - API ключ для YandexGPT
   - `YANDEX_DICT_API_KEY` - ключ Yandex Dictionary API
   - `TELEGRAM_BOT_TOKEN` - токен Telegram бота
   - `YDB_ENDPOINT` - endpoint YDB базы
   - `YDB_DATABASE` - путь к YDB базе

3. **YDB база данных**:
   - Создайте serverless YDB в Yandex Cloud Console
   - Настройте права доступа для сервисного аккаунта
   - Запустите `create_ydb_schema.py` для создания таблиц

### Автоматический деплой:

При push в `main` ветку GitHub Actions:
1. Собирает Docker образ
2. Загружает в Container Registry
3. Деплоит новую ревизию Serverless Container
4. YDB credentials передаются через **MetadataUrlCredentials**

## Лицензия

MIT License

## Контакты

Wordoorio Team
