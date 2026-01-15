/**
 * DictionaryWordRow.js
 * Компактная строка для отображения слова в списке словаря
 *
 * Дизайн:
 * - Mobile-first: компактная карточка для экономии вертикального пространства
 * - Кликабельная: открывает modal с деталями при клике
 * - Иконки: 💬 для слов, 📝 для фраз
 */

/**
 * Создает строку словаря для одного слова
 *
 * @param {Object} word - Данные слова
 * @param {string} word.lemma - Слово/фраза
 * @param {string} word.type - "word" или "expression"
 * @param {string[]} word.translations - Массив переводов
 * @param {number} word.examples_count - Количество примеров
 * @param {string} word.added_at - Дата добавления (ISO string)
 * @param {string} word.status - Статус: "new", "learning", "learned"
 *
 * @returns {string} HTML строки
 */
function createDictionaryWordRow(word) {
    const {
        lemma,
        type,
        translations = [],
        examples_count = 0,
        added_at,
        status = 'new'
    } = word;

    // Цвет бордера в зависимости от типа
    const borderColor = type === 'word' ? '#FF9966' : '#4299e1';

    // Форматируем переводы как таблетки
    // Первый перевод - основной (заполненная таблетка)
    // Остальные - дополнительные (с бордером)
    const mainTranslation = translations.length > 0 ? translations[0] : '';
    const additionalTranslations = translations.slice(1);

    const mainTranslationHTML = mainTranslation
        ? `<span class="translation-pill-main">${escapeHtml(mainTranslation)}</span>`
        : '';

    const additionalTranslationsHTML = additionalTranslations.length > 0
        ? `<div class="translation-pills-additional">
             ${additionalTranslations.map(t =>
                 `<span class="translation-pill-bordered">${escapeHtml(t)}</span>`
             ).join('')}
           </div>`
        : '';

    // Форматируем дату
    const formattedDate = formatDateShort(added_at);

    // Плюрализация для примеров
    const examplesText = pluralizeExamples(examples_count);

    // Бейдж статуса (если не new)
    let statusBadge = '';
    if (status === 'learning') {
        statusBadge = '<span class="status-badge learning">Изучаю</span>';
    } else if (status === 'learned') {
        statusBadge = '<span class="status-badge learned">Выучено</span>';
    }

    return `
        <div class="dictionary-word-row" data-lemma="${escapeHtml(lemma)}" data-type="${type}">
            <div class="word-row-content">
                <div class="word-row-left" style="border-left: 3px solid ${borderColor};">
                    <div class="word-row-header">
                        <span class="word-lemma">${escapeHtml(lemma)}</span>
                        ${statusBadge}
                    </div>
                    <div class="word-row-translations">
                        ${mainTranslationHTML}
                        ${additionalTranslationsHTML}
                    </div>
                    <div class="word-row-date">${formattedDate}</div>
                </div>
            </div>
            <button class="delete-word-btn" onclick="deleteWord('${lemma}', event)" title="Удалить слово" aria-label="Удалить слово">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12h14" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    `;
}

/**
 * Возвращает стили компонента DictionaryWordRow
 * @returns {string} CSS стили
 */
function getDictionaryWordRowStyles() {
    return `
        /* ========== DictionaryWordRow Component ========== */

        .dictionary-word-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: white;
            border-radius: 12px;
            padding: 12px;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            position: relative;
        }

        .word-row-content {
            display: flex;
            align-items: flex-start;
            flex: 1;
            min-width: 0;
        }

        .delete-word-btn {
            /* Круглая кнопка с минусом (единый стиль) */
            width: 40px;
            height: 40px;
            min-width: 40px;
            border-radius: 50%;
            background: #FF8A7D;
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(255, 138, 125, 0.3);
            position: relative;
        }

        .delete-word-btn:hover {
            background: #FF7964;
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(255, 138, 125, 0.4);
        }

        .delete-word-btn:active {
            transform: scale(1.05);
        }

        .delete-word-btn svg {
            width: 20px;
            height: 20px;
        }

        /* Left part */
        .word-row-left {
            flex: 1;
            padding-left: 12px;
            min-width: 0;
        }

        /* Header with icon and lemma */
        .word-row-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }

        .word-icon {
            font-size: 1.2rem;
            line-height: 1;
        }

        .word-lemma {
            font-size: 1rem;
            font-weight: 600;
            color: #2d3748;
        }

        /* Status badges */
        .status-badge {
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
            margin-left: 8px;
        }

        .status-badge.learning {
            background: #FFF4E6;
            color: #ed8936;
        }

        .status-badge.learned {
            background: #E6F7ED;
            color: #48bb78;
        }

        /* Translation pills container */
        .word-row-translations {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 8px;
        }

        /* Main translation pill (filled) */
        .translation-pill-main {
            display: inline-block;
            background-color: #0A3A4D;
            color: #ffffff;
            font-size: 14px;
            font-weight: 500;
            padding: 6px 16px;
            border-radius: 50px;
            line-height: 1.2;
            align-self: flex-start;
        }

        /* Additional translations container */
        .translation-pills-additional {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        /* Additional translation pills (bordered) */
        .translation-pill-bordered {
            display: inline-block;
            border: 1.5px solid #2d3748;
            border-radius: 50px;
            padding: 5px 14px;
            font-size: 13px;
            color: #2d3748;
            font-weight: 400;
            line-height: 1.2;
        }

        /* Date below translation */
        .word-row-date {
            font-size: 0.75rem;
            color: #a0aec0;
            font-weight: 500;
        }

        /* Desktop optimizations */
        @media (min-width: 768px) {
            .dictionary-word-row {
                padding: 16px;
            }

            .word-lemma {
                font-size: 1.125rem;
            }

            .word-row-left {
                padding-left: 16px;
            }

            .translation-pill-main {
                font-size: 15px;
                padding: 7px 18px;
            }

            .translation-pill-bordered {
                font-size: 14px;
                padding: 6px 16px;
            }
        }

        /* Mobile optimizations */
        @media (max-width: 480px) {
            .translation-pill-main {
                font-size: 13px;
                padding: 5px 14px;
            }

            .translation-pill-bordered {
                font-size: 12px;
                padding: 4px 12px;
                border-width: 1.5px;
            }

            .translation-pills-additional {
                gap: 6px;
            }
        }
    `;
}

/**
 * Вспомогательные функции
 */

function formatDateShort(dateString) {
    const date = new Date(dateString);
    const now = new Date();

    // Сбрасываем время до полуночи для корректного сравнения дней
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const diffTime = nowOnly - dateOnly;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    // Если добавлено сегодня
    if (diffDays === 0) {
        return 'Сегодня';
    }

    // Если вчера
    if (diffDays === 1) {
        return 'Вчера';
    }

    // Если меньше недели назад
    if (diffDays > 1 && diffDays < 7) {
        return `${diffDays} дн. назад`;
    }

    // Иначе форматируем дату
    const options = { day: '2-digit', month: 'short' };
    return date.toLocaleDateString('ru-RU', options);
}

function pluralizeExamples(count) {
    const lastDigit = count % 10;
    const lastTwoDigits = count % 100;

    if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
        return `${count} примеров`;
    }

    if (lastDigit === 1) {
        return `${count} пример`;
    }

    if (lastDigit >= 2 && lastDigit <= 4) {
        return `${count} примера`;
    }

    return `${count} примеров`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Автоматическая инжекция стилей при загрузке
document.addEventListener('DOMContentLoaded', function() {
    const styles = document.createElement('style');
    styles.innerHTML = getDictionaryWordRowStyles();
    document.head.appendChild(styles);
});
