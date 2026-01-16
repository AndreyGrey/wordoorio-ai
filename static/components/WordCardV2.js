/**
 * WordCardV2 Component
 *
 * Word card with rating/progress display for dictionary page.
 *
 * Features:
 * - Word lemma with status badge (new/learning/learned)
 * - Translation (main + extra)
 * - Meta info (examples count, date)
 * - Rating display (0-10) with progress bar
 * - Delete button (shows on hover)
 *
 * @version 2.0.0
 */

/**
 * Get rating level class based on rating value
 * @param {number} rating - Rating value 0-10
 * @returns {string} Level class: 'low', 'medium', or 'high'
 */
function getRatingLevel(rating) {
    if (rating >= 8) return 'high';
    if (rating >= 4) return 'medium';
    return 'low';
}

/**
 * Get status badge text and class
 * @param {string} status - Status: 'new', 'learning', 'learned'
 * @returns {Object} {text, className}
 */
function getStatusInfo(status) {
    const statusMap = {
        'new': { text: 'Новое', className: 'new' },
        'learning': { text: 'Изучаю', className: 'learning' },
        'learned': { text: 'Выучено', className: 'learned' }
    };
    return statusMap[status] || statusMap['new'];
}

/**
 * Format date for display
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date DD.MM.YYYY
 */
function formatWordDate(date) {
    if (!date) return '';
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}.${month}.${year}`;
}

/**
 * Get examples count text
 * @param {number} count - Number of examples
 * @returns {string} Formatted text with correct declension
 */
function getExamplesText(count) {
    if (!count || count === 0) return 'нет примеров';

    const lastDigit = count % 10;
    const lastTwoDigits = count % 100;

    if (lastTwoDigits >= 11 && lastTwoDigits <= 14) {
        return `${count} примеров`;
    }

    if (lastDigit === 1) return `${count} пример`;
    if (lastDigit >= 2 && lastDigit <= 4) return `${count} примера`;
    return `${count} примеров`;
}

/**
 * Create word card HTML
 * @param {Object} word - Word data
 * @param {Object} options - Options
 * @returns {string} HTML string
 */
function createWordCard(word, options = {}) {
    const {
        showDelete = true,
        showRating = true,
        showStatus = true,
        onDelete = null,
        onClick = null
    } = options;

    // Extract word data
    const {
        id,
        lemma = '',
        translation = '',
        translation_extra = '',
        translations = [],
        status = 'new',
        rating = 0,
        examples_count = 0,
        added_at = null,
        created_at = null
    } = word;

    // Build translation display
    const mainTranslation = translation || (translations && translations[0]) || '';
    const extraTranslation = translation_extra ||
        (translations && translations.length > 1 ? translations.slice(1).join(', ') : '');

    // Status info
    const statusInfo = getStatusInfo(status);

    // Rating level
    const ratingLevel = getRatingLevel(rating);
    const ratingPercent = Math.round((rating / 10) * 100);

    // Date
    const date = formatWordDate(added_at || created_at);

    // Examples text
    const examplesText = getExamplesText(examples_count);

    // Build HTML
    return `
        <div class="word-card" data-word-id="${id || ''}" data-lemma="${escapeHtml(lemma)}">
            <div class="word-main">
                <div class="word-header">
                    <span class="word-lemma">${escapeHtml(lemma)}</span>
                    ${showStatus ? `<span class="status-badge ${statusInfo.className}">${statusInfo.text}</span>` : ''}
                </div>
                <div class="word-translation">
                    <span class="translation-main">${escapeHtml(mainTranslation)}</span>
                    ${extraTranslation ? `<span class="translation-extra">${escapeHtml(extraTranslation)}</span>` : ''}
                </div>
                <div class="word-meta">
                    ${examplesText ? `<span class="meta-item">${examplesText}</span>` : ''}
                    ${date ? `<span class="meta-item">${date}</span>` : ''}
                </div>
            </div>
            ${showRating ? `
                <div class="word-progress">
                    <div class="rating-display">
                        <span class="rating-value ${ratingLevel}">${rating}</span>
                        <span class="rating-max">/10</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${ratingLevel}" style="width: ${ratingPercent}%"></div>
                    </div>
                </div>
            ` : ''}
            ${showDelete ? `
                <button class="delete-btn" title="Удалить" data-action="delete">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12h14" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                </button>
            ` : ''}
        </div>
    `;
}

/**
 * Escape HTML special characters
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Get WordCard styles
 * @returns {string} CSS styles
 */
function getWordCardStyles() {
    return `
        /* ===== WORD CARD v2.0 ===== */

        /* Status colors */
        :root {
            --wc-color-new: #718096;
            --wc-color-learning: #ed8936;
            --wc-color-learned: #48bb78;
            --wc-color-border: #e2e8f0;
            --wc-color-surface: #ffffff;
            --wc-color-surface-hover: #f7fafc;
            --wc-color-text: #1a202c;
            --wc-color-text-secondary: #4a5568;
            --wc-color-text-muted: #718096;
            --wc-color-text-light: #a0aec0;
        }

        .word-card {
            background: var(--wc-color-surface);
            border-radius: var(--radius-lg, 16px);
            padding: 16px 20px;
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 16px;
            align-items: center;
            box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.08));
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .word-card:hover {
            box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.1));
            transform: translateY(-2px);
        }

        /* Main content area */
        .word-main {
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 0;
        }

        .word-header {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .word-lemma {
            font-size: 1.0625rem;
            font-weight: 700;
            color: var(--wc-color-text);
            letter-spacing: -0.01em;
        }

        /* Status badge */
        .status-badge {
            font-size: 0.6875rem;
            font-weight: 500;
            padding: 3px 8px;
            border-radius: var(--radius-full, 9999px);
            border: 1px solid;
            background: transparent;
        }

        .status-badge.new {
            border-color: var(--wc-color-text-light);
            color: var(--wc-color-text-light);
        }

        .status-badge.learning {
            border-color: #d69e2e;
            color: #b7791f;
        }

        .status-badge.learned {
            border-color: #38a169;
            color: #2f855a;
        }

        /* Translation */
        .word-translation {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding-left: 12px;
            border-left: 2px solid var(--wc-color-border);
        }

        .translation-main {
            font-size: 1rem;
            font-weight: 600;
            color: var(--wc-color-text);
            line-height: 1.3;
        }

        .translation-extra {
            font-size: 0.8125rem;
            color: var(--wc-color-text-muted);
            font-weight: 400;
        }

        /* Meta info */
        .word-meta {
            font-size: 0.6875rem;
            color: var(--wc-color-text-light);
            margin-top: 6px;
        }

        .word-meta .meta-item {
            display: inline;
        }

        .word-meta .meta-item:not(:last-child)::after {
            content: "·";
            margin: 0 6px;
            opacity: 0.5;
        }

        /* Rating indicator */
        .word-progress {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 8px;
            min-width: 80px;
        }

        .rating-display {
            display: flex;
            align-items: baseline;
            gap: 2px;
        }

        .rating-value {
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1;
        }

        .rating-max {
            font-size: 0.875rem;
            color: var(--wc-color-text-light);
            font-weight: 500;
        }

        /* Rating color by value */
        .rating-value.low { color: var(--wc-color-new); }
        .rating-value.medium { color: var(--wc-color-learning); }
        .rating-value.high { color: var(--wc-color-learned); }

        /* Progress bar */
        .progress-bar {
            width: 100%;
            height: 6px;
            background: var(--wc-color-border);
            border-radius: var(--radius-full, 9999px);
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: var(--radius-full, 9999px);
            transition: width 0.3s ease;
        }

        .progress-fill.low { background: var(--wc-color-new); }
        .progress-fill.medium { background: var(--wc-color-learning); }
        .progress-fill.high { background: var(--wc-color-learned); }

        /* Delete button */
        .word-card .delete-btn {
            width: 32px;
            height: 32px;
            min-width: 32px;
            border-radius: 50%;
            background: transparent;
            color: var(--wc-color-text-light);
            border: 1px solid var(--wc-color-border);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            flex-shrink: 0;
            opacity: 0;
        }

        .word-card:hover .delete-btn {
            opacity: 1;
        }

        .word-card .delete-btn:hover {
            background: #fed7d7;
            border-color: #fc8181;
            color: #c53030;
        }

        .word-card .delete-btn svg {
            width: 16px;
            height: 16px;
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 640px) {
            .word-card {
                padding: 14px 16px;
                grid-template-columns: 1fr 50px 32px;
                gap: 12px;
            }

            .word-card .delete-btn {
                width: 32px;
                height: 32px;
                min-width: 32px;
                opacity: 1;
            }

            .word-lemma {
                font-size: 1rem;
            }

            .word-progress {
                min-width: 50px;
            }

            .rating-value {
                font-size: 1.25rem;
            }

            .rating-max {
                font-size: 0.75rem;
            }

            .progress-bar {
                height: 5px;
            }
        }
    `;
}

/**
 * Initialize WordCard styles (inject into document head)
 */
function initWordCardStyles() {
    if (!document.getElementById('word-card-v2-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'word-card-v2-styles';
        styleEl.innerHTML = getWordCardStyles();
        document.head.appendChild(styleEl);
    }
}

/**
 * Render word list
 * @param {Array} words - Array of word objects
 * @param {string} containerId - Container element ID
 * @param {Object} options - Options for word cards
 */
function renderWordList(words, containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    // Initialize styles
    initWordCardStyles();

    // Render cards
    const html = words.map(word => createWordCard(word, options)).join('');
    container.innerHTML = html;

    // Setup event handlers
    setupWordCardEvents(container, options);
}

/**
 * Setup event handlers for word cards
 * @param {HTMLElement} container - Container element
 * @param {Object} options - Options with callbacks
 */
function setupWordCardEvents(container, options = {}) {
    const { onDelete, onClick } = options;

    // Delete button clicks
    container.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = btn.closest('.word-card');
            const wordId = card.dataset.wordId;
            const lemma = card.dataset.lemma;

            if (onDelete) {
                onDelete(wordId, lemma, card);
            }
        });
    });

    // Card clicks
    if (onClick) {
        container.querySelectorAll('.word-card').forEach(card => {
            card.addEventListener('click', () => {
                const wordId = card.dataset.wordId;
                const lemma = card.dataset.lemma;
                onClick(wordId, lemma, card);
            });
        });
    }
}

// Auto-initialize styles on DOMContentLoaded
document.addEventListener('DOMContentLoaded', initWordCardStyles);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createWordCard,
        getWordCardStyles,
        initWordCardStyles,
        renderWordList,
        getRatingLevel,
        getStatusInfo
    };
}
