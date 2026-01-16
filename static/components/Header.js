/**
 * Header Component v2.0
 *
 * Unified header with:
 * - Logo + Navigation on the left
 * - Auth dropdown on the right
 *
 * @version 2.0.0
 */

/**
 * Create header HTML
 * @param {Object} user - Current user (null if not authenticated)
 * @returns {string} HTML header
 */
function createUnifiedHeader(user = null) {
    // Auth section - dropdown or login button
    let authSection = '';

    if (user) {
        const displayName = user.username || 'User';
        authSection = `
            <div class="auth-section" id="authSection">
                <button class="user-trigger" type="button" onclick="toggleUserMenu()">
                    ${displayName}
                    <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 9l6 6 6-6"/>
                    </svg>
                </button>
                <div class="user-menu" id="userMenu">
                    <a href="#" class="user-menu-item" onclick="handleLogout(); return false;">Выйти</a>
                </div>
            </div>
        `;
    } else {
        authSection = `
            <div class="auth-section">
                <a href="/login" class="login-btn">Войти</a>
            </div>
        `;
    }

    return `
        <header class="site-header">
            <div class="header-left">
                <a href="/" class="logo-link">
                    <img src="/static/images/wordoorio-logo.svg" alt="Wordoorio" class="logo-img">
                </a>
                <nav class="site-nav">
                    <a href="/my-highlights" class="nav-item">Хайлайты</a>
                    <a href="/dictionary" class="nav-item">Словарь</a>
                    <a href="/training" class="nav-item">Тренировка</a>
                </nav>
            </div>
            ${authSection}
        </header>
    `;
}

/**
 * Header styles
 * @returns {string} CSS styles
 */
function getUnifiedHeaderStyles() {
    return `
        /* ===== SITE HEADER v2.0 ===== */
        .site-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 0;
            margin-bottom: 24px;
            max-width: var(--container-max-width, 1000px);
            margin-left: auto;
            margin-right: auto;
            padding-left: var(--container-padding, 20px);
            padding-right: var(--container-padding, 20px);
        }

        /* Left section: Logo + Nav */
        .header-left {
            display: flex;
            align-items: center;
            gap: 24px;
        }

        /* Logo */
        .logo-link {
            display: block;
            text-decoration: none;
            transition: transform 0.2s ease;
            flex-shrink: 0;
        }

        .logo-link:hover {
            transform: scale(1.05);
        }

        .logo-img {
            width: 72px;
            height: 72px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
        }

        /* Navigation */
        .site-nav {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .nav-item {
            color: rgba(255, 255, 255, 0.85);
            text-decoration: none;
            font-size: 0.9375rem;
            font-weight: 500;
            transition: var(--transition-base, all 0.2s ease);
            padding: 4px 0;
            position: relative;
        }

        .nav-item:hover {
            color: #ffffff;
        }

        .nav-item::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 2px;
            background: rgba(255, 255, 255, 0.5);
            transition: width 0.2s ease;
        }

        .nav-item:hover::after {
            width: 100%;
        }

        /* ===== AUTH SECTION ===== */
        .auth-section {
            position: relative;
        }

        /* User dropdown trigger */
        .user-trigger {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: var(--radius-pill, 999px);
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition-base, all 0.2s ease);
        }

        .user-trigger:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }

        .user-trigger .dropdown-arrow {
            width: 14px;
            height: 14px;
            transition: transform 0.2s ease;
        }

        .auth-section.open .user-trigger .dropdown-arrow {
            transform: rotate(180deg);
        }

        /* Dropdown menu */
        .user-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: #ffffff;
            border-radius: var(--radius-md, 12px);
            box-shadow: var(--shadow-lg, 0 10px 20px rgba(0, 0, 0, 0.12));
            min-width: 140px;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-8px);
            transition: all 0.2s ease;
            z-index: var(--z-dropdown, 10);
            overflow: hidden;
        }

        .auth-section.open .user-menu {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .user-menu-item {
            display: block;
            padding: 12px 16px;
            color: var(--color-text-secondary, #4a5568);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: background 0.15s ease;
        }

        .user-menu-item:hover {
            background: var(--color-bg-light, #f7fafc);
            color: var(--color-text-primary, #2d3748);
        }

        /* Login button (not authenticated) */
        .login-btn {
            display: inline-block;
            padding: 10px 20px;
            background: var(--gradient-primary, linear-gradient(135deg, #4CAF50 0%, #45a049 100%));
            color: #ffffff;
            text-decoration: none;
            border-radius: var(--radius-md, 12px);
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-button, 0 4px 12px rgba(76, 175, 80, 0.3));
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-button-hover, 0 6px 16px rgba(76, 175, 80, 0.4));
            color: #ffffff;
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 640px) {
            .site-header {
                padding: 12px 16px;
                margin-bottom: 20px;
            }

            .header-left {
                gap: 16px;
            }

            .logo-img {
                width: 52px;
                height: 52px;
            }

            .site-nav {
                gap: 12px;
            }

            .nav-item {
                font-size: 0.8125rem;
            }

            .user-trigger {
                padding: 6px 12px;
                font-size: 0.8125rem;
            }

            .login-btn {
                padding: 8px 16px;
                font-size: 0.8125rem;
            }
        }

        @media (max-width: 480px) {
            .header-left {
                gap: 12px;
            }

            .logo-img {
                width: 44px;
                height: 44px;
            }

            .site-nav {
                gap: 8px;
            }

            .nav-item {
                font-size: 0.75rem;
            }
        }

        /* ===== NOTIFICATION ===== */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }
    `;
}

/**
 * Toggle user dropdown menu
 */
function toggleUserMenu() {
    const authSection = document.getElementById('authSection');
    if (authSection) {
        authSection.classList.toggle('open');
    }
}

/**
 * Close dropdown when clicking outside
 */
function setupDropdownClose() {
    document.addEventListener('click', function(e) {
        const authSection = document.getElementById('authSection');
        if (authSection && !authSection.contains(e.target)) {
            authSection.classList.remove('open');
        }
    });
}

/**
 * Initialize header (insert into DOM)
 * @param {string} containerId - Container ID for header
 */
async function initUnifiedHeader(containerId = 'header-container') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    // Add styles if not already added
    if (!document.getElementById('unified-header-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'unified-header-styles';
        styleEl.innerHTML = getUnifiedHeaderStyles();
        document.head.appendChild(styleEl);
    }

    // Check current user via API
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

    // Render header
    container.innerHTML = createUnifiedHeader(currentUser);

    // Setup dropdown close on outside click
    setupDropdownClose();
}

/**
 * Handle logout
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
 * Show notification
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

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createUnifiedHeader,
        getUnifiedHeaderStyles,
        initUnifiedHeader
    };
}
