# Wordoorio

**AI-powered анализ выразительной английской лексики** для изучающих язык. Система находит "живые", стильные слова и выражения, которые делают речь натуральной и выразительной.

## Возможности

- **Интеллектуальный анализ текста** через AI-агенты Yandex AI Studio
- **Определение сложных слов и фраз** с учетом контекста
- **Автоматические переводы** на русский язык
- **Словарные значения** из Yandex Dictionary API
- **Лемматизация** для удаления дубликатов
- **Персональный словарь** с прогрессом изучения
- **База данных**: YDB (Yandex Database) - serverless база данных

## Технологии

- **Backend**: Python 3.9+, Flask, asyncio
- **AI**: Yandex AI Studio (Qwen3-235B через REST API)
- **NLP**: spaCy (лемматизация)
- **Dictionary**: Yandex Dictionary API
- **Database**: YDB (serverless NoSQL/SQL)
- **Deploy**: Yandex Serverless Containers
- **Frontend**: Vanilla JS

## Быстрый старт

### 1. Установка

```bash
git clone <repo-url>
cd Wordoorio

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Настройка окружения

Создайте `.env`:

```bash
# Yandex Cloud
YANDEX_CLOUD_API_KEY=<api_key>
YANDEX_FOLDER_ID=<folder_id>

# Dictionary API
YANDEX_DICT_API_KEY=<dict_key>

# YDB
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/<folder_id>/<database_id>

# Telegram Bot (авторизация)
TELEGRAM_BOT_TOKEN=<bot_token>
TELEGRAM_BOT_USERNAME=<bot_username>
```

**Получение ключей:**
- Yandex Cloud API Key: Сервисный аккаунт с ролью `ai.languageModels.user`
- Dictionary API: https://yandex.ru/dev/dictionary/
- Telegram Bot: https://t.me/BotFather → /newbot
- YDB: Создайте serverless базу в Yandex Cloud Console, запустите `python create_ydb_schema.py`

### 3. Запуск

```bash
python web_app.py
# Откройте http://localhost:8081
```

## Архитектура

### AI-агенты (Yandex AI Studio)

Два специализированных агента на базе Qwen3-235B:

1. **Agent #1 (Words)** - `fvt3bjtulehmg0v8tss3` - анализирует отдельные слова
2. **Agent #2 (Phrases)** - `fvt6j0ev2cgf1q2itfr6` - анализирует выражения

**Подключение через REST API:**

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
```

См. полную реализацию: `core/yandex_ai_client.py`

### Поток обработки

```
User Text → AnalysisOrchestrator
           ↓
    ┌──────────┬──────────┐
    │ Agent #1 │ Agent #2 │ (параллельно)
    │  Words   │ Phrases  │
    └──────────┴──────────┘
           ↓
    Lemmatization (spaCy)
           ↓
    Dictionary API
           ↓
    Remove Duplicates
           ↓
    Highlights → Frontend
```

## YDB: Важные уроки

### Работа с типами параметров

**Проблема:** Ошибки `type mismatch` при передаче параметров в запросы.

**Решение:**

1. **Проверяйте реальную схему таблицы:**
   ```python
   # Endpoint для проверки схемы
   GET /api/test/describe-table
   ```

2. **Правило:** Тип в `DECLARE` должен **точно соответствовать** типу параметра:
   ```python
   # Если поле в таблице: lemma Utf8?
   # То в запросе:
   query = """
   DECLARE $lemma AS Utf8?;  # С вопросом!
   INSERT INTO table (lemma) VALUES ($lemma);
   """

   params = {
       '$lemma': ('test', ydb.OptionalType(ydb.PrimitiveType.Utf8))  # Optional!
   }
   ```

3. **Используйте QuerySessionPool** (не SessionPool):
   ```python
   # ✅ Правильно
   self.pool = ydb.QuerySessionPool(self.driver)
   result = self.pool.execute_with_retries(query, parameters=params)

   # ❌ Неправильно (баг в SDK 3.23.0)
   self.pool = ydb.SessionPool(self.driver)
   session.transaction().execute(query, parameters=params)
   ```

4. **Беззнаковые типы:**
   - ID поля → `Uint64` (не `Int64`)
   - Счетчики → `Uint32` (не `Int32`)

**Не тратьте токены на догадки** - спрашивайте у поддержки Yandex или проверяйте схему!

## Структура проекта

```
Wordoorio/
├── web_app.py                 # Flask сервер + API endpoints
├── create_ydb_schema.py       # Создание схемы YDB
├── requirements.txt
│
├── core/
│   ├── yandex_ai_client.py    # REST API клиент для AI
│   ├── analysis_orchestrator.py
│   ├── dictionary_manager.py  # YDB операции со словарем
│   └── training_service.py    # Система тренировок
│
├── contracts/
│   └── analysis_contracts.py  # Типы данных
│
├── utils/
│   └── lemmatizer.py          # spaCy лемматизация
│
├── static/
│   ├── components/
│   └── js/
│
└── templates/                 # HTML страницы
```

## API Endpoints

### Анализ текста
- `POST /api/analyze` - анализ текста с AI-агентами

### Словарь
- `POST /api/dictionary/add` - добавить слово
- `GET /api/dictionary/words` - получить все слова
- `GET /api/dictionary/word/<lemma>` - детали слова
- `DELETE /api/dictionary/word/<lemma>` - удалить слово
- `GET /api/dictionary/stats` - статистика

### Авторизация
- `POST /api/auth/login` - вход
- `POST /api/auth/logout` - выход
- `GET /api/auth/current` - текущий пользователь

### Тестовые endpoints (debug)
- `GET /api/test/add-word` - тест добавления слова
- `GET /api/test/describe-table` - схема таблицы YDB

## Развертывание

Автоматический деплой через GitHub Actions при push в `main`:

1. Сборка Docker образа
2. Загрузка в Yandex Container Registry
3. Деплой в Serverless Container

**GitHub Secrets:**
- `YANDEX_CLOUD_API_KEY`
- `YANDEX_DICT_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `YDB_ENDPOINT`
- `YDB_DATABASE`

**Сервисный аккаунт должен иметь роли:**
- `ai.languageModels.user`
- `ydb.editor`
- `container-registry.images.puller`

## Лицензия

MIT License
