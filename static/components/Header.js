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
        // Пользователь авторизован - показываем имя и кнопку выхода
        const displayName = user.username || 'User';

        authSection = `
            <div class="user-info">
                <span class="user-name">${displayName}</span>
                <button class="logout-btn" onclick="handleLogout()">Выйти</button>
            </div>
        `;
    } else {
        // Пользователь не авторизован - показываем кнопку входа
        authSection = `
            <a href="/login" class="login-btn">Войти</a>
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

        /* Login button */
        .login-btn {
            padding: 10px 24px;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 15px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
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

    // Проверяем текущего пользователя через API
    let currentUser = null;
    try {
        const response = await fetch('/api/auth/current', {
            credentials: 'same-origin'
        });
        const data = await response.json();
        if (data.success && data.user) {
            currentUser = data.user;
        }
    } catch (error) {
        console.error('Failed to check auth:', error);
    }

    // Рендерим header
    container.innerHTML = createUnifiedHeader(currentUser);
}

/**
 * Обработчик выхода из системы
 */
async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'same-origin'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Вы вышли из системы');
            // Перезагружаем страницу чтобы обновить header
            setTimeout(() => window.location.reload(), 500);
        } else {
            showNotification('Ошибка выхода', 'error');
        }
    } catch (error) {
        console.error('Logout error:', error);
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

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createUnifiedHeader,
        getUnifiedHeaderStyles,
        initUnifiedHeader
    };
}
