# Деплой Wordoorio на Yandex Cloud Serverless Container

Полная инструкция по настройке автоматического деплоя через GitHub Actions.

## 📋 Архитектура

```
GitHub Repository
      ↓ (push to main)
GitHub Actions
      ↓
Docker Build → Container Registry → Serverless Container
                                           ↓
                                      API Gateway
                                           ↓
                                    wordoorio.ru
```

**Keep-Alive:** Cloud Function пингует сайт каждые 10 минут (нет холодных стартов).

**IAM Токены:** Обновляются автоматически через Metadata Service (не требуют ручного обновления).

## 💰 Стоимость

- **Serverless Container:** ~50-75₽/месяц (зависит от трафика)
- **Keep-Alive Function:** ~25₽/месяц (4320 вызовов × 128MB × ~1 сек)
- **API Gateway:** бесплатно (до 1M запросов)
- **SSL Certificate:** бесплатно (Let's Encrypt через Certificate Manager)

**Итого:** ~100₽/месяц (было 1,676₽/месяц на VM, экономия 94%)

## 🚀 Быстрый старт (новый компьютер)

### 1. Клонировать репозиторий

```bash
git clone git@github.com:ваш-username/wordoorio.git
cd wordoorio
```

### 2. Настроить локальное окружение

**Требования:** Python 3.9 (pymorphy2 несовместим с 3.11+)

```bash
# Создать виртуальное окружение (используйте python3.9)
python3.9 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл для локальной разработки
cp .env.example .env
```

Отредактировать `.env`:
```
YANDEX_FOLDER_ID=b1gcdpfvt5vkfn3o9nm1
YANDEX_DICT_API_KEY=ваш_ключ_словаря
```

**Примечание:** `YANDEX_IAM_TOKEN` не нужен для Serverless Container (автоматически через Metadata Service). Для локальной разработки можно получить через `yc iam create-token`.

### 3. Проверить работу локально

```bash
# Запустить локальный сервер
python web_app.py

# Открыть в браузере
open http://localhost:8080
```

## 🔧 Настройка деплоя (первый раз)

### 1. Установить Yandex Cloud CLI

```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
source ~/.bashrc  # или ~/.zshrc
```

### 2. Авторизоваться в Yandex Cloud

```bash
yc init
```

Выбрать cloud и folder из списка.

### 3. Проверить существующие ресурсы

```bash
# Service Account
yc iam service-account list
# → github-wordoorio (aje3bsioau9v6s0n5b6s)

# Container Registry
yc container registry list
# → wordoorio-registry (crp1mj4p9ro0clhe5t61)

# Serverless Container
yc serverless container list
# → wordoorio (bbaktbcb9dkuurcp862u)

# API Gateway
yc serverless api-gateway list
# → wordoorio-gateway (d5df6n4qui53415eisff)

# SSL Certificate
yc certificate-manager certificate list
# → wordoorio-cert (fpq05g6igphsjir09205)

# Keep-Alive Function
yc serverless function list
# → wordoorio-keep-alive (d4e7l7d8eladv5eivkor)
```

Все ресурсы уже созданы и настроены. Новые создавать не нужно.

### 4. Настроить GitHub Secrets

Если GitHub Secrets уже настроены — пропустить этот шаг.

#### 4.1. Создать Service Account Key

```bash
# Создать новый ключ
yc iam key create \
  --service-account-name github-wordoorio \
  --output sa-key.json

# Закодировать в base64
cat sa-key.json | base64
```

Скопировать вывод base64 строки.

#### 4.2. Добавить Secrets в GitHub

Перейти в Settings → Secrets and variables → Actions → New repository secret

Добавить 3 секрета:

1. **YANDEX_CLOUD_KEY**
   - Value: `<base64 строка из предыдущего шага>`

2. **YANDEX_CLOUD_ID**
   - Value: `b1g5sgin5ubfvtkrvjft`

3. **YANDEX_FOLDER_ID**
   - Value: `b1gcdpfvt5vkfn3o9nm1`

#### 4.3. Удалить файл ключа

```bash
rm sa-key.json
```

**⚠️ ВАЖНО:** Никогда не коммитить `sa-key.json` в репозиторий!

## 📝 Деплой изменений

### Автоматический деплой

```bash
git add .
git commit -m "Ваше сообщение"
git push origin main
```

GitHub Actions автоматически:
1. Соберет Docker образ
2. Загрузит в Container Registry
3. Обновит Serverless Container
4. Сайт будет доступен через 2-3 минуты

### Проверить статус деплоя

1. Открыть GitHub → Actions → Deploy to Yandex Cloud Serverless Container
2. Посмотреть логи последнего запуска

### Проверить сайт

```bash
curl -I https://wordoorio.ru
# Должен вернуть HTTP/2 200
```

## 🔍 Отладка

### Проблема: GitHub Actions падает с ошибкой

**Проверить логи:**
1. GitHub → Actions → последний запуск
2. Раскрыть упавший шаг
3. Прочитать ошибку

**Частые ошибки:**

1. **Permission denied в Registry**
   ```bash
   # Добавить права
   yc container registry add-access-binding wordoorio-registry \
     --service-account-id aje3bsioau9v6s0n5b6s \
     --role container-registry.images.pusher
   ```

2. **Service account not available**
   ```bash
   # Добавить право использовать себя
   yc iam service-account add-access-binding aje3bsioau9v6s0n5b6s \
     --service-account-id aje3bsioau9v6s0n5b6s \
     --role iam.serviceAccounts.user
   ```

### Проблема: Токены Yandex GPT не работают

**Проверка:** IAM токены теперь обновляются автоматически через Metadata Service.

**Если не работает:**
1. Проверить, что Service Account привязан к контейнеру
2. Проверить логи контейнера:
   ```bash
   yc logging read --folder-id=b1gcdpfvt5vkfn3o9nm1 --limit 50
   ```

### Проблема: Сайт возвращает 502/503

**Причина:** Контейнер еще запускается (холодный старт 3-5 секунд).

**Решение:** Подождать или проверить логи:
```bash
yc logging read --folder-id=b1gcdpfvt5vkfn3o9nm1 --limit 50
```

### Проблема: "module 'inspect' has no attribute 'getargspec'"

**Причина:** pymorphy2 несовместим с Python 3.11+ (использует устаревший API).

**Симптомы:**
- Анализ возвращает 0 хайлайтов
- В логах: `❌ Ошибка парсинга v2_dual ответа: module 'inspect' has no attribute 'getargspec'`
- Yandex GPT работает, но результаты не парсятся

**Решение:** Использовать Python 3.9 в Dockerfile:
```dockerfile
FROM python:3.9-slim  # НЕ 3.11!
```

**ВАЖНО:** Python 3.9 обязателен для совместимости с pymorphy2. Не обновляйте до 3.11+!

## 🔐 Безопасность

### GitHub Secrets

- ✅ Используются для хранения чувствительных данных
- ✅ Не видны в логах
- ✅ Шифруются GitHub

### Service Account Permissions

Минимальные необходимые права для `github-wordoorio`:
- `container-registry.images.pusher` - загрузка образов
- `serverless.containers.admin` - управление контейнерами
- `iam.serviceAccounts.user` - использование себя как SA контейнера
- `ai.languageModels.user` - доступ к Yandex GPT API
- `ai.translate.user` - доступ к Yandex Translate API

Команды для добавления прав (если нужно):
```bash
# Права для GPT и Translate
yc resource-manager folder add-access-binding b1gcdpfvt5vkfn3o9nm1 \
  --service-account-id aje3bsioau9v6s0n5b6s \
  --role ai.languageModels.user

yc resource-manager folder add-access-binding b1gcdpfvt5vkfn3o9nm1 \
  --service-account-id aje3bsioau9v6s0n5b6s \
  --role ai.translate.user
```

### IAM Токены

- ✅ Автоматическое обновление через Metadata Service
- ✅ Срок жизни: 12 часов (обновляется при каждом запросе)
- ✅ Не хранятся в переменных окружения контейнера

## 📚 Полезные команды

### Мониторинг

```bash
# Логи контейнера
yc logging read --folder-id=b1gcdpfvt5vkfn3o9nm1 --limit 100

# Статус контейнера
yc serverless container get wordoorio

# Последние ревизии
yc serverless container revision list --container-name wordoorio --limit 5

# Статистика Keep-Alive функции
yc serverless function logs wordoorio-keep-alive --limit 20
```

### Управление

```bash
# Ручной деплой новой ревизии (если нужно)
yc serverless container revision deploy \
  --container-name wordoorio \
  --image cr.yandex/crp1mj4p9ro0clhe5t61/wordoorio-ai:latest \
  --cores 1 \
  --memory 1GB \
  --execution-timeout 180s \
  --service-account-id aje3bsioau9v6s0n5b6s \
  --environment YANDEX_FOLDER_ID=b1gcdpfvt5vkfn3o9nm1

# Проверить домены API Gateway
yc serverless api-gateway get wordoorio-gateway

# Проверить SSL сертификат
yc certificate-manager certificate get wordoorio-cert
```

## 🆘 Контакты

- **Документация Yandex Cloud:** https://cloud.yandex.ru/docs
- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **Docker Docs:** https://docs.docker.com

## 📦 Структура проекта

```
wordoorio/
├── .github/workflows/
│   └── deploy.yml              # GitHub Actions workflow
├── core/
│   └── yandex_ai_client.py     # Metadata Service для токенов
├── Dockerfile                  # Docker образ
├── requirements.txt            # Python зависимости
├── web_app.py                  # Flask приложение
├── api-gateway.yaml            # Спецификация API Gateway
└── SERVERLESS_DEPLOYMENT.md    # Эта документация
```

## ✅ Чеклист для нового разработчика

- [ ] Склонировать репозиторий
- [ ] Установить Python 3.9 (НЕ 3.11+, pymorphy2 несовместим!)
- [ ] Создать venv и установить зависимости
- [ ] Создать .env файл
- [ ] Запустить локально и проверить
- [ ] Установить Yandex Cloud CLI
- [ ] Авторизоваться в YC (yc init)
- [ ] Проверить доступ к ресурсам (yc serverless container list)
- [ ] Сделать изменения и push
- [ ] Проверить деплой в GitHub Actions
- [ ] Проверить сайт https://wordoorio.ru

---

**Версия:** 1.0
**Дата:** 2025-12-10
**Миграция:** VM → Serverless Container
**Экономия:** 1,576₽/мес (94%)
