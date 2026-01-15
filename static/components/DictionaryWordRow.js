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

    // Форматируем переводы (показываем все)
    const translationsText = translations.join(', ');

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
            <div class="word-row-clickable">
                <div class="word-row-left" style="border-left: 3px solid ${borderColor};">
                    <div class="word-row-header">
                        <span class="word-lemma">${escapeHtml(lemma)}</span>
                        ${statusBadge}
                    </div>
                    <div class="word-row-translation">
                        ${escapeHtml(translationsText)}
                    </div>
                </div>
                <div class="word-row-right">
                    <div class="word-row-date">${formattedDate}</div>
                    <div class="word-row-arrow">›</div>
                </div>
            </div>
            <button class="delete-word-btn" onclick="deleteWord('${escapeHtml(lemma)}', event)" title="Удалить слово">
                🗑️
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
            gap: 8px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            position: relative;
        }

        .word-row-clickable {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex: 1;
            cursor: pointer;
            min-width: 0;
        }

        .word-row-clickable:hover {
            opacity: 0.8;
        }

        .dictionary-word-row:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .delete-word-btn {
            background: #ef4444;
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s ease;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .delete-word-btn:hover {
            background: #dc2626;
            transform: scale(1.1);
        }

        .delete-word-btn:active {
            transform: scale(0.95);
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

        /* Translation */
        .word-row-translation {
            font-size: 0.875rem;
            color: #718096;
            margin-bottom: 6px;
            line-height: 1.4;
        }

        .more-indicator {
            color: #a0aec0;
            font-weight: 600;
            margin-left: 4px;
        }

        /* Right part */
        .word-row-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 4px;
            margin-left: 12px;
            flex-shrink: 0;
        }

        /* Date in top right */
        .word-row-date {
            font-size: 0.7rem;
            color: #a0aec0;
            font-weight: 500;
            white-space: nowrap;
        }

        /* Right arrow */
        .word-row-arrow {
            font-size: 1.5rem;
            color: #cbd5e0;
            font-weight: 300;
            transition: transform 0.2s ease;
            line-height: 1;
        }

        .dictionary-word-row:hover .word-row-arrow {
            transform: translateX(4px);
            color: #a0aec0;
        }

        /* Desktop optimizations */
        @media (min-width: 768px) {
            .dictionary-word-row {
                padding: 16px;
            }

            .word-lemma {
                font-size: 1.125rem;
            }

            .word-row-translation {
                font-size: 1rem;
            }

            .word-row-left {
                padding-left: 16px;
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
