/**
 * 🎯 UNIVERSAL ANALYSIS FORM COMPONENT
 *
 * Универсальная форма для анализа текста с двумя режимами:
 * - YouTube: ввод ссылки на видео
 * - Text: ввод текста напрямую
 *
 * @version 2.0.0
 */

/**
 * Создать HTML формы анализа
 * @param {Object} config - Конфигурация компонента
 * @param {string} config.placeholder - Placeholder для textarea
 * @param {string} config.subtitle - Подзаголовок над формой (опционально)
 * @returns {string} HTML формы
 */
function createAnalysisForm(config = {}) {
    const {
        placeholder = 'Enter English text for analysis...',
        subtitle = ''
    } = config;

    const subtitleHTML = subtitle
        ? `<p class="form-subtitle">${subtitle}</p>`
        : '';

    return `
        <div class="analysis-form">
            <h2 class="form-title">Analyze Text</h2>
            ${subtitleHTML}

            <!-- Переключатель режимов -->
            <div class="mode-tabs">
                <button class="mode-tab active" data-mode="text">Text</button>
                <button class="mode-tab" data-mode="youtube">YouTube</button>
            </div>

            <!-- Режим Text -->
            <div id="text-mode" class="input-mode active">
                <textarea
                    id="textInput"
                    class="form-textarea"
                    placeholder="Paste your English text here..."
                ></textarea>
            </div>

            <!-- Режим YouTube -->
            <div id="youtube-mode" class="input-mode">
                <input
                    type="text"
                    id="youtubeInput"
                    class="form-url-input"
                    placeholder="Paste YouTube video link here..."
                >
            </div>

            <button class="form-button" onclick="analyzeText()">
                WORDOORIO!
            </button>
            <div id="error" class="form-error" style="display: none;"></div>
        </div>
    `;
}

/**
 * Стили для формы анализа
 * @returns {string} CSS styles
 */
function getAnalysisFormStyles() {
    return `
        /* ===== UNIVERSAL ANALYSIS FORM ===== */
        .analysis-form {
            background: white;
            padding: 48px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
            margin-bottom: 32px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .analysis-form:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }

        .form-title {
            color: #1a202c;
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .form-subtitle {
            color: #718096;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 24px;
            line-height: 1.5;
        }

        /* ===== MODE TABS ===== */
        .mode-tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }

        .mode-tab {
            padding: 10px 24px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            background: transparent;
            color: #718096;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .mode-tab:hover {
            border-color: #39A0B3;
            color: #39A0B3;
        }

        .mode-tab.active {
            border-color: #39A0B3;
            color: #39A0B3;
            background: rgba(57, 160, 179, 0.08);
        }

        /* ===== INPUT MODES ===== */
        .input-mode {
            display: none;
        }

        .input-mode.active {
            display: block;
        }

        .form-textarea {
            width: 100%;
            height: 280px;
            padding: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 14px;
            font-size: 16px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            resize: vertical;
            transition: all 0.3s ease;
            line-height: 1.6;
            color: #2d3748;
            background: #fafafa;
        }

        .form-textarea:focus {
            outline: none;
            border-color: #39A0B3;
            background: white;
            box-shadow: 0 0 0 4px rgba(57, 160, 179, 0.08);
        }

        .form-textarea::placeholder {
            color: #a0aec0;
        }

        /* ===== YOUTUBE INPUT ===== */
        .form-url-input {
            width: 100%;
            padding: 18px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 14px;
            font-size: 16px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            transition: all 0.3s ease;
            color: #2d3748;
            background: #fafafa;
        }

        .form-url-input:focus {
            outline: none;
            border-color: #39A0B3;
            background: white;
            box-shadow: 0 0 0 4px rgba(57, 160, 179, 0.08);
        }

        .form-url-input::placeholder {
            color: #a0aec0;
        }

        /* ===== BUTTON WITH TEAL GRADIENT ===== */
        .form-button {
            background: linear-gradient(90deg, #39A0B3 0%, #1B7A94 100%);
            color: white;
            padding: 18px 48px;
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 1px;
            cursor: pointer;
            margin-top: 24px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(57, 160, 179, 0.3);
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
        }

        .form-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }

        .form-button:hover::before {
            left: 100%;
        }

        .form-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(57, 160, 179, 0.4);
        }

        .form-button:active {
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(57, 160, 179, 0.3);
        }

        .form-button:disabled {
            background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .form-button:disabled::before {
            display: none;
        }

        .form-error {
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            color: #c53030;
            padding: 16px 20px;
            border-radius: 12px;
            margin-top: 16px;
            font-weight: 500;
            border-left: 4px solid #e53e3e;
        }

        /* ===== АДАПТИВНОСТЬ ===== */

        @media (max-width: 768px) {
            .analysis-form {
                padding: 32px 24px;
                border-radius: 16px;
            }

            .form-title {
                font-size: 1.5rem;
            }

            .form-subtitle {
                font-size: 0.95rem;
                margin-bottom: 20px;
            }

            .mode-tabs {
                gap: 6px;
            }

            .mode-tab {
                padding: 8px 18px;
                font-size: 14px;
            }

            .form-textarea {
                height: 240px;
                padding: 16px;
                font-size: 15px;
            }

            .form-url-input {
                padding: 16px 18px;
                font-size: 15px;
            }

            .form-button {
                padding: 16px 40px;
                font-size: 16px;
                width: 100%;
            }
        }

        @media (max-width: 480px) {
            .analysis-form {
                padding: 24px 20px;
                border-radius: 14px;
            }

            .form-title {
                font-size: 1.3rem;
            }

            .mode-tab {
                padding: 8px 14px;
                font-size: 13px;
                flex: 1;
                text-align: center;
            }

            .form-textarea {
                height: 200px;
                padding: 14px;
                font-size: 14px;
            }

            .form-url-input {
                padding: 14px 16px;
                font-size: 14px;
            }

            .form-button {
                padding: 14px 32px;
                font-size: 15px;
            }
        }
    `;
}

/**
 * Инициализировать форму анализа
 * @param {string} containerId - ID контейнера для формы
 * @param {Object} config - Конфигурация формы
 */
function initAnalysisForm(containerId = 'form-container', config = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    // Вставляем HTML
    container.innerHTML = createAnalysisForm(config);

    // Добавляем стили если еще не добавлены
    if (!document.getElementById('analysis-form-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'analysis-form-styles';
        styleEl.innerHTML = getAnalysisFormStyles();
        document.head.appendChild(styleEl);
    }

    // Инициализируем переключение табов
    initModeTabs();
}

/**
 * Инициализация переключения режимов
 */
function initModeTabs() {
    const tabs = document.querySelectorAll('.mode-tab');
    const textMode = document.getElementById('text-mode');
    const youtubeMode = document.getElementById('youtube-mode');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Убираем active со всех табов
            tabs.forEach(t => t.classList.remove('active'));
            // Добавляем active на кликнутый
            tab.classList.add('active');

            // Переключаем режимы
            const mode = tab.dataset.mode;
            if (mode === 'text') {
                textMode.classList.add('active');
                youtubeMode.classList.remove('active');
            } else {
                textMode.classList.remove('active');
                youtubeMode.classList.add('active');
            }
        });
    });
}

/**
 * Получить текущий режим
 * @returns {string} 'text' или 'youtube'
 */
function getCurrentMode() {
    const activeTab = document.querySelector('.mode-tab.active');
    return activeTab ? activeTab.dataset.mode : 'text';
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createAnalysisForm,
        getAnalysisFormStyles,
        initAnalysisForm,
        getCurrentMode
    };
}
