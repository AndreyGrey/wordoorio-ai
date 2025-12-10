/**
 * 🎨 UNIFIED HEADER COMPONENT
 *
 * Унифицированный header для всех страниц проекта.
 * Логотип + навигация "Мои хайлайты"
 *
 * @version 1.0.0
 */

/**
 * Создать HTML header компонента
 * @param {Object} user - Текущий пользователь (null если не авторизован)
 * @returns {string} HTML header
 */
function createUnifiedHeader(user = null) {
    // Auth button или user info
    let authSection = '';

    if (user) {
        // Пользователь авторизован - показываем аватар и имя
        const displayName = user.first_name || user.username || 'User';
        const defaultAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=39A0B3&color=fff&size=128&bold=true`;
        const photoUrl = user.photo_url || defaultAvatar;

        authSection = `
            <div class="user-info">
                <img src="${photoUrl}" alt="${displayName}" class="user-avatar" />
                <span class="user-name">${displayName}</span>
                <button class="logout-btn" onclick="handleLogout()">Выйти</button>
            </div>
        `;
    } else {
        // Пользователь не авторизован - показываем Telegram Login Widget
        authSection = `
            <div id="telegram-login-container" class="telegram-login-wrapper">
                <!-- Telegram Login Widget будет загружен динамически -->
            </div>
        `;
    }

    return `
        <div class="unified-header">
            <div class="header-content">
                <a href="/" class="logo-link">
                    <img src="/static/images/wordoorio-logo.svg" alt="Wordoorio" class="logo" />
                </a>
                <nav class="header-nav">
                    <a href="/my-highlights" class="nav-link">
                        <span class="nav-icon">📚</span>
                        <span class="nav-text">Мои хайлайты</span>
                    </a>
                    <a href="/dictionary" class="nav-link">
                        <span class="nav-icon">📖</span>
                        <span class="nav-text">Словарь</span>
                    </a>
                    ${authSection}
                </nav>
            </div>
        </div>
    `;
}

/**
 * Стили для unified header
 * @returns {string} CSS styles
 */
function getUnifiedHeaderStyles() {
    return `
        /* ===== UNIFIED HEADER ===== */
        .unified-header {
            background: transparent;
            padding: 20px 0;
            margin-bottom: 30px;
        }

        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .logo-link {
            display: block;
            text-decoration: none;
            transition: transform 0.2s ease;
        }

        .logo-link:hover {
            transform: scale(1.05);
        }

        .logo {
            width: 140px;
            height: 140px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
        }

        .header-nav {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.95);
            color: #2d3748;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 15px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .nav-link:hover {
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }

        .nav-icon {
            font-size: 18px;
        }

        /* Адаптивность */
        @media (max-width: 768px) {
            .header-content {
                padding: 0 16px;
            }

            .logo {
                width: 100px;
                height: 100px;
            }

            .nav-link {
                padding: 8px 16px;
                font-size: 14px;
            }

            .nav-icon {
                font-size: 16px;
            }
        }

        @media (max-width: 480px) {
            .unified-header {
                padding: 16px 0;
                margin-bottom: 24px;
            }

            .logo {
                width: 80px;
                height: 80px;
            }

            .nav-text {
                display: none;
            }

            .nav-link {
                padding: 10px;
                border-radius: 10px;
            }

            .nav-icon {
                font-size: 20px;
            }
        }

        /* ===== AUTH SECTION ===== */

        /* Telegram Login Widget wrapper */
        .telegram-login-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* User info section */
        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #FF9966;
        }

        .user-name {
            font-weight: 600;
            color: #2d3748;
            font-size: 15px;
        }

        .logout-btn {
            padding: 6px 14px;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            color: #718096;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .logout-btn:hover {
            background: #edf2f7;
            border-color: #cbd5e0;
            color: #4a5568;
        }

        @media (max-width: 768px) {
            .user-info {
                gap: 8px;
                padding: 6px 12px;
            }

            .user-avatar {
                width: 32px;
                height: 32px;
            }

            .user-name {
                font-size: 14px;
            }

            .logout-btn {
                padding: 5px 10px;
                font-size: 12px;
            }
        }

        @media (max-width: 480px) {
            .user-name {
                display: none;
            }

            .logout-btn {
                padding: 6px 10px;
                font-size: 11px;
            }
        }
    `;
}

/**
 * Инициализировать header (вставить в DOM)
 * @param {string} containerId - ID контейнера для header
 */
async function initUnifiedHeader(containerId = 'header-container') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    // Добавляем стили если еще не добавлены
    if (!document.getElementById('unified-header-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'unified-header-styles';
        styleEl.innerHTML = getUnifiedHeaderStyles();
        document.head.appendChild(styleEl);
    }

    // Проверяем текущего пользователя
    await window.auth.init();
    const currentUser = window.auth.getCurrentUser();

    // Рендерим header с учетом auth state
    container.innerHTML = createUnifiedHeader(currentUser);

    // Если пользователь не авторизован, загружаем Telegram Login Widget
    if (!currentUser) {
        await loadTelegramLoginWidget();
    }

    // Подписываемся на изменения авторизации
    window.auth.onAuthChange((isAuthenticated, user) => {
        console.log('Auth state changed:', isAuthenticated, user);
        container.innerHTML = createUnifiedHeader(user);

        // Если пользователь вышел, загружаем виджет снова
        if (!isAuthenticated) {
            loadTelegramLoginWidget();
        }
    });
}

/**
 * Загрузить Telegram Login Widget
 */
async function loadTelegramLoginWidget() {
    try {
        // Проверяем, что мы не на localhost (виджет не работает локально)
        const isLocalhost = window.location.hostname === 'localhost' ||
                          window.location.hostname === '127.0.0.1' ||
                          window.location.hostname.includes('192.168');

        if (isLocalhost) {
            console.log('🔧 DEV MODE: Telegram Login Widget не загружается на localhost. Используйте devLogin() в консоли.');
            const container = document.getElementById('telegram-login-container');
            if (container) {
                container.innerHTML = `
                    <div style="padding: 10px 20px; background: rgba(255,255,255,0.9); border-radius: 12px; color: #4a5568; font-size: 14px; font-weight: 500;">
                        🔧 Dev mode: используйте <code style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">devLogin()</code> в консоли
                    </div>
                `;
            }
            return;
        }

        // Получаем bot_username из API
        const response = await fetch('/api/auth/config');
        const data = await response.json();

        if (!data.success || !data.bot_username) {
            console.error('Bot username not configured');
            return;
        }

        const botUsername = data.bot_username;
        const container = document.getElementById('telegram-login-container');

        if (!container) {
            console.warn('Telegram login container not found');
            return;
        }

        // Создаем скрипт Telegram Login Widget
        const script = document.createElement('script');
        script.src = 'https://telegram.org/js/telegram-widget.js?22';
        script.setAttribute('data-telegram-login', botUsername);
        script.setAttribute('data-size', 'medium');
        script.setAttribute('data-radius', '8');
        script.setAttribute('data-onauth', 'onTelegramAuth(user)');
        script.setAttribute('data-request-access', 'write');
        script.async = true;

        container.innerHTML = '';
        container.appendChild(script);
    } catch (error) {
        console.error('Failed to load Telegram widget:', error);
    }
}

/**
 * Обработчик выхода из системы
 */
async function handleLogout() {
    const result = await window.auth.logout();

    if (result.success) {
        // Header обновится автоматически через onAuthChange callback
        showNotification('Вы вышли из системы');
    } else {
        showNotification('Ошибка выхода', 'error');
    }
}

/**
 * Показать уведомление
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#fed7d7' : '#c6f6d5'};
        color: ${type === 'error' ? '#c53030' : '#22543d'};
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * DEV: Тестовая авторизация (для локальной разработки)
 * Использование: откройте консоль браузера и вызовите devLogin()
 */
async function devLogin() {
    console.log('🔧 DEV MODE: Выполняется тестовая авторизация...');

    // Создаем тестовые данные пользователя
    const testUser = {
        id: 123456789,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser',
        photo_url: 'https://ui-avatars.com/api/?name=Test+User&background=39A0B3&color=fff&size=128&bold=true',
        auth_date: Math.floor(Date.now() / 1000),
        hash: 'dev_mode_no_verification'
    };

    // Используем существующий обработчик
    const result = await window.auth.handleTelegramAuth(testUser);

    if (result.success) {
        console.log('✅ DEV MODE: Авторизация успешна');
        showNotification('Вы успешно авторизованы (DEV MODE)');
    } else {
        console.error('❌ DEV MODE: Ошибка авторизации:', result.error);
        showNotification('Ошибка авторизации: ' + result.error, 'error');
    }
}

// Делаем devLogin доступной глобально для вызова из консоли
window.devLogin = devLogin;

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createUnifiedHeader,
        getUnifiedHeaderStyles,
        initUnifiedHeader
    };
}
