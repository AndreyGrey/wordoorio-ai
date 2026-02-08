/**
 * 🎨 HIGHLIGHT CARD COMPONENT V6
 *
 * Интерактивный компонент карточки с кнопками действий
 * - Glass эффект при ховере/тапе
 * - Кнопки сохранения и удаления
 * - Плавные анимации и переходы
 * - Адаптивность для мобильных устройств
 */

/**
 * Создает HTML карточки хайлайта с интерактивными кнопками
 * @param {Object} highlight - Объект хайлайта
 * @param {number} index - Номер хайлайта (для нумерации)
 * @param {string} theme - Цветовая тема: 'green' или 'orange'
 * @param {boolean} showActions - Показывать ли кнопки действий (по умолчанию true)
 * @returns {string} HTML карточки
 */
function createHighlightCard(highlight, index, theme = 'green', showActions = true) {
    // Цветовые схемы
    const themes = {
        green: {
            bg: '#C8E3BF',
            textDark: '#0A3A4D',
            textLight: '#ffffff',
            highlightBg: '#1B7A94',
            highlightText: '#C8E3BF',
            btnSave: '#5AAFBD',
            btnDelete: '#FF8A7D'
        },
        orange: {
            bg: '#FEE8BF',
            textDark: '#0A3A4D',
            textLight: '#ffffff',
            highlightBg: '#FF7964',
            highlightText: '#ffffff',
            btnSave: '#5AAFBD',
            btnDelete: '#FF8A7D'
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

    // Оверлей с кнопками (опционально)
    const actionsHTML = showActions
        ? `
            <!-- Оверлей с кнопками действий -->
            <div class="highlight-actions-overlay">
                <button class="action-btn action-btn-save" 
                        data-action="save" 
                        data-index="${index}"
                        aria-label="Сохранить для изучения">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                        <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
                    </svg>
                </button>
                
                <button class="action-btn action-btn-delete" 
                        data-action="delete" 
                        data-index="${index}"
                        aria-label="Удалить из списка">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12h14" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `
        : '';

    return `
        <div class="highlight-card-v6" data-theme="${theme}" data-index="${index}" data-has-actions="${showActions}">
            <!-- Основной контент -->
            <div class="highlight-card-content">
                <h1 class="highlight-title">${highlight.highlight}</h1>

                <div class="highlight-subtitle">${getMainTranslation(highlight)}</div>

                <div class="highlight-blurrable">
                    <div class="highlight-quote-container">
                        <div class="highlight-quote-icon">➤</div>
                        <p class="highlight-quote-text">${contextWithHighlight}</p>
                    </div>

                    ${meaningsHTML}
                </div>
            </div>

            ${actionsHTML}
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
 * Получает основной перевод хайлайта
 * @param {Object} highlight - Объект хайлайта
 * @returns {string} Перевод от агента
 */
function getMainTranslation(highlight) {
    // Агент всегда возвращает контекстный перевод
    return highlight.highlight_translation || '';
}

/**
 * Инициализирует обработчики событий для карточек
 */
function initHighlightCardInteractions() {
    // Обработчики для desktop (hover)
    document.querySelectorAll('.highlight-card-v6').forEach(card => {
        // Пропускаем карточки без кнопок
        if (card.dataset.hasActions === 'false') return;
        
        // Hover эффекты на desktop
        if (window.matchMedia('(hover: hover)').matches) {
            card.addEventListener('mouseenter', () => {
                card.classList.add('actions-visible');
            });

            card.addEventListener('mouseleave', () => {
                card.classList.remove('actions-visible');
            });
        }

        // Touch эффекты на мобильных
        card.addEventListener('click', (e) => {
            // Игнорируем клики по кнопкам
            if (e.target.closest('.action-btn')) return;

            if (window.matchMedia('(hover: none)').matches) {
                // На мобильных - toggle состояния
                const wasVisible = card.classList.contains('actions-visible');
                
                // Закрываем все остальные карточки
                document.querySelectorAll('.highlight-card-v6').forEach(otherCard => {
                    if (otherCard !== card) {
                        otherCard.classList.remove('actions-visible');
                    }
                });

                // Переключаем текущую
                card.classList.toggle('actions-visible', !wasVisible);
            }
        });
    });

    // Обработчики кнопок действий
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', handleActionButtonClick);
    });
}

/**
 * Обработчик нажатия на кнопки действий
 * @param {Event} e - Событие клика
 */
function handleActionButtonClick(e) {
    e.stopPropagation();
    
    const button = e.currentTarget;
    const action = button.dataset.action;
    const index = button.dataset.index;
    const card = button.closest('.highlight-card-v6');

    // Анимация нажатия кнопки
    button.classList.add('btn-pressed');
    setTimeout(() => button.classList.remove('btn-pressed'), 200);

    if (action === 'delete') {
        handleDeleteCard(card, index);
    } else if (action === 'save') {
        handleSaveCard(card, index);
    }
}

/**
 * Удаляет карточку из списка с анимацией
 * @param {HTMLElement} card - DOM элемент карточки
 * @param {string} index - Индекс карточки
 */
function handleDeleteCard(card, index) {
    // Добавляем класс для анимации удаления
    card.classList.add('card-removing');

    // Ждем окончания анимации, затем удаляем элемент
    setTimeout(() => {
        card.style.height = card.offsetHeight + 'px';
        requestAnimationFrame(() => {
            card.style.height = '0';
            card.style.marginBottom = '0';
            card.style.opacity = '0';
        });

        setTimeout(() => {
            card.remove();
            
            // Вызываем callback если нужен (для интеграции с backend)
            if (typeof window.onHighlightDeleted === 'function') {
                window.onHighlightDeleted(index);
            }
        }, 400);
    }, 200);
}

/**
 * Сохраняет карточку для изучения
 * @param {HTMLElement} card - DOM элемент карточки
 * @param {string} index - Индекс карточки
 */
function handleSaveCard(card, index) {
    // Получаем данные хайлайта через callback
    let highlightData = null;
    if (typeof window.getHighlightData === 'function') {
        highlightData = window.getHighlightData(index);
    }

    // Если есть несколько вариантов перевода — показываем выбор
    if (highlightData && highlightData.dictionary_meanings && highlightData.dictionary_meanings.length > 0) {
        showTranslationChoices(card, index, highlightData);
        return;
    }

    // Один вариант — сохраняем сразу
    completeSave(card, index, highlightData ? highlightData.highlight_translation : null);
}

/**
 * Показывает пиллы выбора перевода
 * @param {HTMLElement} card - DOM элемент карточки
 * @param {string} index - Индекс карточки
 * @param {Object} highlightData - Данные хайлайта
 */
function showTranslationChoices(card, index, highlightData) {
    // Собираем все варианты: основной + из словаря
    const choices = [highlightData.highlight_translation, ...highlightData.dictionary_meanings];

    // Создаём или находим оверлей с пиллами
    let overlay = card.querySelector('.translation-choices-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'translation-choices-overlay';
        card.appendChild(overlay);
    }

    // Генерируем HTML пиллов
    overlay.innerHTML = choices.map(choice =>
        `<button class="translation-pill" data-translation="${choice}" data-index="${index}">${choice}</button>`
    ).join('') + `
        <button class="cancel-pill" data-index="${index}">
            <svg viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
        </button>
    `;

    // Добавляем обработчики
    overlay.querySelectorAll('.translation-pill').forEach(pill => {
        pill.addEventListener('click', handleTranslationSelect);
    });
    overlay.querySelector('.cancel-pill').addEventListener('click', handleCancelChoice);

    // Переключаем в режим выбора
    card.classList.remove('actions-visible');
    card.classList.add('choosing');
}

/**
 * Обработчик выбора перевода
 * @param {Event} e - Событие клика
 */
function handleTranslationSelect(e) {
    const pill = e.currentTarget;
    const card = pill.closest('.highlight-card-v6');
    const index = pill.dataset.index;
    const translation = pill.dataset.translation;

    card.classList.remove('choosing');
    completeSave(card, index, translation);
}

/**
 * Обработчик отмены выбора
 * @param {Event} e - Событие клика
 */
function handleCancelChoice(e) {
    const btn = e.currentTarget;
    const card = btn.closest('.highlight-card-v6');
    card.classList.remove('choosing');
    card.classList.add('actions-visible');
}

/**
 * Завершает сохранение карточки
 * @param {HTMLElement} card - DOM элемент карточки
 * @param {string} index - Индекс карточки
 * @param {string|null} translation - Выбранный перевод
 */
function completeSave(card, index, translation) {
    // Визуальная индикация сохранения
    card.classList.add('card-saved');

    // Показываем уведомление с выбранным переводом
    showSaveNotification(card, translation);

    // Убираем индикацию через некоторое время
    setTimeout(() => {
        card.classList.remove('card-saved');
        card.classList.remove('actions-visible');
    }, 1500);

    // Вызываем callback если нужен (для интеграции с backend)
    if (typeof window.onHighlightSaved === 'function') {
        window.onHighlightSaved(index, translation);
    }
}

/**
 * Показывает уведомление о сохранении
 * @param {HTMLElement} card - DOM элемент карточки
 * @param {string|null} translation - Выбранный перевод (опционально)
 */
function showSaveNotification(card, translation = null) {
    const notification = document.createElement('div');
    notification.className = 'save-notification';
    notification.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>${translation || 'Сохранено'}</span>
    `;

    card.appendChild(notification);

    // Удаляем уведомление через 2 секунды
    setTimeout(() => {
        notification.classList.add('notification-fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 1200);
}

/**
 * Возвращает CSS стили для карточек v6
 * @returns {string} CSS стили
 */
function getHighlightCardStyles() {
    return `
        /* ===== HIGHLIGHT CARD V6 STYLES ===== */
        .highlight-card-v6 {
            font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--card-bg, #FEE8BF);
            border-radius: 20px;
            padding: 36px 40px;
            margin-bottom: 32px;
            max-width: 100%;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Цветовые темы */
        .highlight-card-v6[data-theme="green"] {
            --card-bg: #C8E3BF;
            --text-dark: #0A3A4D;
            --text-light: #ffffff;
            --highlight-bg: #1B7A94;
            --highlight-text: #C8E3BF;
            --btn-save: #5AAFBD;
            --btn-delete: #FF8A7D;
        }

        .highlight-card-v6[data-theme="orange"] {
            --card-bg: #FEE8BF;
            --text-dark: #0A3A4D;
            --text-light: #ffffff;
            --highlight-bg: #1B7A94;
            --highlight-text: #FEE8BF;
            --btn-save: #5AAFBD;
            --btn-delete: #FF8A7D;
        }

        /* Контент карточки */
        .highlight-card-content {
            position: relative;
            z-index: 1;
            transition: all 0.3s ease;
        }

        /* Заголовок */
        .highlight-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 16px;
            line-height: 1.1;
            position: relative;
            z-index: 3;
            transition: transform 0.3s ease;
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
            position: relative;
            z-index: 3;
            transition: transform 0.3s ease;
        }

        /* Блюрящийся контент */
        .highlight-blurrable {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        /* Контейнер цитаты */
        .highlight-quote-container {
            display: flex;
            gap: 16px;
            margin-bottom: 28px;
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

        /* ===== ИНТЕРАКТИВНЫЕ КНОПКИ ===== */
        
        /* Оверлей с кнопками */
        .highlight-actions-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 32px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 2;
        }

        /* Состояние с видимыми кнопками */
        .highlight-card-v6.actions-visible .highlight-actions-overlay {
            opacity: 1;
            pointer-events: all;
        }

        .highlight-card-v6.actions-visible .highlight-blurrable {
            filter: blur(8px);
            opacity: 0.3;
        }

        /* Glass эффект на карточке при активации */
        .highlight-card-v6.actions-visible::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 1;
            pointer-events: none;
        }

        /* Кнопки действий */
        .action-btn {
            width: 100px;
            height: 88px;
            border-radius: 44px;
            border: 1.5px solid rgba(255, 255, 255, 0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
            transform: scale(0.8);
            opacity: 0;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        }

        .highlight-card-v6.actions-visible .action-btn {
            transform: scale(1);
            opacity: 1;
        }

        /* Анимация появления с задержкой */
        .action-btn-save {
            background: linear-gradient(135deg, 
                rgba(90, 175, 189, 0.95) 0%, 
                rgba(74, 155, 169, 0.95) 100%);
            transition-delay: 0.05s;
        }

        .action-btn-delete {
            background: linear-gradient(135deg, 
                rgba(255, 138, 125, 0.95) 0%, 
                rgba(255, 112, 100, 0.95) 100%);
            transition-delay: 0.1s;
        }

        /* Hover эффект */
        .action-btn:hover {
            transform: scale(1.06) translateY(-2px);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
        }

        .action-btn:active {
            transform: scale(0.94);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }

        /* Состояние нажатия */
        .action-btn.btn-pressed {
            animation: btnPress 0.2s ease;
        }

        @keyframes btnPress {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(0.88); }
        }

        /* Ripple эффект при нажатии */
        .action-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.4);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .action-btn:active::before {
            width: 120px;
            height: 120px;
        }

        /* SVG иконки в кнопках */
        .action-btn svg {
            position: relative;
            z-index: 1;
        }

        /* ===== АНИМАЦИИ СОСТОЯНИЙ ===== */
        
        /* Анимация удаления карточки */
        .highlight-card-v6.card-removing {
            animation: cardRemove 0.4s ease forwards;
        }

        @keyframes cardRemove {
            0% {
                opacity: 1;
                transform: translateX(0) scale(1);
            }
            100% {
                opacity: 0;
                transform: translateX(-100%) scale(0.8);
            }
        }

        /* Состояние сохранения */
        .highlight-card-v6.card-saved {
            animation: cardSaved 0.5s ease;
        }

        @keyframes cardSaved {
            0%, 100% { transform: scale(1); }
            25% { transform: scale(1.02); }
            75% { transform: scale(0.98); }
        }

        /* Уведомление о сохранении */
        .save-notification {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--btn-save);
            color: white;
            padding: 12px 20px;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 15px;
            font-weight: 600;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            z-index: 10;
            animation: notificationSlideIn 0.3s ease;
        }

        @keyframes notificationSlideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .save-notification.notification-fade-out {
            animation: notificationFadeOut 0.3s ease forwards;
        }

        @keyframes notificationFadeOut {
            to {
                opacity: 0;
                transform: translateY(-10px);
            }
        }

        /* ===== АДАПТИВНОСТЬ ===== */

        /* Планшеты (до 768px) */
        @media (max-width: 768px) {
            .highlight-card-v6 {
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

            .action-btn {
                width: 88px;
                height: 76px;
                border-radius: 38px;
            }

            .action-btn svg {
                width: 28px;
                height: 28px;
            }

            .highlight-actions-overlay {
                gap: 24px;
            }
        }

        /* Мобильные (до 480px) */
        @media (max-width: 480px) {
            .highlight-card-v6 {
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
                margin-bottom: 24px;
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

            .action-btn {
                width: 76px;
                height: 68px;
                border-radius: 34px;
            }

            .action-btn svg {
                width: 24px;
                height: 24px;
            }

            .highlight-actions-overlay {
                gap: 20px;
            }

            .save-notification {
                top: 12px;
                right: 12px;
                padding: 10px 16px;
                font-size: 14px;
            }
        }

        /* Улучшение производительности анимаций */
        .highlight-card-v6,
        .highlight-blurrable,
        .action-btn,
        .highlight-actions-overlay {
            will-change: transform, opacity, filter;
        }

        /* Отключаем will-change после завершения анимации */
        .highlight-card-v6:not(.actions-visible):not(.card-removing):not(.card-saved) {
            will-change: auto;
        }

        /* ===== РЕЖИМ ВЫБОРА ПЕРЕВОДА (choosing) ===== */

        /* Оверлей с пиллами выбора */
        .translation-choices-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            padding: 20px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 3;
        }

        .highlight-card-v6.choosing .translation-choices-overlay {
            opacity: 1;
            pointer-events: all;
        }

        /* В режиме choosing: кнопки +/- скрыты даже при hover */
        .highlight-card-v6.choosing .highlight-actions-overlay,
        .highlight-card-v6.choosing.actions-visible .highlight-actions-overlay {
            opacity: 0 !important;
            pointer-events: none !important;
        }

        .highlight-card-v6.choosing .highlight-blurrable {
            filter: blur(8px);
            opacity: 0.3;
        }

        /* Таблетка перевода скрывается в режиме choosing */
        .highlight-card-v6.choosing .highlight-subtitle {
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s ease;
        }

        /* Заголовок центрируется в режиме choosing */
        .highlight-card-v6 .highlight-title {
            transition: all 0.4s ease;
        }

        .highlight-card-v6.choosing .highlight-title {
            text-align: center;
            transform: translateY(20px);
        }

        .highlight-card-v6.choosing::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 1;
            pointer-events: none;
        }

        /* Пиллы выбора перевода */
        .translation-pill {
            background: var(--text-dark, #0A3A4D);
            color: var(--text-light, #ffffff);
            font-size: 17px;
            font-weight: 600;
            padding: 12px 24px;
            border-radius: 50px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            line-height: 1.1;
            transform: scale(0.8);
            opacity: 0;
            animation: pillAppear 0.3s ease forwards;
        }

        .translation-pill:nth-child(1) { animation-delay: 0.05s; }
        .translation-pill:nth-child(2) { animation-delay: 0.1s; }
        .translation-pill:nth-child(3) { animation-delay: 0.15s; }
        .translation-pill:nth-child(4) { animation-delay: 0.2s; }
        .translation-pill:nth-child(5) { animation-delay: 0.25s; }

        @keyframes pillAppear {
            to { transform: scale(1); opacity: 1; }
        }

        .translation-pill:hover {
            background: #1a5a6d;
            transform: scale(1.05) translateY(-2px);
        }

        .translation-pill:active {
            transform: scale(0.95);
        }

        /* Кнопка отмены */
        .cancel-pill {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.5);
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(4px);
            color: var(--text-dark, #0A3A4D);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            transform: scale(0.8);
            opacity: 0;
            animation: pillAppear 0.3s ease forwards;
            animation-delay: 0.3s;
        }

        .cancel-pill:hover {
            background: rgba(255, 100, 100, 0.3);
            border-color: rgba(255, 100, 100, 0.5);
        }

        .cancel-pill svg {
            width: 20px;
            height: 20px;
        }

        /* Мобильная адаптивность для пиллов */
        @media (max-width: 480px) {
            .translation-pill {
                font-size: 15px;
                padding: 10px 18px;
            }

            .cancel-pill {
                width: 40px;
                height: 40px;
            }
        }
    `;
}

// Экспортируем функции (если используется модульная система)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createHighlightCard,
        getHighlightCardStyles,
        highlightWordInContext,
        initHighlightCardInteractions,
        handleDeleteCard,
        handleSaveCard
    };
}
