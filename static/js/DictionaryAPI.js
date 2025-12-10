/**
 * DictionaryAPI.js
 * API для работы со словарем на фронтенде
 */

/**
 * Добавить слово в словарь
 *
 * @param {Object} highlight - Highlight объект
 * @param {string} highlight.highlight - Слово/фраза (уже лемматизировано!)
 * @param {string} highlight.type - "word" или "expression"
 * @param {string} highlight.highlight_translation - Перевод
 * @param {string} highlight.context - Контекст использования
 * @param {string[]} highlight.dictionary_meanings - Дополнительные значения
 *
 * @returns {Promise<Object>} Результат: {success, message, is_new, word_id}
 */
async function addToDictionary(highlight) {
    try {
        const response = await fetch('/api/dictionary/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(highlight)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка добавления в словарь');
        }

        return data;
    } catch (error) {
        console.error('Ошибка addToDictionary:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Получить все слова из словаря
 *
 * @param {Object} filters - Фильтры (опционально)
 * @param {string} filters.type - "word" или "expression"
 * @param {string} filters.status - "new", "learning", "learned"
 *
 * @returns {Promise<Object>} {success, words, count}
 */
async function getAllWords(filters = null) {
    try {
        let url = '/api/dictionary/words';

        // Добавляем query параметры если есть фильтры
        if (filters) {
            const params = new URLSearchParams();
            if (filters.type) params.append('type', filters.type);
            if (filters.status) params.append('status', filters.status);

            const queryString = params.toString();
            if (queryString) {
                url += '?' + queryString;
            }
        }

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка получения слов');
        }

        return data;
    } catch (error) {
        console.error('Ошибка getAllWords:', error);
        return {
            success: false,
            error: error.message,
            words: [],
            count: 0
        };
    }
}

/**
 * Получить детальную информацию о слове
 *
 * @param {string} lemma - Слово/фраза в словарной форме
 *
 * @returns {Promise<Object>} {success, word}
 * word содержит:
 * - lemma, type, status
 * - translations: [{translation, added_at}]
 * - examples: [{original_form, context, session_id, added_at}]
 * - added_at, review_count, correct_streak
 */
async function getWord(lemma) {
    try {
        const response = await fetch(`/api/dictionary/word/${encodeURIComponent(lemma)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Слово не найдено');
        }

        return data;
    } catch (error) {
        console.error('Ошибка getWord:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Удалить слово из словаря
 *
 * @param {string} lemma - Слово/фраза в словарной форме
 *
 * @returns {Promise<Object>} {success, message}
 */
async function deleteWord(lemma) {
    try {
        const response = await fetch(`/api/dictionary/word/${encodeURIComponent(lemma)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка удаления слова');
        }

        return data;
    } catch (error) {
        console.error('Ошибка deleteWord:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Получить статистику словаря
 *
 * @returns {Promise<Object>} {success, stats}
 * stats содержит:
 * - total_count: всего слов и фраз
 * - total_words: количество слов
 * - total_phrases: количество фраз
 * - status_breakdown: {new, learning, learned}
 */
async function getDictionaryStats() {
    try {
        const response = await fetch('/api/dictionary/stats');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка получения статистики');
        }

        return data;
    } catch (error) {
        console.error('Ошибка getDictionaryStats:', error);
        return {
            success: false,
            error: error.message,
            stats: {
                total_count: 0,
                total_words: 0,
                total_phrases: 0,
                status_breakdown: { new: 0, learning: 0, learned: 0 }
            }
        };
    }
}

/**
 * Показать уведомление пользователю
 *
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип: "success", "error", "info"
 */
function showNotification(message, type = 'success') {
    // Создаем контейнер для уведомлений если его нет
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }

    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    // Цвета в зависимости от типа
    const colors = {
        success: { bg: '#48bb78', icon: '✅' },
        error: { bg: '#f56565', icon: '❌' },
        info: { bg: '#4299e1', icon: 'ℹ️' }
    };

    const color = colors[type] || colors.info;

    notification.style.cssText = `
        background: ${color.bg};
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-weight: 500;
        min-width: 250px;
        max-width: 400px;
        animation: slideIn 0.3s ease;
        cursor: pointer;
    `;

    notification.innerHTML = `${color.icon} ${message}`;

    // Добавляем анимацию
    if (!document.getElementById('notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.innerHTML = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    container.appendChild(notification);

    // Удаляем через 3 секунды
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);

    // Можно закрыть кликом
    notification.addEventListener('click', () => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
}
