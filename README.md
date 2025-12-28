# Wordoorio

**AI-powered анализ выразительной английской лексики** для изучающих язык. Система находит "живые", стильные слова и выражения, которые делают речь натуральной и выразительной.

## Возможности

- **Интеллектуальный анализ текста** через специализированных AI-агентов Yandex AI Studio
- **Определение сложных слов и фраз** с учетом контекста
- **Автоматические переводы** на русский язык
- **Словарные значения** из Yandex Dictionary API
- **Лемматизация** для удаления дубликатов (amplify/amplifying/amplified = одно слово)
- **Веб-интерфейс** для удобной работы
- **База данных**: SQLite + Yandex Object Storage (персистентное хранение, см. [DATABASE_STORAGE.md](DATABASE_STORAGE.md))

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
- **Database**: SQLite + Yandex Object Storage (см. [DATABASE_STORAGE.md](DATABASE_STORAGE.md))
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
YANDEX_IAM_TOKEN=<ваш_iam_токен>
YANDEX_FOLDER_ID=<ваш_folder_id>

# Yandex Dictionary API (обязательно)
YANDEX_DICT_API_KEY=<ваш_dict_api_ключ>

# Приложение
DEBUG=true
```

**Получение токенов:**

- IAM токен (локальная разработка):
  ```bash
  ~/yandex-cloud/bin/yc iam create-token
  ```
  ⚠️ Токен действителен 12 часов!

- Dictionary API: https://yandex.ru/dev/dictionary/

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
├── database.py                # SQLite операции
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

В продакшене IAM токен получается автоматически через **Metadata Service** Yandex Cloud:

```python
# Код в yandex_ai_client.py автоматически определяет окружение:
if self._is_yandex_cloud_environment():
    # Получаем токен из Metadata Service
    self.iam_token = self._get_token_from_metadata()
else:
    # Используем токен из .env (локальная разработка)
    self.iam_token = os.getenv('YANDEX_IAM_TOKEN')
```

Для Yandex Cloud Container/Compute Instance:
1. Присвойте сервисному аккаунту роль `ai.languageModels.user`
2. Настройте переменные окружения (FOLDER_ID, DICT_API_KEY)
3. Токен будет обновляться автоматически

## Лицензия

MIT License

## Контакты

Wordoorio Team
