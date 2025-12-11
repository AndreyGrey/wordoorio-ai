/**
 * Auth.js
 * Управление авторизацией через Telegram Login Widget
 */

class Auth {
    constructor() {
        this.currentUser = null;
        this.onAuthChangeCallbacks = [];
    }

    /**
     * Инициализация - проверяет текущего пользователя
     */
    async init() {
        try {
            const response = await fetch('/api/auth/current');
            const data = await response.json();

            if (data.success && data.user) {
                this.currentUser = data.user;
                this.notifyAuthChange(true);
            } else {
                this.currentUser = null;
                this.notifyAuthChange(false);
            }
        } catch (error) {
            console.error('Ошибка проверки авторизации:', error);
            this.currentUser = null;
            this.notifyAuthChange(false);
        }
    }

    /**
     * Проверяет авторизован ли пользователь
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }

    /**
     * Получить текущего пользователя
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Обработка авторизации через Telegram
     * Вызывается из Telegram Login Widget callback
     */
    async handleTelegramAuth(telegramData) {
        try {
            const response = await fetch('/api/auth/telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(telegramData)
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = data.user;
                this.notifyAuthChange(true);
                return { success: true, user: data.user };
            } else {
                console.error('Ошибка авторизации:', data.error);
                return { success: false, error: data.error };
            }
        } catch (error) {
            console.error('Ошибка авторизации:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Выход из системы
     */
    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = null;
                this.notifyAuthChange(false);
                return { success: true };
            }
        } catch (error) {
            console.error('Ошибка выхода:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Подписка на изменения авторизации
     */
    onAuthChange(callback) {
        this.onAuthChangeCallbacks.push(callback);
    }

    /**
     * Уведомление подписчиков об изменении авторизации
     */
    notifyAuthChange(isAuthenticated) {
        this.onAuthChangeCallbacks.forEach(callback => {
            callback(isAuthenticated, this.currentUser);
        });
    }
}

// Создаем глобальный экземпляр
window.auth = new Auth();

// Callback для Telegram Login Widget
window.onTelegramAuth = async function(user) {
    console.log('Telegram auth callback:', user);

    const result = await window.auth.handleTelegramAuth(user);

    if (result.success) {
        showNotification('Вы успешно авторизованы! ✓');

        // Перезагружаем страницу для обновления header
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    } else {
        showNotification('Ошибка авторизации: ' + result.error, 'error');
    }
};

// Вспомогательная функция для уведомлений
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#fed7d7' : '#c6f6d5'};
        color: ${type === 'error' ? '#c53030' : '#22543d'};
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
