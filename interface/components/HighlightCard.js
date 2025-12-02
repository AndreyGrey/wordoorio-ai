/**
 * 🎨 HIGHLIGHT CARD COMPONENT
 *
 * Современный адаптивный компонент для отображения карточки хайлайта
 * На основе дизайна HighlightCard1.html с полной адаптивностью
 */

/**
 * Создает HTML карточки хайлайта
 * @param {Object} highlight - Объект хайлайта
 * @param {number} index - Номер хайлайта (для нумерации)
 * @param {string} theme - Цветовая тема: 'green' (main) или 'orange' (experimental)
 * @returns {string} HTML карточки
 */
function createHighlightCard(highlight, index, theme = 'green') {
    // Цветовые схемы
    const themes = {
        green: {
            bg: '#C8E3BF',
            primary: '#1B7A94',
            secondary: '#0A3A4D',
            accent: '#4CAF50',
            textLight: '#C8E3BF'
        },
        orange: {
            bg: '#FEE8BF',
            primary: '#FF7964',
            secondary: '#0A3A4D',
            accent: '#F7931E',
            textLight: '#FEE8BF'
        }
    };

    const colors = themes[theme] || themes.green;

    // Подсветка слова в контексте
    const contextWithHighlight = highlightWordInContext(highlight.context, highlight.highlight, colors.primary);

    // Проверяем наличие словарных значений
    const hasMeanings = highlight.dictionary_meanings && highlight.dictionary_meanings.length > 0;

    // Форматируем словарные значения как таблетки
    const meaningsHTML = hasMeanings
        ? `<div class="highlight-meanings">
             ${highlight.dictionary_meanings.map(meaning =>
                 `<div class="meaning-pill">${meaning}</div>`
             ).join('')}
           </div>`
        : '';

    return `
        <div class="highlight-card" data-theme="${theme}">
            <!-- Заголовок: само слово/фраза -->
            <div class="highlight-header">
                <h2 class="highlight-word">${highlight.highlight}</h2>
            </div>

            <!-- Перевод (темный блок) -->
            <div class="highlight-translation-block">
                ${highlight.context_translation || highlight.russian_example}
            </div>

            <!-- Контекст с подсветкой -->
            <div class="highlight-context-section">
                <div class="context-arrow">➤</div>
                <div class="context-text">${contextWithHighlight}</div>
            </div>

            <!-- Словарные значения (таблетки) -->
            ${meaningsHTML}
        </div>
    `;
}

/**
 * Подсвечивает слово в контексте
 * @param {string} text - Текст контекста
 * @param {string} word - Слово для подсветки
 * @param {string} color - Цвет подсветки
 * @returns {string} HTML с подсвеченным словом
 */
function highlightWordInContext(text, word, color) {
    if (!text || !word) return text;

    try {
        const cleanWord = word.trim();

        // Для фраз
        if (word.includes(' ')) {
            let escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            let regex = new RegExp(escapedWord, 'gi');
            let result = text.replace(regex, `<span class="highlighted-word" style="background: ${color};">${word}</span>`);
            if (result !== text) return result;

            // Попробуем найти каждое слово фразы отдельно
            const words = word.split(' ');
            for (const w of words) {
                if (w.trim().length > 2) {
                    result = highlightWordInContext(text, w.trim(), color);
                    if (result !== text) return result;
                }
            }
        }

        // Для отдельных слов
        let escapedWord = cleanWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let regex = new RegExp(`\\b${escapedWord}\\b`, 'gi');
        let result = text.replace(regex, `<span class="highlighted-word" style="background: ${color};">${cleanWord}</span>`);
        if (result !== text) return result;

        // Поиск без границ слов
        regex = new RegExp(escapedWord, 'gi');
        result = text.replace(regex, `<span class="highlighted-word" style="background: ${color};">${cleanWord}</span>`);
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
        /* ===== HIGHLIGHT CARD STYLES ===== */
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        .highlight-card {
            font-family: 'Manrope', 'Inter', Arial, sans-serif;
            background: var(--card-bg, #FEE8BF);
            border-radius: 32px;
            padding: 50px;
            margin-bottom: 40px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }

        .highlight-card:hover {
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            transform: translateY(-2px);
        }

        /* Цветовые темы */
        .highlight-card[data-theme="green"] {
            --card-bg: #C8E3BF;
            --primary: #1B7A94;
            --secondary: #0A3A4D;
            --accent: #4CAF50;
            --text-light: #C8E3BF;
        }

        .highlight-card[data-theme="orange"] {
            --card-bg: #FEE8BF;
            --primary: #FF7964;
            --secondary: #0A3A4D;
            --accent: #F7931E;
            --text-light: #FEE8BF;
        }

        /* Заголовок (слово/фраза) */
        .highlight-header {
            margin-bottom: 50px;
        }

        .highlight-word {
            font-size: 80px;
            font-weight: 800;
            line-height: 1.1;
            color: var(--secondary);
            margin: 0;
            word-break: break-word;
        }

        /* Блок перевода */
        .highlight-translation-block {
            background: var(--secondary);
            color: var(--card-bg);
            font-size: 44px;
            font-weight: 600;
            line-height: 1.2;
            padding: 30px;
            border-radius: 32px;
            margin-bottom: 50px;
            display: inline-block;
            max-width: 100%;
            word-break: break-word;
        }

        /* Контекст */
        .highlight-context-section {
            display: flex;
            gap: 20px;
            align-items: flex-start;
            margin-bottom: 50px;
        }

        .context-arrow {
            font-size: 42px;
            color: var(--primary);
            flex-shrink: 0;
            line-height: 1;
        }

        .context-text {
            font-size: 32px;
            font-weight: 600;
            line-height: 1.4;
            color: var(--secondary);
        }

        .highlighted-word {
            color: white;
            padding: 2px 6px;
            border-radius: 6px;
            font-weight: 800;
        }

        /* Словарные значения (таблетки) */
        .highlight-meanings {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }

        .meaning-pill {
            font-size: 32px;
            font-weight: 600;
            color: var(--secondary);
            background: transparent;
            border: 3px solid var(--secondary);
            border-radius: 32px;
            padding: 12px 24px;
            transition: all 0.2s ease;
        }

        .meaning-pill:hover {
            background: var(--secondary);
            color: var(--card-bg);
            transform: translateY(-2px);
        }

        /* ===== АДАПТИВНОСТЬ ===== */

        /* Планшеты (768px - 1024px) */
        @media (max-width: 1024px) {
            .highlight-card {
                padding: 40px;
                margin-bottom: 30px;
            }

            .highlight-word {
                font-size: 60px;
            }

            .highlight-translation-block {
                font-size: 36px;
                padding: 24px;
            }

            .context-arrow {
                font-size: 36px;
            }

            .context-text {
                font-size: 28px;
            }

            .meaning-pill {
                font-size: 28px;
                padding: 10px 20px;
            }
        }

        /* Мобильные (до 768px) */
        @media (max-width: 768px) {
            .highlight-card {
                padding: 30px;
                border-radius: 24px;
                margin-bottom: 24px;
            }

            .highlight-header {
                margin-bottom: 30px;
            }

            .highlight-word {
                font-size: 42px;
            }

            .highlight-translation-block {
                font-size: 28px;
                padding: 20px;
                border-radius: 24px;
                margin-bottom: 30px;
            }

            .highlight-context-section {
                gap: 12px;
                margin-bottom: 30px;
            }

            .context-arrow {
                font-size: 28px;
            }

            .context-text {
                font-size: 22px;
            }

            .meaning-pill {
                font-size: 22px;
                padding: 8px 16px;
                gap: 12px;
            }
        }

        /* Маленькие мобильные (до 480px) */
        @media (max-width: 480px) {
            .highlight-card {
                padding: 20px;
                border-radius: 20px;
                margin-bottom: 20px;
            }

            .highlight-header {
                margin-bottom: 24px;
            }

            .highlight-word {
                font-size: 32px;
            }

            .highlight-translation-block {
                font-size: 22px;
                padding: 16px;
                border-radius: 20px;
                margin-bottom: 24px;
            }

            .highlight-context-section {
                gap: 10px;
                margin-bottom: 24px;
            }

            .context-arrow {
                font-size: 22px;
            }

            .context-text {
                font-size: 18px;
            }

            .highlight-meanings {
                gap: 10px;
            }

            .meaning-pill {
                font-size: 18px;
                padding: 6px 12px;
                border-radius: 20px;
                border-width: 2px;
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
