/**
 * 🎨 HIGHLIGHT CARD COMPONENT V5
 *
 * Современный компактный компонент для отображения карточки хайлайта
 * Обновленные размеры шрифтов и spacing для лучшей читаемости
 */

/**
 * Создает HTML карточки хайлайта
 * @param {Object} highlight - Объект хайлайта
 * @param {number} index - Номер хайлайта (для нумерации)
 * @param {string} theme - Цветовая тема: 'green' или 'orange'
 * @returns {string} HTML карточки
 */
function createHighlightCard(highlight, index, theme = 'green') {
    // Цветовые схемы
    const themes = {
        green: {
            bg: '#C8E3BF',
            textDark: '#0A3A4D',
            textLight: '#ffffff',
            highlightBg: '#1B7A94',
            highlightText: '#C8E3BF'
        },
        orange: {
            bg: '#FEE8BF',
            textDark: '#0A3A4D',
            textLight: '#ffffff',
            highlightBg: '#FF7964',
            highlightText: '#ffffff'
        }
    };

    const colors = themes[theme] || themes.green;

    // Подсветка слова в контексте
    const contextWithHighlight = highlightWordInContext(
        highlight.context,
        highlight.highlight,
        colors.highlightBg,
        colors.highlightText
    );

    // Проверяем наличие словарных значений
    const hasMeanings = highlight.dictionary_meanings && highlight.dictionary_meanings.length > 0;

    // Форматируем словарные значения как теги
    const meaningsHTML = hasMeanings
        ? `<div class="highlight-tags">
             ${highlight.dictionary_meanings.map(meaning =>
                 `<span class="highlight-tag">${meaning}</span>`
             ).join('')}
           </div>`
        : '';

    return `
        <div class="highlight-card" data-theme="${theme}">
            <h1 class="highlight-title">${highlight.highlight}</h1>

            <div class="highlight-subtitle">${highlight.russian_example || highlight.context_translation}</div>

            <div class="highlight-quote-container">
                <div class="highlight-quote-icon">➤</div>
                <p class="highlight-quote-text">${contextWithHighlight}</p>
            </div>

            ${meaningsHTML}
        </div>
    `;
}

/**
 * Подсвечивает слово в контексте
 * @param {string} text - Текст контекста
 * @param {string} word - Слово для подсветки
 * @param {string} bgColor - Цвет фона подсветки
 * @param {string} textColor - Цвет текста подсветки
 * @returns {string} HTML с подсвеченным словом
 */
function highlightWordInContext(text, word, bgColor, textColor) {
    if (!text || !word) return text;

    try {
        const cleanWord = word.trim();

        // Для фраз
        if (word.includes(' ')) {
            let escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            let regex = new RegExp(escapedWord, 'gi');
            let result = text.replace(regex, `<span class="highlight-word-inline" style="background-color: ${bgColor}; color: ${textColor};">${word}</span>`);
            if (result !== text) return result;

            // Попробуем найти каждое слово фразы отдельно
            const words = word.split(' ');
            for (const w of words) {
                if (w.trim().length > 2) {
                    result = highlightWordInContext(text, w.trim(), bgColor, textColor);
                    if (result !== text) return result;
                }
            }
        }

        // Для отдельных слов
        let escapedWord = cleanWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let regex = new RegExp(`\\b${escapedWord}\\b`, 'gi');
        let result = text.replace(regex, `<span class="highlight-word-inline" style="background-color: ${bgColor}; color: ${textColor};">${cleanWord}</span>`);
        if (result !== text) return result;

        // Поиск без границ слов
        regex = new RegExp(escapedWord, 'gi');
        result = text.replace(regex, `<span class="highlight-word-inline" style="background-color: ${bgColor}; color: ${textColor};">${cleanWord}</span>`);
        if (result !== text) return result;

        return text;
    } catch (e) {
        console.error('Highlight error:', e);
        return text;
    }
}

/**
 * Возвращает CSS стили для карточек
 * @returns {string} CSS стили
 */
function getHighlightCardStyles() {
    return `
        /* ===== HIGHLIGHT CARD STYLES V5 ===== */
        .highlight-card {
            font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--card-bg, #FEE8BF);
            border-radius: 20px;
            padding: 36px 40px;
            margin-bottom: 32px;
            max-width: 100%;
        }

        /* Цветовые темы */
        .highlight-card[data-theme="green"] {
            --card-bg: #C8E3BF;
            --text-dark: #0A3A4D;
            --text-light: #ffffff;
            --highlight-bg: #1B7A94;
            --highlight-text: #C8E3BF;
        }

        .highlight-card[data-theme="orange"] {
            --card-bg: #FEE8BF;
            --text-dark: #0A3A4D;
            --text-light: #ffffff;
            --highlight-bg: #1B7A94;
            --highlight-text: #FEE8BF;
        }

        /* Заголовок */
        .highlight-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 16px;
            line-height: 1.1;
        }

        /* Подзаголовок (перевод как таблетка) */
        .highlight-subtitle {
            display: inline-block;
            background-color: var(--text-dark);
            color: var(--text-light);
            font-size: 18px;
            font-weight: 500;
            padding: 8px 20px;
            border-radius: 50px;
            margin-bottom: 24px;
            line-height: 1.1;
        }

        /* Контейнер цитаты */
        .highlight-quote-container {
            display: flex;
            gap: 16px;
            margin-bottom: 0;
        }

        .highlight-quote-icon {
            flex-shrink: 0;
            font-size: 28px;
            color: var(--highlight-bg);
            line-height: 1.1;
        }

        .highlight-quote-text {
            font-size: 17px;
            line-height: 1.5;
            color: var(--text-dark);
            margin: 0;
        }

        /* Подсветка слова внутри текста */
        .highlight-word-inline {
            padding: 1px 6px;
            border-radius: 4px;
            margin: 0 2px;
            box-decoration-break: clone;
            -webkit-box-decoration-break: clone;
        }

        /* Теги (словарные значения) */
        .highlight-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 24px;
        }

        .highlight-tag {
            border: 1.5px solid var(--text-dark);
            border-radius: 50px;
            padding: 8px 20px;
            font-size: 14px;
            color: var(--text-dark);
            background: transparent;
            line-height: 1.1;
        }

        /* ===== АДАПТИВНОСТЬ ===== */

        /* Планшеты (до 768px) */
        @media (max-width: 768px) {
            .highlight-card {
                padding: 28px 32px;
                margin-bottom: 24px;
                border-radius: 16px;
            }

            .highlight-title {
                font-size: 20px;
                margin-bottom: 14px;
            }

            .highlight-subtitle {
                font-size: 16px;
                padding: 7px 18px;
                margin-bottom: 20px;
            }

            .highlight-quote-icon {
                font-size: 24px;
            }

            .highlight-quote-text {
                font-size: 15px;
            }

            .highlight-tag {
                font-size: 13px;
                padding: 7px 18px;
            }
        }

        /* Мобильные (до 480px) */
        @media (max-width: 480px) {
            .highlight-card {
                padding: 24px 28px;
                margin-bottom: 20px;
                border-radius: 14px;
            }

            .highlight-title {
                font-size: 18px;
                margin-bottom: 12px;
            }

            .highlight-subtitle {
                font-size: 15px;
                padding: 6px 16px;
                margin-bottom: 18px;
            }

            .highlight-quote-container {
                gap: 12px;
                margin-bottom: 0;
            }

            .highlight-quote-icon {
                font-size: 20px;
            }

            .highlight-quote-text {
                font-size: 14px;
            }

            .highlight-tags {
                gap: 10px;
            }

            .highlight-tag {
                font-size: 12px;
                padding: 6px 14px;
                border-width: 1.5px;
            }
        }
    `;
}

// Экспортируем функции (если используется модульная система)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createHighlightCard,
        getHighlightCardStyles,
        highlightWordInContext
    };
}
