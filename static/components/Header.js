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
 * @returns {string} HTML header
 */
function createUnifiedHeader() {
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
    `;
}

/**
 * Инициализировать header (вставить в DOM)
 * @param {string} containerId - ID контейнера для header
 */
function initUnifiedHeader(containerId = 'header-container') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    // Вставляем HTML
    container.innerHTML = createUnifiedHeader();

    // Добавляем стили если еще не добавлены
    if (!document.getElementById('unified-header-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'unified-header-styles';
        styleEl.innerHTML = getUnifiedHeaderStyles();
        document.head.appendChild(styleEl);
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createUnifiedHeader,
        getUnifiedHeaderStyles,
        initUnifiedHeader
    };
}
