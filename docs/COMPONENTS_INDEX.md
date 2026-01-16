# Components Index

Справочник всех frontend компонентов Wordoorio.

---

## UI Components

### Header.js v2.0
**Путь:** `static/components/Header.js`

Унифицированный header для всех страниц.

| Функция | Описание |
|---------|----------|
| `createUnifiedHeader(user)` | Создание HTML |
| `getUnifiedHeaderStyles()` | CSS стили |
| `initUnifiedHeader(containerId)` | Полная инициализация |
| `toggleUserMenu()` | Toggle dropdown |
| `handleLogout()` | Выход из системы |
| `showNotification(msg, type)` | Уведомление |

**Использование:**
```html
<div id="header-container"></div>
<script src="/static/components/Header.js"></script>
<script>
    initUnifiedHeader('header-container');
</script>
```

---

### WordCardV2.js
**Путь:** `static/components/WordCardV2.js`

Карточка слова с рейтингом и прогрессом.

| Функция | Описание |
|---------|----------|
| `createWordCard(word, options)` | Создание HTML карточки |
| `getWordCardStyles()` | CSS стили |
| `initWordCardStyles()` | Инъекция стилей |
| `renderWordList(words, containerId, options)` | Рендер списка |
| `getRatingLevel(rating)` | Уровень: low/medium/high |
| `getStatusInfo(status)` | Текст и класс статуса |

**Options:**
```javascript
{
    showDelete: true,   // Кнопка удаления
    showRating: true,   // Рейтинг 0-10
    showStatus: true,   // Бейдж статуса
    onDelete: fn,       // Callback удаления
    onClick: fn         // Callback клика
}
```

---

### CustomDropdown.js
**Путь:** `static/components/CustomDropdown.js`

Переиспользуемый dropdown.

| Функция | Описание |
|---------|----------|
| `createCustomDropdown(config)` | Создание HTML |
| `initDropdown(id, options)` | Инициализация |
| `initAllDropdowns(options)` | Инициализация всех |
| `getCustomDropdownStyles()` | CSS стили |
| `closeAllDropdowns()` | Закрыть все |

**Config:**
```javascript
{
    id: 'myDropdown',
    options: [
        { value: 'a', label: 'Option A' },
        { value: 'b', label: 'Option B' }
    ],
    defaultValue: 'a',
    placeholder: 'Выбрать'
}
```

**Instance methods:**
```javascript
const dd = initDropdown('myDropdown', { onChange: fn });
dd.getValue();       // Текущее значение
dd.setValue('b');    // Установить значение
dd.open();           // Открыть
dd.close();          // Закрыть
```

---

### HighlightCard.js
**Путь:** `static/components/HighlightCard.js`

Карточка хайлайта для страницы анализа.

| Функция | Описание |
|---------|----------|
| `createHighlightCard(highlight, index, color, showActions)` | Создание HTML |
| `getHighlightCardStyles()` | CSS стили |

**Параметры:**
- `highlight` - объект хайлайта
- `index` - индекс в списке
- `color` - 'orange' (слова) или 'blue' (фразы)
- `showActions` - показывать кнопки +/-

---

### AnalysisForm.js
**Путь:** `static/components/AnalysisForm.js`

Форма для ввода текста на анализ.

| Функция | Описание |
|---------|----------|
| `initAnalysisForm(containerId, options)` | Инициализация |

**Options:**
```javascript
{
    placeholder: 'Enter text...',
    subtitle: 'AI-powered analysis',
    buttonText: 'Analyze'
}
```

---

## JS Modules

### DictionaryAPI.js
**Путь:** `static/js/DictionaryAPI.js`

API клиент для работы со словарём.

| Функция | Описание |
|---------|----------|
| `addToDictionary(highlight)` | Добавить слово |
| `getAllWords(filters)` | Получить все слова |
| `getWord(lemma)` | Детали слова |
| `deleteWord(lemma)` | Удалить слово |
| `getDictionaryStats()` | Статистика |
| `showNotification(msg, type)` | Уведомление |

---

### HighlightsStorage.js
**Путь:** `static/js/HighlightsStorage.js`

Работа с localStorage для хайлайтов.

**Класс:** `HighlightsStorage`

| Метод | Описание |
|-------|----------|
| `saveHighlight(highlight, sessionId)` | Сохранить |
| `getSavedHighlights(sessionId)` | Получить по сессии |
| `getAllSessions()` | Все сессии |
| `generateSetTitle(text, maxLen)` | Генерация названия |
| `formatDate(dateStr)` | Форматирование даты |

---

### Auth.js
**Путь:** `static/js/Auth.js`

Авторизация пользователя.

---

## CSS Files

### variables.css
**Путь:** `static/css/variables.css`

CSS переменные (цвета, шрифты, spacing, shadows).

### global.css
**Путь:** `static/css/global.css`

Глобальные стили (reset, body, container, links, headings).

---

## Использование на страницах

### index.html (Анализ)
```html
<script src="/static/components/Header.js"></script>
<script src="/static/components/AnalysisForm.js"></script>
<script src="/static/components/HighlightCard.js"></script>
<script src="/static/js/HighlightsStorage.js"></script>
<script src="/static/js/DictionaryAPI.js"></script>
```

### dictionary-v2.html (Словарь)
```html
<link rel="stylesheet" href="/static/css/variables.css">
<link rel="stylesheet" href="/static/css/global.css">
<script src="/static/components/Header.js"></script>
<script src="/static/components/WordCardV2.js"></script>
<script src="/static/components/CustomDropdown.js"></script>
<script src="/static/js/DictionaryAPI.js"></script>
```

### my_highlights.html (Хайлайты)
```html
<script src="/static/components/Header.js"></script>
<script src="/static/components/HighlightCard.js"></script>
<script src="/static/js/HighlightsStorage.js"></script>
```
