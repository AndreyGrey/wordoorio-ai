# Wordoorio Design System

**Version:** 2.0
**Last Updated:** 2026-01-16
**Author:** Wordoorio Team

---

## Принципы дизайна

### 1. Mobile-First
Все компоненты сначала разрабатываются для мобильных устройств (320px+), затем адаптируются для десктопа.

**Основной breakpoint:** 640px

### 2. Вертикальная оптимизация
Длинные списки (словарь, хайлайты) должны быть компактными, чтобы на экран помещалось много элементов.

### 3. CSS Variables
Все стили используют переменные из `static/css/variables.css`. Компоненты должны использовать fallback значения.

### 4. Компонентная архитектура
Один компонент = один файл в `static/components/`

---

## Цветовая палитра

### Основные цвета (из variables.css)

```css
/* Primary - зеленый (успех, действие) */
--color-primary: #4CAF50;
--color-primary-dark: #45A049;

/* Secondary - бирюзовый (информация) */
--color-secondary: #39A0B3;
--color-secondary-dark: #1B7A94;

/* Background - градиент */
--color-bg-body: linear-gradient(90deg, #39A0B3 0%, #1B7A94 100%);

/* Text */
--color-text-primary: #2d3748;
--color-text-secondary: #4a5568;
--color-text-muted: #718096;
--color-text-light: #a0aec0;
--color-text-white: #ffffff;

/* Status (для рейтинга слов) */
--color-new: #718096;        /* Новое слово (rating 0-3) */
--color-learning: #ed8936;   /* Изучаю (rating 4-7) */
--color-learned: #48bb78;    /* Выучено (rating 8-10) */
```

---

## Типографика

### Шрифты

```css
--font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-family-heading: 'Manrope', 'Inter', sans-serif;
```

### Размеры

| Элемент | Размер | Вес |
|---------|--------|-----|
| Page Title | 1.75rem | 800 |
| Section Title | 1.25rem | 700 |
| Body | 1rem | 400 |
| Small/Meta | 0.875rem | 400 |
| Extra Small | 0.75rem | 500 |

---

## Компоненты

### Header.js v2.0

**Структура:** `[Logo + Nav]` слева, `[Auth dropdown]` справа

```javascript
// Инициализация
await initUnifiedHeader('header-container');
```

**Функции:**
- `createUnifiedHeader(user)` - создание HTML
- `getUnifiedHeaderStyles()` - стили
- `initUnifiedHeader(containerId)` - полная инициализация с API
- `toggleUserMenu()` - переключение dropdown
- `handleLogout()` - выход

**Размеры логотипа:**
- Desktop: 72px
- Tablet (640px): 52px
- Mobile (480px): 44px

---

### WordCardV2.js

**Назначение:** Карточка слова с рейтингом для страницы словаря

```javascript
// Создание карточки
const html = createWordCard(word, {
    showDelete: true,
    showRating: true,
    showStatus: true
});

// Рендер списка с обработчиками
renderWordList(words, 'container-id', {
    onDelete: (wordId, lemma, card) => { },
    onClick: (wordId, lemma, card) => { }
});
```

**Данные слова:**
```javascript
{
    id: 'word_123',
    lemma: 'serendipity',
    translation: 'счастливая случайность',
    translation_extra: 'удачное стечение',
    status: 'learning',  // new | learning | learned
    rating: 5,           // 0-10
    examples_count: 2,
    added_at: '2026-01-15T10:00:00Z'
}
```

**Рейтинг:**
- `low` (0-3): серый
- `medium` (4-7): оранжевый
- `high` (8-10): зеленый

---

### CustomDropdown.js

**Назначение:** Переиспользуемый dropdown

```javascript
// Создание HTML
const html = createCustomDropdown({
    id: 'sortDropdown',
    options: [
        { value: 'date', label: 'По дате' },
        { value: 'rating', label: 'По рейтингу' }
    ],
    defaultValue: 'date'
});

// Инициализация
const dropdown = initDropdown('sortDropdown', {
    onChange: (value, label, element) => { }
});

// Методы инстанса
dropdown.getValue();
dropdown.setValue('rating');
dropdown.open();
dropdown.close();
```

---

### HighlightCard.js

**Назначение:** Карточка хайлайта на странице анализа

```javascript
const html = createHighlightCard(highlight, index, 'orange', true);
```

**Цвета:**
- `orange` - для слов
- `blue` - для фраз

---

### HighlightsStorage.js

**Назначение:** Работа с localStorage для хайлайтов

```javascript
const storage = new HighlightsStorage();
storage.saveHighlight(highlight, sessionId);
const highlights = storage.getSavedHighlights(sessionId);
const sessions = storage.getAllSessions();
```

---

### DictionaryAPI.js

**Назначение:** API клиент для словаря

```javascript
await addToDictionary(highlight);
await getAllWords(filters);
await getWord(lemma);
await deleteWord(lemma);
await getDictionaryStats();
showNotification(message, type);
```

---

## Layout Patterns

### Page Header

```html
<header class="page-header">
    <h1 class="page-title">Словарь</h1>
    <div class="stats-inline">
        <span class="stat"><span class="stat-num">47</span> слов</span>
        <span class="divider">·</span>
        ...
    </div>
</header>
```

### Section Divider

```html
<div class="section-divider">
    <span class="section-label">Изучаю</span>
    <span class="section-line"></span>
    <span class="section-count">14</span>
</div>
```

### Empty State

```html
<div class="empty-state">
    <div class="empty-icon">...</div>
    <h3 class="empty-title">Словарь пуст</h3>
    <p class="empty-text">Описание</p>
    <a href="/analyze" class="empty-btn">Действие</a>
</div>
```

### Loading State

```html
<div class="loading-state">
    <div class="loading-spinner"></div>
    <div>Загрузка...</div>
</div>
```

---

## Responsive Breakpoints

```css
/* Mobile First - базовые стили для 320px+ */
.component { }

/* Tablet/Desktop - 640px+ */
@media (max-width: 640px) { }

/* Small mobile - 480px */
@media (max-width: 480px) { }
```

---

## Spacing

```css
--spacing-1: 0.25rem;   /* 4px */
--spacing-2: 0.5rem;    /* 8px */
--spacing-3: 0.75rem;   /* 12px */
--spacing-4: 1rem;      /* 16px */
--spacing-5: 1.25rem;   /* 20px */
--spacing-6: 1.5rem;    /* 24px */
--spacing-8: 2rem;      /* 32px */
```

---

## Shadows

```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
--shadow-md: 0 4px 12px rgba(0,0,0,0.1);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
```

---

## Файловая структура

```
static/
├── css/
│   ├── variables.css    # CSS переменные
│   └── global.css       # Глобальные стили
├── components/
│   ├── Header.js        # v2.0 - header с dropdown
│   ├── WordCardV2.js    # Карточка слова с рейтингом
│   ├── CustomDropdown.js # Переиспользуемый dropdown
│   ├── HighlightCard.js # Карточка хайлайта
│   └── AnalysisForm.js  # Форма анализа
└── js/
    ├── DictionaryAPI.js # API клиент
    ├── HighlightsStorage.js # localStorage
    └── Auth.js          # Авторизация
```

---

## Checklist для нового компонента

- [ ] Файл в `static/components/` в CamelCase
- [ ] Функция `createComponent(data, options)`
- [ ] Функция `getComponentStyles()` с fallback значениями
- [ ] Auto-init стилей через `DOMContentLoaded`
- [ ] Mobile-first (640px breakpoint)
- [ ] Использует CSS переменные из variables.css
- [ ] Export для module usage
