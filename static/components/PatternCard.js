/**
 * 📌 PATTERN CARD COMPONENT V1
 *
 * Компонент для отображения языковых конструкций (patterns)
 * Показывает пример, шаблон, контекст и объяснение
 */

/**
 * Создает HTML карточки pattern
 * @param {Object} pattern - Объект pattern (это Highlight с type="pattern")
 * @param {number} index - Номер pattern (для нумерации)
 * @returns {string} HTML карточки
 */
function createPatternCard(pattern, index) {
    // Цветовая схема для patterns (фиолетовая)
    const colors = {
        bg: '#E8D5F2',           // Светло-фиолетовый фон
        textDark: '#0A3A4D',     // Темный текст
        textLight: '#ffffff',    // Белый текст
        highlightBg: '#9B59B6',  // Фиолетовый для подсветки
        highlightText: '#ffffff' // Белый текст на подсветке
    };

    // Подсветка примера в контексте
    const contextWithHighlight = highlightWordInContext(
        pattern.context,
        pattern.highlight,  // пример из текста
        colors.highlightBg,
        colors.highlightText
    );

    return `
        <div class="highlight-card pattern-card" data-type="pattern">
            <div class="pattern-template">
                <div class="template-label">📌 Шаблон:</div>
                <div class="template-text">${pattern.pattern_template}</div>
            </div>

            <div class="highlight-quote-container">
                <div class="highlight-quote-icon">➤</div>
                <p class="highlight-quote-text">${contextWithHighlight}</p>
            </div>

            <div class="pattern-explanation">
                <div class="explanation-label">Почему крутое:</div>
                <p class="explanation-text">${pattern.why_interesting}</p>
            </div>
        </div>
    `;
}

/**
 * Подсвечивает слово/фразу в контексте
 * @param {string} text - Текст контекста
 * @param {string} word - Слово/фраза для подсветки
 * @param {string} bgColor - Цвет фона подсветки
 * @param {string} textColor - Цвет текста подсветки
 * @returns {string} HTML с подсвеченным словом
 */
function highlightWordInContext(text, word, bgColor, textColor) {
    // Экранируем спецсимволы для RegExp
    const escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Ищем слово без учета регистра
    const regex = new RegExp(`(${escapedWord})`, 'gi');

    // Заменяем на span с подсветкой
    return text.replace(regex, `<span class="highlight-word" style="background-color: ${bgColor}; color: ${textColor}; padding: 2px 6px; border-radius: 4px; font-weight: 600;">$1</span>`);
}
