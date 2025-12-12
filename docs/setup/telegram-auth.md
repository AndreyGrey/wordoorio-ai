# Настройка Telegram аутентификации

Wordoorio использует Telegram Login Widget для аутентификации пользователей. Это руководство описывает процесс настройки Telegram бота и конфигурации приложения.

## Зачем нужен Telegram бот?

Telegram Login Widget использует криптографическую подпись (HMAC-SHA256) для верификации данных пользователя. Без корректно настроенного `TELEGRAM_BOT_TOKEN` авторизация будет возвращать ошибку `Invalid Telegram signature`.

## Шаг 1: Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота:
   - Введите имя бота (например, "Wordoorio Auth Bot")
   - Введите username бота (например, "wordoorio_auth_bot")
4. BotFather вернет вам **BOT TOKEN** в формате: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
5. Сохраните токен и username бота

## Шаг 2: Локальная разработка

### Настройка .env файла

1. Скопируйте `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Откройте `.env` и добавьте ваши данные:
   ```env
   # Yandex Cloud IAM токен (обязательно для работы)
   YANDEX_IAM_TOKEN=ваш_yandex_iam_токен

   # Yandex Cloud Folder ID (обязательно для работы)
   YANDEX_FOLDER_ID=ваш_folder_id

   # Telegram Bot для авторизации (обязательно)
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_BOT_USERNAME=wordoorio_auth_bot
   ```

3. Сохраните файл

### Проверка работы

Запустите приложение локально:
```bash
python3 web_app.py
```

Откройте браузер и попробуйте авторизоваться через Telegram. Вы должны увидеть успешную авторизацию без ошибок.

## Шаг 3: Production деплоймент (Yandex Cloud)

### Добавление секрета в GitHub

Для деплоймента через GitHub Actions необходимо добавить `TELEGRAM_BOT_TOKEN` в секреты репозитория:

1. Откройте ваш репозиторий на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Заполните поля:
   - **Name**: `TELEGRAM_BOT_TOKEN`
   - **Secret**: вставьте ваш токен (например, `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Нажмите **Add secret**

### Конфигурация GitHub Actions

Workflow файл `.github/workflows/deploy.yml` уже настроен для передачи токена в контейнер:

```yaml
- name: Update Serverless Container
  run: |
    yc serverless container revision deploy \
      --container-name ${{ env.CONTAINER_NAME }} \
      --image cr.yandex/${{ env.REGISTRY_ID }}/${{ env.IMAGE_NAME }}:latest \
      --cores 1 \
      --memory 1GB \
      --execution-timeout 180s \
      --service-account-id ${{ env.SERVICE_ACCOUNT_ID }} \
      --environment YANDEX_FOLDER_ID=${{ secrets.YANDEX_FOLDER_ID }},TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}
```

После добавления секрета, следующий push в `main` ветку автоматически задеплоит приложение с токеном.

## Архитектура проверки подписи

### Как работает верификация

Код верификации находится в `core/auth_manager.py:37-56`:

```python
def verify_telegram_auth(self, auth_data: Dict) -> bool:
    """
    Проверяет подпись данных от Telegram Login Widget
    """
    # Извлекаем hash из данных
    received_hash = auth_data.get('hash')
    if not received_hash:
        return False

    # Проверяем наличие BOT_TOKEN
    if not self.bot_token:
        print("⚠️  BOT_TOKEN не найден в .env")
        return False

    # Создаем строку для проверки (все поля кроме hash)
    check_fields = {k: v for k, v in auth_data.items() if k != 'hash' and v is not None}
    check_string = '\n'.join(f'{k}={v}' for k, v in sorted(check_fields.items()))

    # Вычисляем secret_key = SHA256(bot_token)
    secret_key = hashlib.sha256(self.bot_token.encode()).digest()

    # Вычисляем HMAC-SHA256
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    # Сравниваем хеши
    return hmac.compare_digest(calculated_hash, received_hash)
```

### Процесс авторизации

1. Пользователь нажимает на Telegram Login Widget
2. Telegram отправляет данные пользователя с HMAC подписью в callback
3. Frontend отправляет данные на `/api/auth/telegram`
4. Сервер проверяет подпись используя `TELEGRAM_BOT_TOKEN`
5. Если подпись валидна, создается сессия пользователя
6. Frontend перезагружает страницу для обновления UI

## Troubleshooting

### Ошибка "Invalid Telegram signature"

**Проблема:** При попытке авторизации появляется уведомление с ошибкой `Invalid Telegram signature`.

**Причины:**
1. `TELEGRAM_BOT_TOKEN` не установлен в `.env` (локально)
2. `TELEGRAM_BOT_TOKEN` не добавлен в GitHub Secrets (production)
3. Неправильный токен (не соответствует боту в Login Widget)

**Решение:**
1. Проверьте, что токен правильно указан в `.env` файле
2. Убедитесь, что токен добавлен в GitHub Secrets
3. Проверьте, что username бота в коде совпадает с созданным ботом
4. Проверьте логи сервера для деталей ошибки

### Логи показывают "BOT_TOKEN не найден"

**Проблема:** В логах приложения видно `⚠️ BOT_TOKEN не найден в .env`.

**Решение:**
1. Убедитесь, что файл `.env` существует в корне проекта
2. Проверьте, что переменная `TELEGRAM_BOT_TOKEN` указана в `.env`
3. Перезапустите приложение после изменения `.env`

### Production: авторизация не работает после деплоя

**Проблема:** Локально все работает, но в production авторизация не проходит.

**Решение:**
1. Проверьте, что `TELEGRAM_BOT_TOKEN` добавлен в GitHub Secrets
2. Проверьте логи Yandex Cloud Serverless Container:
   ```bash
   ~/yandex-cloud/bin/yc logging read --group-id=<your-log-group-id>
   ```
3. Убедитесь, что последний деплой включал обновленный `.github/workflows/deploy.yml`

## Проверка конфигурации

### Локальная проверка

Запустите Python интерпретатор:
```python
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"Token loaded: {token[:10]}..." if token else "Token NOT found")
```

Должно вывести: `Token loaded: 1234567890...`

### Production проверка

Проверьте переменные окружения контейнера:
```bash
~/yandex-cloud/bin/yc serverless container revision get \
  --container-name wordoorio \
  --format json | grep TELEGRAM_BOT_TOKEN
```

Должно показать, что переменная установлена.

## Файлы конфигурации

Список файлов, связанных с Telegram аутентификацией:

- `.env.example` - шаблон переменных окружения
- `.env` - ваш локальный файл конфигурации (не в git)
- `core/auth_manager.py` - логика верификации Telegram подписи
- `web_app.py:773-830` - эндпоинт `/api/auth/telegram`
- `static/js/Auth.js` - клиентский код авторизации
- `templates/header.html` - Telegram Login Widget
- `.github/workflows/deploy.yml` - конфигурация CI/CD

---

*Последнее обновление: December 2024*
