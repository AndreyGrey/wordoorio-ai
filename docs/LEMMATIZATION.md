# Лемматизация в Wordoorio

Полная документация по лемматизации: архитектура, проблемы, решения, тест-кейсы.

---

## 1. Архитектура

### 1.1 Пайплайн обработки

```
User Text → AI Agents (Yandex AI Studio, Qwen3-235B)
              ↓
    ┌─────────────┬─────────────┐
    │  Agent #1   │  Agent #2   │
    │   Words     │   Phrases   │
    └─────────────┴─────────────┘
              ↓
    Для каждого highlight:
    ┌─────────────────────────────────────────────────┐
    │ _dict_to_highlight() в analysis_orchestrator.py │
    │                                                 │
    │ 1. word = highlight из AI                       │
    │ 2. word_lemma, is_participle = lemmatize(word)  │
    │ 3. Словарь Yandex Dictionary (для 1 слова)      │
    │ 4. raw_translation = перевод из AI              │
    │ 5. main_translation = lemmatize_russian(...)    │
    │    или оставляем как есть (если EN = причастие) │
    └─────────────────────────────────────────────────┘
              ↓
    Remove Duplicates (по lemma)
              ↓
    Highlights → Frontend (карточки)
```

### 1.2 Ключевые файлы

| Файл | Назначение |
|------|------------|
| `utils/lemmatizer.py` | Функции лемматизации для EN и RU |
| `core/analysis_orchestrator.py` | Оркестратор, метод `_dict_to_highlight()` |
| `contracts/analysis_contracts.py` | Типы данных: Highlight, AgentResponse |
| `docs/PROMPTS.md` | Версии промптов для AI-агентов |

### 1.3 Зависимости

```
spacy==3.7.2          # Английская лемматизация
en_core_web_sm        # Модель spaCy (скачивается отдельно)
pymorphy2==0.9.1      # Русская лемматизация
```

---

## 2. Определение части речи (POS)

### 2.1 Английский — spaCy

spaCy автоматически определяет POS при морфологическом анализе:

```python
import spacy
nlp = spacy.load("en_core_web_sm")

doc = nlp("embroiled")
for token in doc:
    print(f"{token.text}: pos_={token.pos_}, tag_={token.tag_}")
    # embroiled: pos_=VERB, tag_=VBN
```

**Ключевые теги:**

| tag_ | Описание | Пример |
|------|----------|--------|
| VBN | Past participle | embroiled, broken, written |
| VBG | Gerund / Present participle | amplifying, running |
| VB | Verb, base form | run, go |
| VBD | Verb, past tense | ran, went |
| VBZ | Verb, 3rd person singular | runs, goes |
| NN | Noun, singular | cat, dog |
| NNS | Noun, plural | cats, dogs |
| JJ | Adjective | big, compelling |

**Важно:** spaCy анализирует слово ВНЕ контекста (мы передаем отдельное слово/фразу). Это может привести к неоднозначности: "run" без контекста может быть и глаголом, и существительным.

### 2.2 Русский — pymorphy2

pymorphy2 определяет POS через морфологический анализ:

```python
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

parsed = morph.parse("засыпали")[0]
print(f"POS: {parsed.tag.POS}")  # VERB
print(f"normal_form: {parsed.normal_form}")  # засыпать
```

**Ключевые POS:**

| POS | Описание | Пример |
|-----|----------|--------|
| VERB | Глагол в личной форме | засыпали, бежит |
| INFN | Инфинитив | засыпать, бежать |
| NOUN | Существительное | кошка, собака |
| ADJF | Прилагательное (полное) | большой, красивая |
| ADJS | Прилагательное (краткое) | велик, красива |
| PRTF | Причастие (полное) | захватывающий, сделанный |
| PRTS | Причастие (краткое) | сделан, написана |

---

## 3. Логика лемматизации

### 3.1 Английский: `lemmatize()`

**Файл:** `utils/lemmatizer.py`

**Правила:**
1. Причастия (VBN, VBG) — НЕ лемматизируем, оставляем как есть
2. Все остальное — лемматизируем через spaCy

```python
def lemmatize(text: str) -> str:
    nlp = _get_nlp()
    doc = nlp(text.strip())

    lemmas = []
    for token in doc:
        if token.tag_ in ('VBN', 'VBG'):
            # Причастие — оставляем как есть
            lemmas.append(token.text.lower())
        else:
            # Лемматизируем
            lemmas.append(token.lemma_)

    return " ".join(lemmas)
```

**Примеры:**

| Вход | Выход | Почему |
|------|-------|--------|
| incentives | incentive | NNS → лемма |
| went | go | VBD → лемма |
| embroiled | embroiled | VBN → оставляем |
| amplifying | amplifying | VBG → оставляем |
| gave up | give up | VBD + RP → лемма первого слова |

**Почему причастия не лемматизируем:**
- "embroiled" в контексте "embroiled in conflict" — это причастие, не глагол
- Если лемматизировать → "embroil in conflict" — странно
- На карточке должно быть "embroiled", не "embroil"

### 3.2 Русский: `lemmatize_russian()`

**Файл:** `utils/lemmatizer.py`

**Правила для одиночных слов:**
1. Глагол (VERB, INFN) → инфинитив через `normal_form`
2. Причастие/прилагательное (ADJF, ADJS, PRTF, PRTS) → м.р. ед.ч. им.п. через `inflect()`
3. Существительное (NOUN) → ед.ч. им.п. через `inflect()`
4. Остальное → `normal_form`

**Правила для фраз (2+ слов):**
- НЕ трогаем — оставляем как вернул AI-агент
- AI лучше справляется с согласованием внутри фразы

```python
def lemmatize_russian(text: str) -> str:
    morph = _get_morph()
    words = text.strip().split()

    if len(words) == 1:
        parsed = morph.parse(words[0])[0]
        pos = parsed.tag.POS

        if pos == 'VERB' or pos == 'INFN':
            return parsed.normal_form  # засыпали → засыпать
        elif pos in ('ADJF', 'ADJS', 'PRTF', 'PRTS'):
            # ВАЖНО: inflect(), НЕ normal_form!
            inflected = parsed.inflect({'masc', 'sing', 'nomn'})
            return inflected.word if inflected else parsed.normal_form
        elif pos == 'NOUN':
            inflected = parsed.inflect({'sing', 'nomn'})
            return inflected.word if inflected else parsed.normal_form
        else:
            return parsed.normal_form
    else:
        # Фразы не трогаем
        return text.strip()
```

**Примеры:**

| Вход | POS | Выход | Метод |
|------|-----|-------|-------|
| захватывающие | PRTF | захватывающий | inflect() |
| нарушающая | PRTF | нарушающий | inflect() |
| адаптировались | VERB | адаптироваться | normal_form |
| касается | VERB | касаться | normal_form |
| закрытая экосистема | — | закрытая экосистема | не трогаем |

**Почему `inflect()` для причастий, а не `normal_form`:**
- `normal_form` для причастия возвращает ГЛАГОЛ: "нарушающая" → "нарушать"
- `inflect({'masc', 'sing', 'nomn'})` возвращает ПРИЧАСТИЕ: "нарушающая" → "нарушающий"
- Это критически важно для сохранения части речи

### 3.3 Согласование EN ↔ RU

**Проблема:** EN и RU обрабатываются независимо → несогласованность частей речи.

**Пример проблемы:**
- EN: "peppered" (VBN, причастие) → оставляем "peppered"
- RU: "засыпали" (VERB) → `normal_form` → "засыпать" (инфинитив)
- Результат: "peppered" + "засыпать" — несогласованно

**Решение:** если EN = причастие (VBN/VBG), RU не лемматизируем.

```python
# В _dict_to_highlight():
word_lemma, is_participle = lemmatize_with_pos(word)

if is_participle:
    # EN причастие → RU оставляем как есть от AI
    main_translation = raw_translation.lower()
else:
    # EN не причастие → RU лемматизируем
    main_translation = lemmatize_russian(raw_translation).lower()
```

---

## 4. Собранные проблемы и решения

### 4.1 Категория A: RU перевод не в словарной форме

AI-агент возвращает перевод в контекстной форме (род, число, время).

| EN | RU от AI | Должно быть | Проблема |
|----|----------|-------------|----------|
| intriguing | захватывающие | захватывающий | мн.ч. → м.р. ед.ч. |
| adapted | адаптировались | адаптироваться | прош.вр. → инфинитив |
| bogus | поддельные | поддельный | мн.ч. → м.р. ед.ч. |
| disruptive | нарушающая | нарушающий | ж.р. → м.р. |

**Решение:** `lemmatize_russian()` с pymorphy2.

### 4.2 Категория B: EN слово не в базовой форме

AI-агент возвращает слово в контекстной форме, а не в словарной.

| Показывалось | Должно быть | Причина |
|--------------|-------------|---------|
| pertains | pertain | AI нарушил промпт |
| embroiled | embroiled | Причастие — оставляем |
| popped up | pop up | Фраза — лемматизируем |

**Решение:** используем spaCy-лемму для отображения (`highlight=word_lemma`).

### 4.3 Категория C: Несогласованность EN ↔ RU

| EN (POS) | RU | Проблема |
|----------|-----|----------|
| peppered (VBN) | засыпать | EN причастие, RU инфинитив |
| embroiled (VBN) | втянуть | EN причастие, RU инфинитив |

**Решение:** если EN = причастие, RU не лемматизируем.

---

## 5. Тест-кейсы

### 5.1 Английская лемматизация

```python
english_tests = [
    # Обычные слова → лемматизируются
    ("incentives", "incentive"),
    ("went", "go"),
    ("bigger", "big"),
    ("stories", "story"),
    # Причастия (VBN, VBG) → НЕ лемматизируются
    ("embroiled", "embroiled"),
    ("amplifying", "amplifying"),
    ("running", "running"),
    ("broken", "broken"),
    # Фразы
    ("gave up", "give up"),
    ("came across", "come across"),
]
```

### 5.2 Русская лемматизация

```python
russian_tests = [
    # Причастия/прилагательные → м.р. ед.ч.
    ("захватывающие", "захватывающий"),
    ("нарушающая", "нарушающий"),
    ("поддельные", "поддельный"),
    ("сосредоточённое", "сосредоточённый"),
    # Глаголы → инфинитив
    ("адаптировались", "адаптироваться"),
    ("касается", "касаться"),
    ("появился", "появиться"),
    # Фразы → не трогаем
    ("закрытая экосистема", "закрытая экосистема"),
    ("засыпали вопросами", "засыпали вопросами"),
]
```

### 5.3 Запуск тестов

```bash
python utils/lemmatizer.py
```

---

## 6. Промпты AI-агентов

Промпты хранятся в `docs/PROMPTS.md`.

**Ключевые требования в промптах v2.0:**

**Agent #1 (Words):**
- `highlight`: базовая форма (существительные → ед.ч., глаголы → инфинитив, причастия → как есть)
- `highlight_translation`: словарная форма (м.р. ед.ч. для прил/прич, инфинитив для глаголов)

**Agent #2 (Phrases):**
- `highlight`: базовая форма (phrasal verbs → инфинитив: "pop up", не "popped up")
- `highlight_translation`: словарная форма

---

## 7. Известные ограничения

### 7.1 spaCy без контекста

spaCy анализирует слово изолированно, что может привести к неоднозначности:
- "run" → может быть глаголом или существительным
- "skirting" → может быть герундием от "skirt" или существительным "плинтус"

**Митигация:** доверяем AI-агенту в выборе контекста, код только нормализует форму.

### 7.2 pymorphy2 неоднозначность

pymorphy2 может вернуть несколько вариантов разбора. Мы берем первый (`[0]`), который обычно наиболее вероятный.

### 7.3 Фразы

Фразы (2+ слов) не лемматизируем в русском, чтобы не сломать согласование:
- "закрытая экосистема" → оставляем как есть
- Если лемматизировать первое слово → "закрытый экосистема" — неграмотно

---

## 8. История изменений

| Коммит | Изменение |
|--------|-----------|
| e9d0f10 | Удален pymorphy2 (ошибочно) |
| 5c6dd36 | Добавлен pymorphy2, `lemmatize_russian()` |
| 2381bd5 | Исправлена лемматизация причастий (inflect vs normal_form) |
| 39c4787 | EN причастия (VBN/VBG) не лемматизируются |

---

## 9. TODO

- [ ] Реализовать согласование EN ↔ RU: если EN причастие, RU не лемматизировать
- [ ] Добавить функцию `lemmatize_with_pos()` для получения POS вместе с леммой
- [ ] Тесты на согласованность EN/RU частей речи
