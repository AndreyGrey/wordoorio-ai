# YouTube Datacenter IP Block Issue

**Дата:** 2025-12-05
**Статус:** 🔴 CRITICAL BUG
**Приоритет:** P0

---

## 🐛 Проблема

YouTube блокирует запросы с IP адресов датацентров (включая Yandex Cloud).

### Ошибка
```
Could not retrieve a transcript for the video!
This is most likely caused by: The video is unplayable for the following reason:
This content isn't available.
```

### Тестированные видео (все заблокированы):
- `https://www.youtube.com/watch?v=qWK47sqLmJQ` ❌
- `https://www.youtube.com/watch?v=jNQXAC9IVRw` ("Me at the zoo") ❌
- `https://www.youtube.com/watch?v=9bZkp7q19f0` ("Gangnam Style") ❌

### Причина
YouTube использует несколько методов детекции:
1. **IP reputation** - определяет что IP принадлежит дата центру
2. **User-Agent** - отсутствие браузерных заголовков
3. **Rate limiting** - слишком много запросов с одного IP
4. **Bot detection** - отсутствие cookies, JavaScript execution

---

## ✅ Решения

### Решение 1: yt-dlp (РЕКОМЕНДУЕТСЯ)

**Преимущества:**
- Обходит блокировки YouTube
- Активно поддерживается
- Работает с любыми видео
- Не требует cookies

**Установка:**
```bash
pip install yt-dlp==2024.12.3
```

**Код:**
```python
import subprocess
import json

def extract_subtitles_ytdlp(video_url):
    """Extract subtitles using yt-dlp"""
    cmd = [
        'yt-dlp',
        '--skip-download',
        '--write-auto-subs',
        '--sub-lang', 'en',
        '--sub-format', 'json3',
        '--print', '%(subtitles)s',
        video_url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        subtitles = json.loads(result.stdout)
        return subtitles
    else:
        raise Exception(f"yt-dlp failed: {result.stderr}")
```

**Статус:** ✅ Библиотека установлена на production (2024-12-05)

---

### Решение 2: YouTube API v3 (АЛЬТЕРНАТИВА)

**Преимущества:**
- Официальный метод
- Надежный
- Документирован

**Недостатки:**
- Требует API ключ
- Квоты (10,000 units/day)
- Платный при превышении квот

**Установка:**
```bash
pip install google-api-python-client
```

**Код:**
```python
from googleapiclient.discovery import build

def get_captions_official(video_id, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Get caption tracks
    captions = youtube.captions().list(
        part='snippet',
        videoId=video_id
    ).execute()

    # Download caption
    caption_id = captions['items'][0]['id']
    caption_content = youtube.captions().download(
        id=caption_id,
        tfmt='json3'
    ).execute()

    return caption_content
```

---

### Решение 3: Proxy/VPN

**Преимущества:**
- Работает с любыми библиотеками
- Прозрачно

**Недостатки:**
- Дополнительная сложность
- Стоимость proxy сервиса
- Медленнее

**Установка:**
```bash
pip install requests[socks]
```

**Код:**
```python
proxies = {
    'http': 'socks5://user:pass@proxy:port',
    'https': 'socks5://user:pass@proxy:port'
}

response = requests.get(url, proxies=proxies)
```

---

### Решение 4: Cookies от браузера

**Преимущества:**
- Не требует дополнительных сервисов
- Бесплатно

**Недостатки:**
- Cookies expire
- Нужно периодически обновлять
- Не всегда помогает с datacenter IPs

**Экспорт cookies из Chrome:**
```bash
# Используйте browser extension "Get cookies.txt"
# Сохраните в cookies.txt
```

**Код:**
```python
from youtube_transcript_api import YouTubeTranscriptApi

cookies_path = '/path/to/cookies.txt'
transcript = YouTubeTranscriptApi.fetch(
    video_id,
    languages=['en'],
    cookies=cookies_path
)
```

---

## 📋 План реализации (Следующие шаги)

### Фаза 1: yt-dlp Fallback (СРОЧНО)
- [x] Установлена библиотека yt-dlp
- [ ] Добавить метод `extract_transcript_ytdlp()` в YouTubeTranscriptAgent
- [ ] Обновить `extract_transcript()` для использования fallback
- [ ] Протестировать на production

### Фаза 2: Улучшения
- [ ] Добавить retry логику
- [ ] Кеширование транскриптов в базе данных
- [ ] Метрики: сколько запросов fallback vs primary
- [ ] Logging для диагностики

### Фаза 3: Долгосрочно
- [ ] Рассмотреть YouTube API v3 (если объем вырастет)
- [ ] Или использовать managed proxy service

---

## 🧪 Тестирование

###Тест yt-dlp на production:
```bash
ssh yc-user@158.160.126.200
cd /var/www/wordoorio
source venv/bin/activate

yt-dlp --skip-download --write-subs --sub-lang en --print "%(title)s" \
  https://www.youtube.com/watch?v=jNQXAC9IVRw
```

**Ожидаемый результат:** Название видео + загрузка субтитров

---

## 📚 Ссылки

- [youtube-transcript-api Issue #301](https://github.com/jdepoix/youtube-transcript-api/issues/301) - Datacenter IP blocks
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [YouTube API v3 Captions](https://developers.google.com/youtube/v3/docs/captions)

---

**Обновлено:** 2025-12-05
**Ответственный:** Andrew Kondakow
