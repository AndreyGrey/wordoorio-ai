# 🎨 Wordoorio Design System

**Version:** 1.0
**Last Updated:** 2024-12-09
**Author:** Wordoorio Team

---

## 📐 Принципы дизайна

### 1. Mobile-First
Все компоненты сначала разрабатываются для мобильных устройств (320px+), затем адаптируются для десктопа.

**Почему:** Большинство пользователей заходит с мобильных устройств.

### 2. Вертикальная оптимизация
Длинные списки (словарь, хайлайты) должны быть компактными, чтобы на экран помещалось много элементов.

**Принцип:** Минимум вертикального пространства, максимум информации.

### 3. Преемственность стилей
Единый визуальный язык во всех разделах приложения. Если компонент похож функционально — он должен выглядеть похоже.

**Пример:** HighlightCard используется везде одинаково: /experimental, /my_highlights, /dictionary modal.

### 4. Компонентная архитектура
Максимум переиспользования, минимум дублирования кода.

**Структура:** Один компонент = один файл в `static/components/`

---

## 🎨 Цветовая палитра

### Основные цвета

```css
/* Primary - зеленый (успех, действие) */
--color-primary: #4CAF50;
--color-primary-hover: #45A049;
--color-primary-light: rgba(76, 175, 80, 0.1);

/* Secondary - голубой (информация) */
--color-secondary: #39A0B3;
--color-secondary-dark: #1B7A94;

/* Background - градиент */
--gradient-main: linear-gradient(90deg, #39A0B3 0%, #1B7A94 100%);

/* Text */
--color-text-primary: #2d3748;
--color-text-secondary: #718096;
--color-text-muted: #a0aec0;

/* UI */
--color-white: #ffffff;
--color-gray-light: #e2e8f0;
--color-gray: #cbd5e0;
--color-gray-dark: #4a5568;

/* Status */
--color-error: #f56565;
--color-warning: #ed8936;
--color-info: #4299e1;
--color-success: #48bb78;
```

### Использование цветов

| Элемент | Цвет | Когда использовать |
|---------|------|--------------------|
| Кнопки действий | `--color-primary` | Основное действие (Analyze, Add, Save) |
| Фон приложения | `--gradient-main` | Всегда на body |
| Текст заголовков | `--color-text-primary` | h1, h2, h3 |
| Текст описаний | `--color-text-secondary` | Вспомогательный текст |
| Хайлайты (слова) | Orange | В HighlightCard для слов |
| Хайлайты (фразы) | Blue | В HighlightCard для фраз |

---

## 📝 Типографика

### Шрифты

```css
/* Основной текст */
--font-primary: 'Inter', sans-serif;

/* Заголовки */
--font-headings: 'Poppins', sans-serif;

/* Моноширинный (код) */
--font-mono: 'Manrope', monospace;
```

### Размеры шрифтов (Mobile-First)

```css
/* Mobile (320px+) */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */

/* Desktop (768px+) */
@media (min-width: 768px) {
  --text-3xl: 2.5rem;  /* 40px на десктопе */
}
```

### Использование

| Элемент | Размер | Вес |
|---------|--------|-----|
| H1 (Page Title) | `text-3xl` | 700 (Bold) |
| H2 (Section Title) | `text-2xl` | 600 (Semibold) |
| H3 (Subsection) | `text-xl` | 600 |
| Body Text | `text-base` | 400 (Regular) |
| Small Text (meta) | `text-sm` | 400 |
| Button Text | `text-base` | 600 |

---

## 📦 Компоненты

### Архитектура компонента

Каждый компонент должен:
1. ✅ Быть самодостаточным (свои стили)
2. ✅ Инжектировать стили через `getComponentStyles()`
3. ✅ Экспортировать функцию создания `createComponent(data, options)`
4. ✅ Поддерживать mobile-first дизайн

**Шаблон:**

```javascript
/**
 * MyComponent.js
 * Описание компонента
 */

function createMyComponent(data, options = {}) {
    const {
        showActions = true,
        theme = 'default'
    } = options;

    return `
        <div class="my-component" data-theme="${theme}">
            ${data.content}
        </div>
    `;
}

function getMyComponentStyles() {
    return `
        .my-component {
            /* Mobile-first стили */
            padding: 16px;
            border-radius: 12px;
        }

        @media (min-width: 768px) {
            .my-component {
                /* Desktop адаптация */
                padding: 24px;
            }
        }
    `;
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    const styles = document.createElement('style');
    styles.innerHTML = getMyComponentStyles();
    document.head.appendChild(styles);
});
```

---

## 🧩 Существующие компоненты

### 1. Header.js
**Назначение:** Унифицированный заголовок приложения

**Функции:**
- `initUnifiedHeader(containerId)` - Инициализация header в контейнере

**Использование:**
```html
<div id="header-container"></div>
<script src="/static/components/Header.js"></script>
<script>
    initUnifiedHeader('header-container');
</script>
```

---

### 2. AnalysisForm.js
**Назначение:** Форма для ввода текста на анализ

**Функции:**
- `initAnalysisForm(containerId, options)` - Инициализация формы

**Параметры:**
```javascript
{
    placeholder: 'Enter text...',
    subtitle: 'Description text',
    buttonText: 'Analyze'
}
```

**Использование:**
```javascript
initAnalysisForm('form-container', {
    placeholder: 'Paste your text here...',
    subtitle: 'AI-powered analysis'
});
```

---

### 3. HighlightCard.js ⭐ (Основной компонент)
**Назначение:** Карточка хайлайта (слово/фраза) с переводом

**Функции:**
- `createHighlightCard(highlight, index, color, showActions)` - Создать карточку
- `getHighlightCardStyles()` - Получить стили

**Параметры:**
```javascript
highlight = {
    highlight: "give up",           // Слово/фраза
    context: "Never give up...",    // Контекст
    highlight_translation: "сдаться", // Перевод
    type: "expression",             // "word" или "expression"
    dictionary_meanings: ["бросить"] // Доп. переводы
}

index = 0;              // Индекс в списке
color = "orange";       // "orange" для слов, "blue" для фраз
showActions = true;     // Показывать кнопки ➕ и 🗑️
```

**Использование:**
```javascript
// С кнопками (на странице анализа)
const cardHTML = createHighlightCard(highlight, 0, 'orange', true);

// Без кнопок (в словаре, в модалах)
const cardHTML = createHighlightCard(highlight, 0, 'blue', false);
```

**Внешний вид:**
- 🟠 **Оранжевая рамка** - для слов
- 🔵 **Синяя рамка** - для фраз
- Контекст - серый текст с подсветкой слова
- Перевод - крупный шрифт
- Дополнительные переводы - мелкие pills

---

### 4. DictionaryWordRow.js (NEW)
**Назначение:** Компактная строка для списка слов в словаре

**Функции:**
- `createDictionaryWordRow(word)` - Создать строку

**Параметры:**
```javascript
word = {
    lemma: "give up",
    type: "expression",
    translations: ["сдаться", "бросить"],
    examples_count: 3,
    added_at: "2024-12-09T10:00:00Z"
}
```

**Использование:**
```javascript
const rowHTML = createDictionaryWordRow(word);
document.getElementById('list').innerHTML += rowHTML;
```

**Дизайн:**
```
┌────────────────────────────────────┐
│ 💬 give up                         │
│ сдаться                            │
│ 3 примера • 09 дек 2024            │
└────────────────────────────────────┘
```

---

### 5. HighlightsStorage.js
**Назначение:** Управление сохраненными хайлайтами в localStorage

**Класс:** `HighlightsStorage`

**Методы:**
- `saveHighlight(highlight, sessionId)` - Сохранить хайлайт
- `getSavedHighlights(sessionId)` - Получить хайлайты сессии
- `getAllSessions()` - Получить все сессии
- `generateSetTitle(text, maxLength)` - Генерация названия сета
- `formatDate(dateString)` - Форматирование даты

**Использование:**
```javascript
const storage = new HighlightsStorage();

// Сохранить
storage.saveHighlight(highlight, 'session_123');

// Получить
const highlights = storage.getSavedHighlights('session_123');

// Все сессии
const sessions = storage.getAllSessions();
```

---

### 6. DictionaryAPI.js (NEW)
**Назначение:** API для работы со словарем

**Функции:**
- `addToDictionary(highlight, sessionId)` - Добавить в словарь
- `getAllWords()` - Получить все слова
- `getWord(lemma)` - Получить детали слова
- `deleteWord(lemma)` - Удалить слово
- `getStats()` - Статистика словаря

**Использование:**
```javascript
// Добавить слово
const result = await addToDictionary(highlight, 'session_123');
if (result.success) {
    showNotification('✅ Добавлено в словарь');
}

// Получить все слова
const words = await getAllWords();

// Детали слова
const word = await getWord('give up');
```

---

## 📐 Spacing & Layout

### Отступы (Mobile-First)

```css
/* Spacing scale */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;

/* Внутренние отступы карточек */
.card {
    padding: var(--space-md); /* 16px на мобиле */
}

@media (min-width: 768px) {
    .card {
        padding: var(--space-lg); /* 24px на десктопе */
    }
}

/* Отступы между элементами */
.list-item + .list-item {
    margin-top: var(--space-sm); /* 8px между карточками */
}
```

### Контейнеры

```css
.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px; /* Mobile */
}

@media (min-width: 768px) {
    .container {
        padding: 40px; /* Desktop */
    }
}
```

---

## 🎭 Интерактивность

### Анимации

```css
/* Hover эффект */
.card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Кнопки */
.button {
    transition: all 0.2s ease;
}

.button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
}

.button:active {
    transform: translateY(0);
}
```

### Тени

```css
/* Shadow scale */
--shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
--shadow-md: 0 4px 8px rgba(0,0,0,0.12);
--shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
--shadow-xl: 0 20px 40px rgba(0,0,0,0.2);

/* Использование */
.card {
    box-shadow: var(--shadow-md);
}

.modal {
    box-shadow: var(--shadow-xl);
}
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile First - базовые стили для 320px+ */
.component { }

/* Small tablets - 640px+ */
@media (min-width: 640px) { }

/* Tablets - 768px+ */
@media (min-width: 768px) { }

/* Desktop - 1024px+ */
@media (min-width: 1024px) { }

/* Large Desktop - 1280px+ */
@media (min-width: 1280px) { }
```

**Стратегия:** Пишем стили для мобильных, затем добавляем медиа-запросы для больших экранов.

---

## ✅ Checklist для нового компонента

Перед добавлением нового компонента убедись:

- [ ] Компонент нужен (нельзя переиспользовать существующий?)
- [ ] Файл назван в CamelCase: `MyComponent.js`
- [ ] Есть функция `createMyComponent(data, options)`
- [ ] Есть функция `getMyComponentStyles()`
- [ ] Стили инжектируются при загрузке страницы
- [ ] Mobile-first дизайн (базовые стили для 320px+)
- [ ] Адаптивность через `@media (min-width: 768px)`
- [ ] Соблюдена цветовая палитра
- [ ] Используется spacing scale (`--space-*`)
- [ ] Hover/active эффекты с transitions
- [ ] Добавлена документация в `docs/components/`

---

## 🚀 Примеры использования

### Пример 1: Страница со списком

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
    <script src="/static/components/Header.js"></script>
    <script src="/static/components/MyListComponent.js"></script>
    <style>
        body {
            background: linear-gradient(90deg, #39A0B3 0%, #1B7A94 100%);
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div id="header-container"></div>

    <!-- Content -->
    <div class="container">
        <h1>Page Title</h1>
        <div id="list-container"></div>
    </div>

    <script>
        // Init header
        initUnifiedHeader('header-container');

        // Render list
        const items = [...];
        const listHTML = items.map(item =>
            createMyListItem(item)
        ).join('');
        document.getElementById('list-container').innerHTML = listHTML;
    </script>
</body>
</html>
```

---

## 📖 Дополнительные ресурсы

- **Компоненты:** См. `docs/components/COMPONENTS_INDEX.md`
- **API:** См. `docs/api/DICTIONARY_API.md`
- **База данных:** См. `docs/architecture/DATABASE_SCHEMA.md`
- **Разработка:** См. `docs/development/COMPONENT_CREATION_GUIDE.md`

---

**Поддерживайте этот документ актуальным при добавлении новых компонентов!** 🎨
