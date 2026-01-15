# Система тренировки слов — План реализации

**Обновлено:** 15 января 2025
**Статус:** ✅ Готово к тестированию

---

## Текущее состояние

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| YDB схема (таблицы) | ✅ Готово | `user_training_state`, `tests`, `word_test_statistics` |
| `generate_test_options()` | ✅ Готово | `core/yandex_ai_client.py:404` |
| `TrainingService` | ✅ YDB | Мигрирован на YDB |
| `TestManager` | ✅ YDB | Мигрирован на YDB |
| API эндпоинты | ✅ Готово | `/api/training/start`, `/api/training/answer` |
| Telegram бот | ✅ Готово | `telegram_bot.py` |
| Методы в `database.py` | ✅ Готово | Все методы для тренировки добавлены |

---

## Архитектура

```
Пользователь (Web/Telegram)
        │
        ▼
┌─────────────────────────┐
│  API / Telegram Bot     │
│  - /api/training/start  │
│  - /api/training/answer │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐      ┌─────────────────────┐
│   TrainingService       │      │   TestManager       │
│   - select_words(8)     │      │   - create_tests()  │
│   - 8-шаговый алгоритм  │      │   - submit_answer() │
└───────────┬─────────────┘      └──────────┬──────────┘
            │                               │
            ▼                               ▼
┌─────────────────────────────────────────────────────┐
│                    database.py (YDB)                │
│  - get_user_training_state()                        │
│  - update_training_position()                       │
│  - insert_test() / get_test() / delete_test()       │
│  - update_word_rating() / update_word_statistics()  │
└─────────────────────────────────────────────────────┘
```

---

## 8-шаговый алгоритм отбора слов

При запросе N слов система циклически проходит по шагам:

| Шаг | Описание | SQL условие |
|-----|----------|-------------|
| 1 | Новое слово, добавленное последним | `status='new' ORDER BY added_at DESC` |
| 2 | Learning по давности повтора | `status='learning' ORDER BY last_reviewed_at ASC` |
| 3 | Новое слово, добавленное давнее всего | `status='new' ORDER BY added_at ASC` |
| 4 | Learning с макс. рейтингом (рандомно) | `status='learning' AND rating=MAX ORDER BY RANDOM()` |
| 5 | Слово, обнулившее рейтинг последним | `status='learning' AND rating=0 ORDER BY last_rating_change DESC` |
| 6 | = Шаг 4 (дубликат для частого повтора) | — |
| 7 | = Шаг 3 (дубликат для разогрева) | — |
| 8 | Рандомное выученное | `status='learned' ORDER BY RANDOM()` |

Позиция сохраняется в `user_training_state.last_selection_position`.

---

## Система рейтинга

**Шкала:** 0–10

| Событие | Действие |
|---------|----------|
| ✅ Правильный ответ | `rating += 1` |
| ❌ Неправильный ответ | `rating = 0` |
| `rating >= 10` | Статус → `learned` |
| Ошибка в `learned` | Статус → `learning` |

**Переходы статусов:**
```
new ──(первый тест)──▶ learning ──(rating≥10)──▶ learned
                            ▲                        │
                            └──(неправильный ответ)──┘
```

---

## План реализации

### Этап 1: Методы YDB в database.py ✅

Добавлены методы:
- `get_user_training_state()`, `update_training_position()`
- `insert_test()`, `get_test()`, `delete_test()`, `get_pending_tests()`
- `update_word_rating()`, `update_word_statistics()`, `get_word_by_id()`
- `get_words_by_training_step()` — 8-шаговый алгоритм
- `get_translation_for_word()`, `get_random_translations()`

### Этап 2: Миграция TrainingService ✅

- Удалён `sqlite3`, используются методы `self.db.*`
- Используется `Random()` вместо `RANDOM()`

### Этап 3: Миграция TestManager ✅

- Удалён `sqlite3`, используются методы `self.db.*`
- Fallback через `get_random_translations()`

### Этап 4: Тестирование

- [ ] Проверить отбор 8 слов по алгоритму
- [ ] Проверить создание тестов через AI
- [ ] Проверить submit_answer и обновление рейтинга
- [ ] Проверить переходы статусов (new→learning→learned)
- [ ] Тест через Telegram бот
- [ ] Тест через веб-интерфейс

---

## YDB схема (уже создана)

```sql
-- Состояние тренировки
CREATE TABLE user_training_state (
    user_id Uint64,
    last_selection_position Uint32,
    last_training_at Utf8,
    PRIMARY KEY (user_id)
)

-- Тесты
CREATE TABLE tests (
    id Uint64,
    user_id Uint64,
    word_id Uint64,
    word Utf8,
    correct_translation Utf8,
    wrong_option_1 Utf8,
    wrong_option_2 Utf8,
    wrong_option_3 Utf8,
    created_at Utf8,
    PRIMARY KEY (id),
    INDEX idx_user_id GLOBAL ON (user_id)
)

-- Статистика
CREATE TABLE word_test_statistics (
    id Uint64,
    user_id Uint64,
    word_id Uint64,
    total_tests Uint32,
    correct_answers Uint32,
    wrong_answers Uint32,
    last_test_at Utf8,
    last_result Bool,
    PRIMARY KEY (id),
    INDEX idx_user_word GLOBAL ON (user_id, word_id)
)

-- Поля в dictionary_words (уже есть)
rating Uint32,
last_rating_change Utf8
```

---

## API эндпоинты

### POST /api/training/start
Запуск тренировки: отбор 8 слов → генерация тестов → возврат test_ids

**Response:**
```json
{
  "success": true,
  "test_ids": [1, 2, 3, 4, 5, 6, 7, 8],
  "words_count": 8
}
```

### POST /api/training/answer
Отправка ответа на тест

**Request:**
```json
{
  "test_id": 123,
  "answer": "утончённый"
}
```

**Response:**
```json
{
  "is_correct": true,
  "correct_translation": "утончённый",
  "new_rating": 5,
  "new_status": "learning"
}
```

---

## Генерация тестов (Yandex AI)

**Agent ID:** `fvtludf1115lb39bei78`
**Метод:** `YandexAIClient.generate_test_options()`

**Input:**
```json
{
  "words": [
    {"word": "sophisticated", "correct_translation": "утончённый"}
  ]
}
```

**Output:**
```json
{
  "tests": [
    {
      "word": "sophisticated",
      "correct_translation": "утончённый",
      "wrong_options": ["сложный", "изощренный", "продвинутый"]
    }
  ]
}
```

**Fallback:** Если AI недоступен — случайные переводы из словаря пользователя.

---

## Файлы

| Файл | Назначение |
|------|------------|
| `database.py` | YDB методы (нужно добавить) |
| `core/training_service.py` | 8-шаговый алгоритм отбора |
| `core/test_manager.py` | Создание/проверка тестов |
| `core/yandex_ai_client.py` | Генерация wrong_options через AI |
| `telegram_bot.py` | Telegram интерфейс |
| `web_app.py` | API эндпоинты |
| `create_ydb_schema.py` | Создание таблиц YDB |
