# 🔧 Troubleshooting Guide - Wordoorio

Документация по решению типичных проблем в Wordoorio.

---

## 📋 Содержание

1. [IAM Token Expiration](#iam-token-expiration)
2. [Dictionary & Highlights Issues](#dictionary--highlights-issues)
3. [Header Missing](#header-missing)
4. [ReferenceError: Storage not defined](#referenceerror-storage-not-defined)

---

## IAM Token Expiration

### Проблема
Сайт возвращает ошибку "Ошибка соединения с сервером" при анализе текста. Запросы к `/analyze` таймаутят.

### Симптомы
```bash
curl -X POST https://wordoorio.ru/analyze -d '{"text":"valid text"}' --max-time 30
# Exit code 28 (timeout)
```

### Причина
Код проверял `YANDEX_IAM_TOKEN` из переменных окружения **ДО** Metadata Service. Если в `.env` был старый токен (истекший), он использовался вместо свежего из Metadata Service.

### Решение
**Исправлено в:** `core/yandex_ai_client.py:181-212`

Инвертирован приоритет проверки токенов:

**БЫЛО (неправильно):**
```python
def _get_iam_token(self) -> str:
    # Сначала проверяем переменную окружения
    env_token = os.getenv('YANDEX_IAM_TOKEN', '')
    if env_token:
        return env_token

    # Metadata Service как fallback
    try:
        # ...
```

**СТАЛО (правильно):**
```python
def _get_iam_token(self) -> str:
    # СНАЧАЛА Metadata Service (продакшн, всегда свежий)
    try:
        metadata_url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
        headers = {'Metadata-Flavor': 'Google'}
        response = requests.get(metadata_url, headers=headers, timeout=2)
        if response.status_code == 200:
            token_data = response.json()
            iam_token = token_data.get('access_token', '')
            print(f"✅ IAM токен получен через Metadata Service", flush=True)
            return iam_token
    except Exception as e:
        pass

    # FALLBACK: environment variable (локальная разработка)
    env_token = os.getenv('YANDEX_IAM_TOKEN', '')
    if env_token:
        print(f"⚠️ Используется IAM токен из .env (истекает через 12 часов!)", flush=True)
        return env_token
```

### Проверка
```bash
# Тест с валидным текстом
curl -X POST https://wordoorio.ru/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"The internet has revolutionized the way we communicate."}'

# Должен вернуть JSON с success: true
```

### Дополнительные действия
1. Закомментирован `YANDEX_IAM_TOKEN` в `.env`:
```env
# ⚠️ ВНИМАНИЕ: В продакшн токен получается автоматически через Metadata Service!
# Раскомментируйте ТОЛЬКО для локальной разработки (токен истекает через 12 часов)
#YANDEX_IAM_TOKEN=your_token_here
```

2. Обновлена документация в README.md с объяснением разницы между локальной разработкой и продакшн.

**Коммит:** `30b319d` - Инверсия приоритета IAM токенов

---

## Dictionary & Highlights Issues

### Проблема 1: Слова не попадают в словарь
Пользователь нажимает "+" на карточке слова, слово сохраняется в highlights, но не появляется на странице `/dictionary`.

### Причина
Словарь и highlights были разделены логически, но словарь требовал авторизацию (`/api/dictionary/add` возвращал 401). Пользователь ожидал, что они работают вместе.

### Решение
**Исправлено в:**
- `templates/index.html:277-308`
- `templates/dictionary.html:311-335`

Объединена логика: словарь и highlights теперь работают из одного источника - `localStorage`.

**Ключевые изменения:**

1. **Index.html** - изменено уведомление при сохранении:
```javascript
// БЫЛО
showNotification('Добавлено в словарь ✓');

// СТАЛО
showNotification('✓ Сохранено');
```

2. **Dictionary.html** - загрузка из localStorage:
```javascript
// Загружаем слова из localStorage
const storage = new HighlightsStorage();
const savedData = storage._getAllSaved();

for (const sessionId in savedData) {
    const highlights = savedData[sessionId];
    highlights.forEach((h) => {
        const word = convertHighlightToWord(h);
        localWords.push(word);
    });
}
```

### Проблема 2: Неправильное поле для перевода
Переводы не загружались из localStorage в словарь.

### Причина
Функция `convertHighlightToWord` использовала неправильное поле: `highlight.translation` вместо `highlight.highlight_translation`.

### Решение
**Исправлено в:** `templates/dictionary.html:363`

```javascript
// БЫЛО
translations: [highlight.translation || 'No translation']

// СТАЛО
translations: [highlight.highlight_translation || highlight.translation || 'No translation']
```

**Коммит:** `e503bf2` - Local-first highlights/dictionary

---

## Header Missing

### Проблема
На странице `/my-highlights` не отображался header (логотип + навигация).

### Симптомы
- Header рендерится как пустой div
- Навигация отсутствует
- Telegram login widget не загружается

### Причина
Функция `initUnifiedHeader()` асинхронная (`async`), но вызывалась без `await`. Код продолжал выполнение до завершения инициализации header.

### Решение
**Исправлено в:** `templates/my-highlights.html:15-28`

```javascript
// БЫЛО
document.addEventListener('DOMContentLoaded', function() {
    // ...
    initUnifiedHeader('header-container');  // БЕЗ await
    loadSavedHighlights();
});

// СТАЛО
document.addEventListener('DOMContentLoaded', async function() {  // async
    // ...
    await initUnifiedHeader('header-container');  // С await
    loadSavedHighlights();
});
```

**Коммит:** `e503bf2` - Local-first highlights/dictionary

---

## ReferenceError: Storage not defined

### Проблема
При открытии страницы `/dictionary` в консоли браузера появляется ошибка:
```
Uncaught ReferenceError: HighlightsStorage is not defined
```

### Симптомы
- Словарь не загружает слова из localStorage
- JavaScript ошибка в консоли
- Пустая страница словаря

### Причина
Файл `static/js/HighlightsStorage.js` не был подключен в `<head>` страницы `templates/dictionary.html`. Код пытался использовать класс `HighlightsStorage`, который не был загружен.

### Решение
**Исправлено в:** `templates/dictionary.html:10-15`

```html
<!-- БЫЛО -->
<script src="/static/js/Auth.js"></script>
<script src="/static/components/Header.js"></script>
<script src="/static/components/DictionaryWordRow.js"></script>
<script src="/static/js/DictionaryAPI.js"></script>

<!-- СТАЛО -->
<script src="/static/js/Auth.js"></script>
<script src="/static/components/Header.js"></script>
<script src="/static/components/DictionaryWordRow.js"></script>
<script src="/static/js/HighlightsStorage.js"></script>  <!-- ДОБАВЛЕНО -->
<script src="/static/js/DictionaryAPI.js"></script>
```

### Проверка
1. Открыть https://wordoorio.ru/dictionary
2. Проверить консоль браузера - ошибок нет
3. Проверить localStorage - слова загружаются корректно

**Коммит:** `5eb3ec1` - Add missing HighlightsStorage.js to dictionary

---

## Общие рекомендации по диагностике

### 1. Проверка логов продакшн
```bash
~/yandex-cloud/bin/yc logging read --folder-id=b1gcdpfvt5vkfn3o9nm1 --limit 100
```

### 2. Проверка токенов
```bash
# Проверить получение токена через Metadata Service
curl -H "Metadata-Flavor: Google" \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token
```

### 3. Проверка localStorage
Откройте консоль браузера:
```javascript
// Проверить все сохраненные данные
const storage = new HighlightsStorage();
console.log(storage._getAllSaved());

// Проверить конкретную сессию
console.log(storage.getSavedHighlights('session_id_here'));
```

### 4. Проверка GitHub Actions
https://github.com/YOUR_USERNAME/wordoorio/actions

Проверить логи последнего деплоя на наличие ошибок.

---

## История изменений

| Дата | Проблема | Решение | Коммит |
|------|----------|---------|--------|
| 2025-12-11 | IAM Token Expiration | Инверсия приоритета токенов | `30b319d` |
| 2025-12-11 | Dictionary не загружается | Объединение с highlights | `e503bf2` |
| 2025-12-11 | Неправильное поле перевода | Использование `highlight_translation` | `1397e29` |
| 2025-12-11 | Header отсутствует | Добавлен `await` для `initUnifiedHeader` | `e503bf2` |
| 2025-12-11 | HighlightsStorage not defined | Добавлен скрипт в dictionary.html | `5eb3ec1` |

---

**Последнее обновление:** 2025-12-11
**Актуальная архитектура:** Yandex Cloud Serverless Container
**Основная документация:** См. `SERVERLESS_DEPLOYMENT.md`
