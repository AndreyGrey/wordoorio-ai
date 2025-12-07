# YouTube Transcript Analysis

## Обзор

Функционал анализа YouTube видео позволяет пользователям извлекать транскрипты английских видео и анализировать их лексику с помощью AI агентов.

**Дата внедрения:** 2025-12-04
**Статус:** ✅ Production Ready

---

## Архитектура

### Компоненты

1. **YouTube Agent** (`agents/youtube_agent.py`)
   - Извлечение транскриптов через `youtube-transcript-api`
   - Поддержка различных форматов YouTube URL
   - Получение метаданных видео (название, длительность, количество слов)

2. **Frontend** (`templates/youtube.html`)
   - Минималистичный UI с персонажем Wordoorio
   - Форма ввода YouTube URL
   - Loading animation во время обработки
   - Обработка ошибок

3. **Backend Routes** (`web_app.py`)
   - `GET /youtube` - страница ввода URL
   - `POST /youtube/analyze` - извлечение транскрипта и возврат данных

4. **Integration** (`templates/experimental.html`)
   - Автоматическое заполнение формы транскриптом
   - Запуск dual-prompt анализа
   - Отображение результатов (слова + фразы)

---

## User Flow

```
1. Пользователь открывает /youtube
   ↓
2. Вставляет ссылку на YouTube видео
   ↓
3. Нажимает "GO!"
   ↓
4. Backend извлекает транскрипт (2-5 сек)
   ↓
5. Данные сохраняются в localStorage
   ↓
6. Редирект на /experimental
   ↓
7. Auto-fill формы транскриптом
   ↓
8. Автоматический запуск анализа (60-90 сек)
   ↓
9. Отображение результатов с summary pill
```

---

## API Specification

### POST /youtube/analyze

**Request:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response (Success):**
```json
{
  "success": true,
  "redirect": "/experimental",
  "transcript": "Full transcript text...",
  "video_title": "Video Title",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "word_count": 2615
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Субтитры отключены для этого видео"
}
```

---

## Поддерживаемые форматы URL

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`
- `https://www.youtube.com/watch?v=VIDEO_ID&t=123`

---

## Обработка ошибок

| Код ошибки | Сценарий | Сообщение пользователю |
|------------|----------|------------------------|
| `TranscriptsDisabled` | Субтитры отключены автором | "Субтитры отключены для этого видео" |
| `VideoUnavailable` | Видео приватное/удалено | "Видео недоступно (приватное или удалено)" |
| `RequestBlocked` | Rate limit YouTube API | "Слишком много запросов. Попробуйте через несколько минут" |
| `InvalidURL` | Невалидный URL | "Невалидный YouTube URL. Поддерживаемые форматы: youtube.com/watch?v=..." |
| `NoTranscriptFound` | Нет английских субтитров | "Английские субтитры не найдены" |

---

## Технические детали

### localStorage Data Transfer

Вместо Flask session используется localStorage для передачи больших транскриптов (>8KB):

```javascript
// youtube.html - сохранение
localStorage.setItem('youtube_transcript_data', JSON.stringify({
    transcript: data.transcript,
    video_title: data.video_title,
    video_url: videoUrl
}));
window.location.href = '/experimental';

// experimental.html - получение
const youtubeData = JSON.parse(localStorage.getItem('youtube_transcript_data'));
if (youtubeData) {
    document.getElementById('textInput').value = youtubeData.transcript;
    localStorage.removeItem('youtube_transcript_data');
    analyzeText(); // auto-start
}
```

**Причина:** Flask session ограничена 4KB cookie, транскрипты часто 10-50KB.

### YouTube Transcript Agent

**Библиотека:** `youtube-transcript-api==0.6.1`

**Основной метод:**
```python
def extract_transcript(self, video_url: str) -> Dict:
    """
    Returns:
    {
        'success': bool,
        'video_id': str,
        'video_title': str,
        'transcript': str,        # Полный текст
        'segments': list,         # [{start, duration, text}]
        'word_count': int,
        'duration': float,        # секунды
        'method': 'youtube-transcript-api',
        'language': 'en',
        'error': str | None
    }
    """
```

---

## UI/UX Design

### YouTube Page (`/youtube`)

- **Layout:** Horizontal - персонаж Wordoorio слева, форма справа
- **Input:** Большое белое поле с placeholder "вставьте ссылку на ютуб-видео"
- **Button:** "GO!" (80px height, темно-синий #1e4a5f)
- **Background:** Трехцветный градиент (#39A0B3 → #D4E7C5 → #39A0B3)
- **Character:** wordoorio-logo.svg смещен вниз на -40px (эффект "выглядывания")

### Results Page (`/experimental`)

**Новые элементы:**

1. **Summary Pill** - компактная таблетка с количеством хайлайтов
   - Стиль: `background: #0A3A4D`, `color: #ffffff`, `font-size: 18px`
   - Формат: "21 хайлайт из 2615 слов"
   - Правильная русская грамматика (хайлайт/хайлайта/хайлайтов)

2. **Original Text Block** - блок с исходным текстом
   - Расположен между summary и tabs
   - Стиль: белый фон, серый текст, скругленные углы
   - Полезен для проверки контекста

3. **Tabs** - без эмодзи
   - "Слова" | "Фразы" | "Все вместе"
   - Чистый дизайн без визуального шума

---

## Производительность

| Этап | Время | Оптимизация |
|------|-------|-------------|
| Извлечение транскрипта | 2-5 сек | `youtube-transcript-api` (нет скачивания видео) |
| Dual-prompt анализ | 60-90 сек | Параллельные промпты к YandexGPT |
| Отображение результатов | <1 сек | Рендер 20-30 карточек |

**Типичный workflow:** ~75 секунд от вставки URL до результатов

---

## Deployment Checklist

- [x] Добавлена зависимость `youtube-transcript-api==0.6.1` в requirements.txt
- [x] Удален избыточный код (session routes, неиспользуемые CSS классы)
- [x] Проверена работа на production (158.160.126.200)
- [x] Обработаны все edge cases (rate limits, отключенные субтитры)
- [x] Документация обновлена

---

## Известные ограничения

1. **Только английские субтитры** - фильтр `languages=['en', 'en-US', 'en-GB']`
2. **Зависит от YouTube API** - может быть rate-limited при высокой нагрузке
3. **Нет поддержки live-стримов** - только загруженные видео
4. **Максимальная длина видео** - не ограничена, но очень длинные транскрипты (>50K слов) могут долго анализироваться

---

## Future Enhancements

1. **Поддержка других языков** - добавить выбор языка субтитров
2. **Кеширование транскриптов** - сохранять в БД для повторного использования
3. **Прогресс-бар для анализа** - показывать % completion
4. **Экспорт в Anki** - создание flashcards из хайлайтов
5. **Поддержка плейлистов** - анализ нескольких видео подряд

---

## Code References

- **Agent:** `agents/youtube_agent.py:29-296`
- **Backend:** `web_app.py:485-529`
- **Frontend:** `templates/youtube.html:1-354`
- **Integration:** `templates/experimental.html:314-367`
- **Dependencies:** `requirements.txt:6`
