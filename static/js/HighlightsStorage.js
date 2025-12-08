/**
 * 💾 HIGHLIGHTS STORAGE MODULE
 *
 * Модуль для работы с сохраненными хайлайтами через localStorage.
 * Управляет сессиями анализа, сохранением карточек, кешированием.
 *
 * @version 1.0.0
 * @author Wordoorio Team
 */

class HighlightsStorage {
    constructor() {
        this.KEYS = {
            SESSIONS: 'wordoorio_sessions',
            SAVED: 'wordoorio_saved',
            LAST_ANALYSIS: 'wordoorio_last_analysis'
        };
    }

    // ===== СЕССИИ =====

    /**
     * Создать новую сессию анализа
     * @param {string} originalText - Исходный текст
     * @param {string} page - Страница: "main" | "experimental"
     * @returns {string} session_id
     */
    createSession(originalText, page) {
        const sessionId = this.generateSessionId();
        const session = {
            session_id: sessionId,
            original_text: originalText,
            created_at: new Date().toISOString(),
            page: page,
            highlights_count: 0
        };

        const sessions = this.getAllSessions();
        sessions.push(session);
        localStorage.setItem(this.KEYS.SESSIONS, JSON.stringify(sessions));

        console.log(`📝 Создана новая сессия: ${sessionId}`);
        return sessionId;
    }

    /**
     * Получить сессию по ID
     * @param {string} sessionId
     * @returns {object|null}
     */
    getSession(sessionId) {
        const sessions = this.getAllSessions();
        return sessions.find(s => s.session_id === sessionId) || null;
    }

    /**
     * Получить все сессии (сортировка по дате, новые сверху)
     * @returns {Array}
     */
    getAllSessions() {
        try {
            const data = localStorage.getItem(this.KEYS.SESSIONS);
            const sessions = data ? JSON.parse(data) : [];
            // Сортируем по дате создания (новые сверху)
            return sessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        } catch (e) {
            console.error('Ошибка чтения сессий:', e);
            return [];
        }
    }

    /**
     * Обновить счетчик хайлайтов в сессии
     * @param {string} sessionId
     */
    updateHighlightsCount(sessionId) {
        const sessions = this.getAllSessions();
        const session = sessions.find(s => s.session_id === sessionId);
        if (session) {
            const savedHighlights = this.getSavedHighlights(sessionId);
            session.highlights_count = savedHighlights.length;
            localStorage.setItem(this.KEYS.SESSIONS, JSON.stringify(sessions));
        }
    }

    // ===== СОХРАНЕННЫЕ ХАЙЛАЙТЫ =====

    /**
     * Сохранить хайлайт в сет
     * @param {string} sessionId
     * @param {object} highlight
     * @returns {boolean} успех операции
     */
    saveHighlight(sessionId, highlight) {
        try {
            // Проверка что сессия существует
            if (!this.getSession(sessionId)) {
                console.error(`Сессия ${sessionId} не найдена`);
                return false;
            }

            // Проверка дубликата
            if (this.isHighlightSaved(sessionId, highlight)) {
                console.warn(`Хайлайт "${highlight.highlight}" уже сохранен`);
                return false;
            }

            // Получаем существующие хайлайты
            const saved = this._getAllSaved();
            if (!saved[sessionId]) {
                saved[sessionId] = [];
            }

            // Добавляем новый
            saved[sessionId].push(highlight);
            localStorage.setItem(this.KEYS.SAVED, JSON.stringify(saved));

            // Обновляем счетчик
            this.updateHighlightsCount(sessionId);

            console.log(`✅ Сохранен хайлайт: "${highlight.highlight}" в сессию ${sessionId}`);
            return true;
        } catch (e) {
            console.error('Ошибка сохранения хайлайта:', e);
            return false;
        }
    }

    /**
     * Проверить сохранен ли хайлайт
     * @param {string} sessionId
     * @param {object} highlight
     * @returns {boolean}
     */
    isHighlightSaved(sessionId, highlight) {
        const saved = this.getSavedHighlights(sessionId);
        return saved.some(h => h.highlight === highlight.highlight);
    }

    /**
     * Получить все сохраненные хайлайты для сессии
     * @param {string} sessionId
     * @returns {Array}
     */
    getSavedHighlights(sessionId) {
        const saved = this._getAllSaved();
        return saved[sessionId] || [];
    }

    /**
     * Получить ВСЕ сохраненные хайлайты (внутренний метод)
     * @private
     * @returns {object}
     */
    _getAllSaved() {
        try {
            const data = localStorage.getItem(this.KEYS.SAVED);
            return data ? JSON.parse(data) : {};
        } catch (e) {
            console.error('Ошибка чтения сохраненных:', e);
            return {};
        }
    }

    // ===== ПОСЛЕДНИЙ АНАЛИЗ (КЕШИРОВАНИЕ) =====

    /**
     * Сохранить результаты последнего анализа
     * @param {string} sessionId
     * @param {string} page
     * @param {Array} highlights
     */
    saveLastAnalysis(sessionId, page, highlights) {
        const analysis = {
            session_id: sessionId,
            page: page,
            timestamp: new Date().toISOString(),
            highlights: highlights,
            deleted_indexes: []
        };
        localStorage.setItem(this.KEYS.LAST_ANALYSIS, JSON.stringify(analysis));
        console.log(`💾 Кеширован последний анализ: ${highlights.length} хайлайтов`);
    }

    /**
     * Получить результаты последнего анализа
     * @returns {object|null}
     */
    getLastAnalysis() {
        try {
            const data = localStorage.getItem(this.KEYS.LAST_ANALYSIS);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('Ошибка чтения last_analysis:', e);
            return null;
        }
    }

    /**
     * Пометить карточку как удаленную в текущей сессии
     * @param {number} index
     */
    markAsDeleted(index) {
        const analysis = this.getLastAnalysis();
        if (!analysis) return;

        if (!analysis.deleted_indexes.includes(index)) {
            analysis.deleted_indexes.push(index);
            localStorage.setItem(this.KEYS.LAST_ANALYSIS, JSON.stringify(analysis));
            console.log(`🗑️  Карточка ${index} помечена как удаленная`);
        }
    }

    /**
     * Проверить удалена ли карточка
     * @param {number} index
     * @returns {boolean}
     */
    isDeleted(index) {
        const analysis = this.getLastAnalysis();
        return analysis ? analysis.deleted_indexes.includes(index) : false;
    }

    // ===== УТИЛИТЫ =====

    /**
     * Генерировать UUID v4 для session_id
     * @returns {string}
     */
    generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Сгенерировать название сета из текста
     * @param {string} text
     * @param {number} maxLength
     * @returns {string}
     */
    generateSetTitle(text, maxLength = 120) {
        // Убираем лишние пробелы и переносы
        const cleaned = text.trim().replace(/\s+/g, ' ');

        if (cleaned.length <= maxLength) {
            return cleaned;
        }

        // Обрезаем до maxLength
        const truncated = cleaned.substring(0, maxLength);

        // Ищем последний пробел чтобы не обрезать слово
        const lastSpace = truncated.lastIndexOf(' ');

        if (lastSpace > maxLength * 0.8) {
            // Если пробел близко к концу, обрезаем по нему
            return truncated.substring(0, lastSpace) + '...';
        }

        // Иначе просто добавляем многоточие
        return truncated + '...';
    }

    /**
     * Форматировать дату для отображения
     * @param {string} dateString - ISO timestamp
     * @returns {string}
     */
    formatDate(dateString) {
        const date = new Date(dateString);

        // Формат: дд.мм.гггг
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        return `${day}.${month}.${year}`;
    }

    // ===== СТАТИСТИКА =====

    /**
     * Получить общее количество сохраненных хайлайтов
     * @returns {number}
     */
    getTotalSavedCount() {
        const saved = this._getAllSaved();
        let total = 0;
        for (const sessionId in saved) {
            total += saved[sessionId].length;
        }
        return total;
    }

    /**
     * Получить статистику по сессии
     * @param {string} sessionId
     * @returns {object}
     */
    getSessionStats(sessionId) {
        const session = this.getSession(sessionId);
        const highlights = this.getSavedHighlights(sessionId);

        return {
            session_id: sessionId,
            created_at: session ? session.created_at : null,
            page: session ? session.page : null,
            total_highlights: highlights.length,
            words: highlights.filter(h => !h.highlight.includes(' ')).length,
            expressions: highlights.filter(h => h.highlight.includes(' ')).length
        };
    }

    // ===== ОЧИСТКА =====

    /**
     * Удалить все данные (для тестирования)
     */
    clearAll() {
        localStorage.removeItem(this.KEYS.SESSIONS);
        localStorage.removeItem(this.KEYS.SAVED);
        localStorage.removeItem(this.KEYS.LAST_ANALYSIS);
        console.log('🧹 Все данные очищены');
    }

    /**
     * Экспорт данных (для бэкапа)
     * @returns {object}
     */
    exportData() {
        return {
            sessions: this.getAllSessions(),
            saved: this._getAllSaved(),
            last_analysis: this.getLastAnalysis(),
            exported_at: new Date().toISOString()
        };
    }

    /**
     * Импорт данных (восстановление из бэкапа)
     * @param {object} data
     */
    importData(data) {
        if (data.sessions) {
            localStorage.setItem(this.KEYS.SESSIONS, JSON.stringify(data.sessions));
        }
        if (data.saved) {
            localStorage.setItem(this.KEYS.SAVED, JSON.stringify(data.saved));
        }
        if (data.last_analysis) {
            localStorage.setItem(this.KEYS.LAST_ANALYSIS, JSON.stringify(data.last_analysis));
        }
        console.log('📥 Данные импортированы');
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HighlightsStorage;
}
