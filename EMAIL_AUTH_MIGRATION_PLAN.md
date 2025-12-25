# 📧 План миграции на Email-авторизацию

## Цель
Заменить авторизацию через Telegram на passwordless email-авторизацию с 5-значным кодом.

---

## 1. Новая схема базы данных

### 1.1 Изменения в таблице `users`

**Было:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    photo_url TEXT,
    auth_date INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    last_login_at TEXT NOT NULL
)
```

**Станет:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    last_login_at TEXT NOT NULL,

    -- Опционально (для совместимости со старыми данными)
    telegram_id INTEGER UNIQUE,
    first_name TEXT,
    last_name TEXT
)
```

### 1.2 Новая таблица `auth_codes`

```sql
CREATE TABLE auth_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    code TEXT NOT NULL,           -- 5-значный код (например, "12345")
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,     -- Код действителен 10 минут
    used BOOLEAN DEFAULT 0,       -- Использован ли код
    ip_address TEXT,              -- IP для защиты от злоупотреблений

    INDEX idx_email (email),
    INDEX idx_code (code),
    INDEX idx_expires_at (expires_at)
)
```

**Логика:**
- Код действителен 10 минут
- После использования помечается как `used = 1`
- Каждый email может иметь только 1 активный код (старые автоматически инвалидируются)
- Rate limiting: не более 3 кодов в час для одного email

---

## 2. Backend (Python)

### 2.1 Новый модуль `/core/email_service.py`

**Функционал:**
- Отправка email через SMTP
- Генерация HTML шаблона письма с кодом
- Rate limiting (защита от спама)

```python
class EmailService:
    def send_auth_code(email: str, code: str) -> bool
    def generate_code() -> str  # Генерирует 5-значный код
```

**SMTP конфигурация (.env):**
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=Wordoorio <noreply@wordoorio.ru>
```

### 2.2 Переписать `/core/auth_manager.py`

**Новые методы:**

```python
class AuthManager:
    # Шаг 1: Генерация и отправка кода
    def send_verification_code(email: str, ip_address: str) -> Dict
        # 1. Проверить rate limiting (не более 3 кодов в час)
        # 2. Сгенерировать 5-значный код
        # 3. Сохранить в таблицу auth_codes
        # 4. Отправить email через EmailService
        # Возвращает: {'success': True/False, 'error': ...}

    # Шаг 2: Проверка кода и авторизация
    def verify_code(email: str, code: str) -> Dict
        # 1. Найти код в auth_codes
        # 2. Проверить что код не истек (expires_at > now)
        # 3. Проверить что код не использован (used = 0)
        # 4. Пометить код как использованный
        # 5. Создать/обновить пользователя в users
        # 6. Вернуть user_id
        # Возвращает: {'success': True/False, 'user_id': ...}

    # Вспомогательные методы
    def get_user_by_email(email: str) -> Optional[Dict]
    def create_or_update_user(email: str) -> int
    def cleanup_expired_codes() -> None  # Удалить истекшие коды
    def check_rate_limit(email: str, ip_address: str) -> bool
```

**Удалить:**
- `verify_telegram_auth()`
- `get_user_by_telegram_id()`

### 2.3 Обновить `/web_app.py` - новые роуты

**Удалить:**
```python
@app.route('/api/auth/telegram', methods=['POST'])
@app.route('/api/auth/config', methods=['GET'])
```

**Добавить:**
```python
@app.route('/api/auth/send-code', methods=['POST'])
def send_auth_code():
    """
    Отправить код на email

    Body: { "email": "user@example.com" }
    Response: { "success": true, "message": "Code sent to email" }
    """
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    # Валидация email
    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Invalid email'}), 400

    # Получаем IP для rate limiting
    ip_address = request.remote_addr

    # Отправляем код
    auth = AuthManager()
    result = auth.send_verification_code(email, ip_address)

    if not result['success']:
        return jsonify(result), 429 if 'rate limit' in result.get('error', '') else 400

    return jsonify({'success': True, 'message': 'Code sent to your email'})


@app.route('/api/auth/verify-code', methods=['POST'])
def verify_auth_code():
    """
    Проверить код и авторизоваться

    Body: { "email": "user@example.com", "code": "12345" }
    Response: { "success": true, "user": {...} }
    """
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()

    # Валидация
    if not email or not code:
        return jsonify({'success': False, 'error': 'Email and code required'}), 400

    # Проверяем код
    auth = AuthManager()
    result = auth.verify_code(email, code)

    if not result['success']:
        return jsonify(result), 401

    # Сохраняем в сессию
    user_id = result['user_id']
    session['user_id'] = user_id
    session['email'] = email

    # Возвращаем данные пользователя
    user = auth.get_user_by_id(user_id)
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'created_at': user['created_at']
        }
    })
```

**Оставить без изменений:**
```python
@app.route('/api/auth/current', methods=['GET'])  # Только изменить формат ответа
@app.route('/api/auth/logout', methods=['POST'])  # Без изменений
```

---

## 3. Frontend (JavaScript)

### 3.1 Переписать `/static/js/Auth.js`

**Удалить:**
- `handleTelegramAuth()`
- `window.onTelegramAuth`
- `window.devLogin()`

**Новые методы:**

```javascript
class Auth {
    // Шаг 1: Отправить код на email
    async sendCode(email) {
        const response = await fetch('/api/auth/send-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to send code');
        }

        return data;
    }

    // Шаг 2: Проверить код и авторизоваться
    async verifyCode(email, code) {
        const response = await fetch('/api/auth/verify-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Invalid code');
        }

        // Обновляем текущего пользователя
        this.currentUser = data.user;
        this.notifyAuthChange();

        return data.user;
    }

    // Остальные методы без изменений
    async getCurrentUser() { ... }
    async logout() { ... }
    isAuthenticated() { ... }
}
```

### 3.2 Переписать `/static/components/Header.js`

**Удалить:**
- `loadTelegramLoginWidget()`
- Ссылки на Telegram Widget

**Новый UI:**

```javascript
function createUnifiedHeader(user) {
    if (user) {
        // Авторизован - показываем email и кнопку выхода
        return `
            <div class="header-auth">
                <span class="user-email">${user.email}</span>
                <button onclick="handleLogout()" class="logout-btn">Выйти</button>
            </div>
        `;
    } else {
        // Не авторизован - показываем форму для входа
        return `
            <div class="auth-form" id="auth-form">
                <input
                    type="email"
                    id="email-input"
                    placeholder="Введите email"
                    class="email-input"
                />
                <button onclick="handleSendCode()" id="send-code-btn" class="auth-btn">
                    Получить код
                </button>

                <!-- Форма для ввода кода (скрыта по умолчанию) -->
                <div id="code-form" style="display: none;">
                    <input
                        type="text"
                        id="code-input"
                        placeholder="Введите код"
                        maxlength="5"
                        class="code-input"
                    />
                    <button onclick="handleVerifyCode()" id="verify-code-btn" class="auth-btn">
                        Войти
                    </button>
                </div>

                <div id="auth-message" class="auth-message"></div>
            </div>
        `;
    }
}

async function handleSendCode() {
    const email = document.getElementById('email-input').value.trim();
    const messageEl = document.getElementById('auth-message');
    const sendBtn = document.getElementById('send-code-btn');

    if (!email || !email.includes('@')) {
        messageEl.textContent = 'Введите корректный email';
        messageEl.className = 'auth-message error';
        return;
    }

    try {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Отправка...';

        await window.auth.sendCode(email);

        // Показываем форму для ввода кода
        document.getElementById('code-form').style.display = 'block';
        document.getElementById('email-input').disabled = true;
        sendBtn.textContent = 'Код отправлен';

        messageEl.textContent = 'Код отправлен на ' + email;
        messageEl.className = 'auth-message success';

        // Фокус на поле кода
        document.getElementById('code-input').focus();

    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'auth-message error';
        sendBtn.disabled = false;
        sendBtn.textContent = 'Получить код';
    }
}

async function handleVerifyCode() {
    const email = document.getElementById('email-input').value.trim();
    const code = document.getElementById('code-input').value.trim();
    const messageEl = document.getElementById('auth-message');
    const verifyBtn = document.getElementById('verify-code-btn');

    if (!code || code.length !== 5) {
        messageEl.textContent = 'Введите 5-значный код';
        messageEl.className = 'auth-message error';
        return;
    }

    try {
        verifyBtn.disabled = true;
        verifyBtn.textContent = 'Проверка...';

        const user = await window.auth.verifyCode(email, code);

        // Успешная авторизация - обновляем header
        messageEl.textContent = 'Успешно!';
        messageEl.className = 'auth-message success';

        // Header обновится автоматически через onAuthChange

    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.className = 'auth-message error';
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Войти';
    }
}
```

### 3.3 Добавить CSS для формы (в `/static/css/`)

```css
.auth-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 300px;
}

.email-input,
.code-input {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.auth-btn {
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.auth-btn:hover {
    background: #0056b3;
}

.auth-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.auth-message {
    padding: 8px;
    border-radius: 4px;
    font-size: 13px;
}

.auth-message.success {
    background: #d4edda;
    color: #155724;
}

.auth-message.error {
    background: #f8d7da;
    color: #721c24;
}

.user-email {
    font-weight: 500;
    margin-right: 10px;
}

.logout-btn {
    padding: 6px 12px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
```

---

## 4. Миграция базы данных

### 4.1 Скрипт миграции `/migrate_to_email_auth.py`

```python
#!/usr/bin/env python3
"""
Миграция базы данных с Telegram авторизации на Email авторизацию
"""

import sqlite3
from datetime import datetime

def migrate_database(db_path='wordoorio.db'):
    print("🔄 Начинаем миграцию базы данных...")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 1. Создаем новую таблицу users_new
        print("📋 Создаем новую таблицу users...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT NOT NULL,

                -- Для совместимости со старыми данными
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT
            )
        """)

        # 2. Переносим данные из старой таблицы (опционально)
        # ВАЖНО: У старых пользователей нет email, поэтому:
        # - Либо удаляем старых пользователей
        # - Либо создаем фейковые email (telegram_{telegram_id}@placeholder.local)

        print("📦 Переносим существующих пользователей...")
        cursor.execute("""
            INSERT INTO users_new (id, email, created_at, last_login_at, telegram_id, first_name, last_name)
            SELECT
                id,
                'telegram_' || telegram_id || '@placeholder.local' as email,
                created_at,
                last_login_at,
                telegram_id,
                first_name,
                last_name
            FROM users
        """)

        migrated_count = cursor.rowcount
        print(f"✅ Перенесено пользователей: {migrated_count}")

        # 3. Удаляем старую таблицу и переименовываем новую
        print("🔄 Заменяем таблицу users...")
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # 4. Создаем таблицу auth_codes
        print("📋 Создаем таблицу auth_codes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used BOOLEAN DEFAULT 0,
                ip_address TEXT
            )
        """)

        # 5. Создаем индексы
        print("🔍 Создаем индексы...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_codes_email ON auth_codes(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_codes_code ON auth_codes(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_codes_expires ON auth_codes(expires_at)")

        conn.commit()

    print("✅ Миграция завершена успешно!")
    print(f"⚠️  Внимание: Старым пользователям назначены placeholder email-адреса")
    print(f"   Они смогут войти по новой email-авторизации")

if __name__ == "__main__":
    migrate_database()
```

---

## 5. Обновить Telegram Bot (опционально)

### 5.1 `/telegram_bot.py`

Telegram бот можно оставить как **дополнительную фичу**, но убрать привязку к авторизации.

**Вариант 1:** Попросить пользователя связать Telegram с email:
```
Бот: "Для использования бота авторизуйтесь на сайте wordoorio.ru и свяжите свой Telegram аккаунт"
```

**Вариант 2:** Полностью отключить бота до реализации связки.

---

## 6. Конфигурация email (.env)

Добавить в `.env`:

```bash
# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=Wordoorio <noreply@wordoorio.ru>

# Rate limiting
AUTH_CODE_RATE_LIMIT=3        # Макс кодов в час на 1 email
AUTH_CODE_EXPIRATION=600      # Время жизни кода в секундах (10 минут)
```

Для Gmail нужно создать **App Password**:
1. Google Account → Security → 2-Step Verification
2. App Passwords → Generate password
3. Использовать этот пароль вместо основного

---

## 7. Безопасность

### 7.1 Rate Limiting
- Не более 3 кодов в час для одного email
- Не более 10 кодов в час с одного IP

### 7.2 Защита от брутфорса
- После 5 неудачных попыток ввода кода - блокировка на 15 минут
- Код действителен только 10 минут

### 7.3 Валидация email
- Проверка формата email (regex)
- Проверка существования домена (опционально)

### 7.4 HTTPS
- В продакшене обязательно использовать HTTPS
- Защита от перехвата кода

---

## 8. План развертывания

### Этап 1: Разработка и тестирование
1. ✅ Спроектировать схему БД
2. ⏳ Настроить email сервис
3. ⏳ Создать модуль отправки email
4. ⏳ Переписать auth_manager.py
5. ⏳ Обновить web_app.py роуты
6. ⏳ Переписать фронтенд Auth.js и Header.js
7. ⏳ Локальное тестирование

### Этап 2: Миграция БД
1. ⏳ Создать скрипт миграции
2. ⏳ Сделать backup БД
3. ⏳ Запустить миграцию
4. ⏳ Проверить целостность данных

### Этап 3: Деплой
1. ⏳ Обновить .env на сервере (SMTP настройки)
2. ⏳ Деплой нового кода
3. ⏳ Запустить миграцию на проде
4. ⏳ Тестирование на проде

### Этап 4: Мониторинг
1. ⏳ Проверить логи отправки email
2. ⏳ Мониторинг ошибок авторизации
3. ⏳ Сбор feedback от пользователей

---

## 9. Rollback план

Если что-то пойдет не так:

1. **Откатить код** до предыдущей версии
2. **Восстановить БД** из backup
3. **Вернуть Telegram авторизацию**

Backup БД перед миграцией:
```bash
cp wordoorio.db wordoorio.db.backup_$(date +%Y%m%d_%H%M%S)
```

---

## 10. Тестирование

### Тест-кейсы:

1. **Успешная авторизация:**
   - Ввести email → получить код → ввести код → авторизован

2. **Неверный email:**
   - Ввести невалидный email → ошибка

3. **Rate limiting:**
   - Запросить 4 кода за час → 4-й запрос отклонен

4. **Истекший код:**
   - Подождать 11 минут → код не работает

5. **Использованный код:**
   - Использовать код → попытаться использовать повторно → ошибка

6. **Неверный код:**
   - Ввести неправильный код → ошибка
   - После 5 попыток → блокировка

7. **Сессия:**
   - Авторизоваться → обновить страницу → остаться авторизованным

8. **Logout:**
   - Выйти → session очищена

---

## Оценка времени

- **Бэкенд (Python):** ~4-6 часов
- **Фронтенд (JS/HTML/CSS):** ~3-4 часа
- **Миграция БД:** ~1-2 часа
- **Тестирование:** ~2-3 часа
- **Деплой:** ~1-2 часа

**Итого:** ~11-17 часов работы

---

## Вопросы для уточнения

1. ✅ **Passwordless** (только код) или с паролем? → **Только код**
2. Какой email сервис использовать? (Gmail, SendGrid, Mailgun, свой SMTP)
3. Нужно ли сохранять старых Telegram пользователей? Или можно удалить?
4. Telegram бот - оставить или полностью убрать?
5. Нужна ли верификация email (подтверждение что email реальный)?

---

**Готово к реализации!** 🚀
