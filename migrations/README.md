# Database Migrations

## 001: Add word_id to highlights table (2026-01-16)

### Проблема
Ранее в приложении была несистемная логика хранения данных:
- Клик на "+" сохранял данные И в `dictionary_words` И в `highlights` (дублирование)
- Удаление из словаря удаляло только `dictionary_words`, но не `highlights` (мусор)
- Удаление анализа удаляло highlights, но не слова из словаря

### Решение: Словарь как единый источник правды (Single Source of Truth)

**Новая архитектура:**
- `dictionary_words` — главная таблица со всеми словами
- `highlights` — только ссылки на слова через `word_id`
- При удалении слова → каскадное удаление всех его highlights
- При удалении анализа → удаляются только highlights, слова остаются

### Изменения в schema

**Старая структура `highlights`:**
```sql
CREATE TABLE highlights (
    id Uint64,
    analysis_id Uint64,
    highlight_word Utf8?,          -- ДУБЛИРОВАНИЕ
    context Utf8?,                 -- ДУБЛИРОВАНИЕ
    highlight_translation Utf8?,   -- ДУБЛИРОВАНИЕ
    dictionary_meanings Utf8?,     -- ДУБЛИРОВАНИЕ
    PRIMARY KEY (id)
)
```

**Новая структура `highlights`:**
```sql
CREATE TABLE highlights (
    id Uint64,
    analysis_id Uint64,
    word_id Uint64,      -- ССЫЛКА на dictionary_words.id
    position Uint32,     -- Порядковый номер в тексте
    PRIMARY KEY (id)
)
```

### Что делает миграция

1. **Создает новую таблицу** `highlights_new` с новой структурой
2. **Мигрирует данные**:
   - Для каждого старого highlight:
     - Находит или создает слово в `dictionary_words`
     - Создает новый highlight со ссылкой на `word_id`
3. **Заменяет таблицу**:
   - Удаляет старую `highlights`
   - Переименовывает `highlights_new` → `highlights`

### Изменения в коде

#### database.py
- `_find_or_create_word_for_highlight()` — новый метод для создания/поиска слова
- `_add_example_if_not_exists()` — добавляет пример к существующему слову
- `save_analysis()` — теперь создает слова в словаре перед созданием highlights
- `add_highlight_to_analysis()` — теперь принимает `user_id` и `session_id`
- `get_user_highlights()` — делает JOIN с `dictionary_words` для получения полных данных

#### dictionary_manager.py
- `delete_word()` — добавлено каскадное удаление всех highlights с этим `word_id`

#### web_app.py
- `/api/dictionary/add` — обновлен вызов `add_highlight_to_analysis()` с новыми параметрами

### Как запустить миграцию

```bash
python3 migrations/001_add_word_id_to_highlights.py
```

**Безопасность:**
- Миграция автоматически проверяет, не была ли она уже выполнена
- Если структура уже новая — миграция пропускается
- Все существующие данные сохраняются

### Результат

**До:**
- Дублирование данных между `dictionary_words` и `highlights`
- Несогласованность при удалении (мусор в одной из таблиц)
- Невозможно обновить перевод слова для всех highlights одновременно

**После:**
- Нет дублирования — единый источник правды в `dictionary_words`
- Удаление слова из словаря → автоматически удаляются все его highlights
- Удаление анализа → слова остаются в словаре (могут быть в других анализах)
- Обновление данных слова → автоматически отражается во всех highlights
