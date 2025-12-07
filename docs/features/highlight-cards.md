# 📋 HIGHLIGHT CARD SPECIFICATION

Спецификация компонента карточки хайлайта для Wordoorio

---

## 🎯 Назначение

**HighlightCard** - переиспользуемый UI компонент для отображения найденного слова/фразы с его характеристиками.

---

## 📦 Структура данных (Backend → Frontend)

### Полный объект Highlight:

```python
@dataclass
class Highlight:
    # === ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ===
    highlight: str                    # Само слово/фраза
    context: str                     # Контекст из текста
    context_translation: str         # Перевод контекста

    # === ОПЦИОНАЛЬНЫЕ ПОЛЯ ===
    english_example: str = ""        # Пример на английском
    russian_example: str = ""        # Пример на русском
    cefr_level: str = "C1"          # Уровень сложности (A1-C2)
    importance_score: int = 85       # Важность (0-100)
    dictionary_meanings: List[str] = []  # Словарные определения
    why_interesting: str = ""        # Почему интересен
```

### JSON пример:

```json
{
  "highlight": "sophisticated",
  "context": "This is a sophisticated approach to solving problems.",
  "context_translation": "утончённый, сложный, изысканный",
  "english_example": "Example: This is a sophisticated approach...",
  "russian_example": "[ПЕРЕВОД: sophisticated]",
  "cefr_level": "C1",
  "importance_score": 85,
  "dictionary_meanings": [
    "сложный или утончённый",
    "имеющий опыт в мире и культуре"
  ],
  "why_interesting": "Выразительная лексика для стильной речи"
}
```

---

## 🎨 UI Элементы карточки

### 1. **Основное слово/фраза** ✅ ОБЯЗАТЕЛЬНО

**Поле**: `highlight`
**Отображение**: Крупный шрифт, жирное начертание
**Формат**: `{номер}. {слово}`

```html
<div class="highlight-word">
    1. sophisticated
</div>
```

**CSS**:
```css
.highlight-word {
    font-size: 20px;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 8px;
}
```

---

### 2. **Перевод контекста** ✅ ОБЯЗАТЕЛЬНО

**Поле**: `context_translation`
**Отображение**: Средний шрифт, серый цвет
**Назначение**: Быстрый перевод значения слова

```html
<div class="highlight-translation">
    утончённый, сложный, изысканный
</div>
```

**CSS**:
```css
.highlight-translation {
    font-size: 16px;
    color: #718096;
    margin-bottom: 12px;
    font-style: italic;
}
```

---

### 3. **Словарные определения** ⚠️ ОПЦИОНАЛЬНО

**Поле**: `dictionary_meanings`
**Условие**: Показывать если `dictionary_meanings.length > 0`
**Источник**: Free Dictionary API → Yandex Translate
**Отображение**: Список через `;`

```html
<div class="highlight-meaning">
    <strong>📚 Словарные значения:</strong>
    сложный или утончённый; имеющий опыт в мире и культуре
</div>
```

**CSS**:
```css
.highlight-meaning {
    font-size: 14px;
    color: #4a5568;
    background: #f7fafc;
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 12px;
}
```

**Логика**:
```javascript
const meaningsHtml = highlight.dictionary_meanings?.length > 0
    ? `<div class="highlight-meaning">
         <strong>📚 Словарные значения:</strong>
         ${highlight.dictionary_meanings.join('; ')}
       </div>`
    : '';
```

---

### 4. **Контекст с подсветкой** ✅ ОБЯЗАТЕЛЬНО

**Поле**: `context`
**Обработка**: Подсветить `highlight` внутри `context`
**Отображение**: Цитата с выделенным словом

```html
<div class="highlight-context">
    "This is a <span class="highlighted-word">sophisticated</span> approach..."
</div>
```

**CSS**:
```css
.highlight-context {
    font-size: 14px;
    color: #4a5568;
    background: #edf2f7;
    padding: 12px;
    border-left: 3px solid #4299e1;
    border-radius: 4px;
    font-style: italic;
}

.highlighted-word {
    background: #fef08a;  /* Желтая подсветка */
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 600;
}
```

---

### 5. **Примеры использования** ⚠️ ОПЦИОНАЛЬНО (будущее)

**Поля**: `english_example`, `russian_example`
**Статус**: Пока не используется в UI (есть в данных)
**Планируется**: Показывать примеры употребления

```html
<div class="highlight-examples">
    <div class="example-en">
        📝 Example: She presented a sophisticated argument.
    </div>
    <div class="example-ru">
        🇷🇺 Она представила изощрённый аргумент.
    </div>
</div>
```

---

### 6. **Метаданные** ⚠️ ОПЦИОНАЛЬНО (будущее)

**Поля**: `cefr_level`, `importance_score`, `why_interesting`
**Статус**: Есть в данных, но не отображается в UI
**Планируется**: Бейджи с уровнем и важностью

```html
<div class="highlight-meta">
    <span class="badge badge-level">C1</span>
    <span class="badge badge-score">⭐ 85/100</span>
    <span class="badge badge-reason">Выразительная лексика</span>
</div>
```

---

## 📐 Полная структура карточки

### Текущая версия (v1):

```html
<div class="highlight-item">
    <!-- 1. Слово/фраза (ОБЯЗАТЕЛЬНО) -->
    <div class="highlight-word">
        {номер}. {highlight}
    </div>

    <!-- 2. Перевод (ОБЯЗАТЕЛЬНО) -->
    <div class="highlight-translation">
        {context_translation}
    </div>

    <!-- 3. Словарные значения (ОПЦИОНАЛЬНО) -->
    {if dictionary_meanings.length > 0}
    <div class="highlight-meaning">
        <strong>📚 Словарные значения:</strong>
        {dictionary_meanings.join('; ')}
    </div>
    {/if}

    <!-- 4. Контекст с подсветкой (ОБЯЗАТЕЛЬНО) -->
    <div class="highlight-context">
        "{context_with_highlighted_word}"
    </div>
</div>
```

### Планируемая версия (v2):

```html
<div class="highlight-item">
    <!-- Заголовок -->
    <div class="highlight-header">
        <div class="highlight-word">{номер}. {highlight}</div>
        <div class="highlight-meta">
            <span class="badge">{cefr_level}</span>
            <span class="badge">⭐ {importance_score}</span>
        </div>
    </div>

    <!-- Перевод -->
    <div class="highlight-translation">{context_translation}</div>

    <!-- Словарные значения -->
    <div class="highlight-vocabulary">
        <strong>📚 Словарь:</strong>
        <ul>
            {dictionary_meanings.map(m => <li>{m}</li>)}
        </ul>
    </div>

    <!-- Контекст -->
    <div class="highlight-context">"{context}"</div>

    <!-- Примеры -->
    <div class="highlight-examples">
        <div class="example-en">{english_example}</div>
        <div class="example-ru">{russian_example}</div>
    </div>

    <!-- Почему интересен -->
    <div class="highlight-reason">{why_interesting}</div>
</div>
```

---

## 🔧 API данных

### Источник словарных значений:

**API**: [Free Dictionary API](https://dictionaryapi.dev/)
**Endpoint**: `https://api.dictionaryapi.dev/api/v2/entries/en/{word}`

**Ответ API**:
```json
[
  {
    "word": "sophisticated",
    "meanings": [
      {
        "partOfSpeech": "adjective",
        "definitions": [
          {
            "definition": "Having worldly experience and knowledge of culture",
            "example": "A sophisticated woman"
          }
        ]
      }
    ]
  }
]
```

**Обработка**:
1. Берем первые 2 meanings
2. Берем первое definition из каждого
3. Переводим через Yandex Translate
4. Сохраняем в `dictionary_meanings[]`

---

## 📊 Таблица элементов

| Элемент | Поле | Обязательность | Статус в UI | Источник |
|---------|------|----------------|-------------|----------|
| Слово/фраза | `highlight` | ✅ ОБЯЗАТЕЛЬНО | ✅ Используется | Yandex GPT |
| Перевод | `context_translation` | ✅ ОБЯЗАТЕЛЬНО | ✅ Используется | Yandex GPT → Yandex Translate |
| Контекст | `context` | ✅ ОБЯЗАТЕЛЬНО | ✅ Используется | Yandex GPT |
| Словарь | `dictionary_meanings[]` | ⚠️ Опционально | ✅ Используется | Free Dictionary API → Yandex Translate |
| Примеры EN | `english_example` | ⚠️ Опционально | ❌ Не используется | Yandex GPT |
| Примеры RU | `russian_example` | ⚠️ Опционально | ❌ Не используется | Yandex Translate |
| Уровень | `cefr_level` | ⚠️ Опционально | ❌ Не используется | Фиксированный (C1) |
| Важность | `importance_score` | ⚠️ Опционально | ❌ Не используется | Фиксированный (85) |
| Причина | `why_interesting` | ⚠️ Опционально | ❌ Не используется | Фиксированный текст |

---

## 🎯 Следующие шаги

### 1. Создать переиспользуемый компонент
- [ ] `interface/components/HighlightCard.js`
- [ ] Принимает данные highlight
- [ ] Рендерит все секции
- [ ] Используется на всех страницах

### 2. Расширить функционал
- [ ] Показывать примеры (`english_example`, `russian_example`)
- [ ] Показывать метаданные (уровень, важность)
- [ ] Показывать "почему интересен"

### 3. Улучшить API данные
- [ ] Динамический CEFR level (сейчас всегда C1)
- [ ] Динамический importance_score (сейчас всегда 85)
- [ ] Реальное "why_interesting" от GPT

---

**Создано**: 1 декабря 2025
**Версия**: 1.0
**Статус**: Draft - требует согласования
