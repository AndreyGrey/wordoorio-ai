/*!
 * 🎨 WORDOORIO LOADING ANIMATION
 * Универсальный компонент анимации загрузки для всех страниц
 * 
 * Особенности:
 * - Извлекает слова из пользовательского текста
 * - Адаптивная анимация под разные устройства
 * - Единый дизайн для всего проекта
 */

class WordoorioLoadingAnimation {
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        this.words = [];
        this.currentWordIndex = 0;
        this.isAnimating = false;
        this.animationInterval = null;
        
        // Настройки анимации
        this.config = {
            wordChangeInterval: 800,     // Смена слова каждые 800мс
            maxWordsToShow: 20,         // Максимум слов для показа
            minWordLength: 3,           // Минимальная длина слова
            progressMaxPercent: 90,     // Максимальный прогресс (не доходим до 100%)
            fallbackWords: ['analyzing', 'processing', 'thinking', 'working', 'parsing']
        };
        
        // Инициализируем CSS если его еще нет
        this.ensureStylesLoaded();
    }
    
    /**
     * Показать анимацию загрузки
     * @param {string} userText - Текст пользователя для извлечения слов
     * @param {string} loadingMessage - Сообщение загрузки (по умолчанию "Анализирую...")
     */
    show(userText, loadingMessage = "Анализирую...") {
        this.extractWordsFromText(userText);
        this.isAnimating = true;
        this.renderLoadingInterface(loadingMessage);
        this.startWordAnimation();
    }
    
    /**
     * Скрыть анимацию
     */
    hide() {
        this.isAnimating = false;
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }
        
        // Плавное исчезновение
        if (this.container) {
            this.container.style.opacity = '0';
            setTimeout(() => {
                this.container.innerHTML = '';
                this.container.style.opacity = '1';
            }, 300);
        }
    }
    
    /**
     * Обновить прогресс загрузки
     * @param {number} percent - Процент от 0 до 100
     */
    updateProgress(percent) {
        const progressBar = document.getElementById('wordoorio-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${Math.min(percent, this.config.progressMaxPercent)}%`;
        }
    }
    
    /**
     * Обновить сообщение загрузки
     * @param {string} message - Новое сообщение
     */
    updateMessage(message) {
        const messageElement = document.getElementById('wordoorio-loading-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
    
    /**
     * Извлекает слова из пользовательского текста
     * @param {string} text - Исходный текст пользователя
     */
    extractWordsFromText(text) {
        if (!text || typeof text !== 'string') {
            this.words = [...this.config.fallbackWords];
            return;
        }
        
        // Извлекаем английские слова подходящей длины
        const extractedWords = text
            .toLowerCase()
            .match(/\\b[a-z]{3,}\\b/g);
        
        if (extractedWords && extractedWords.length > 0) {
            // Убираем дубликаты и берем первые N слов
            this.words = [...new Set(extractedWords)]
                .slice(0, this.config.maxWordsToShow);
        } else {
            // Если не удалось извлечь слова, используем fallback
            this.words = [...this.config.fallbackWords];
        }
        
        // Перемешиваем слова для разнообразия
        this.shuffleArray(this.words);
    }
    
    /**
     * Создает HTML интерфейс загрузки
     * @param {string} loadingMessage - Сообщение загрузки
     */
    renderLoadingInterface(loadingMessage) {
        this.container.innerHTML = `
            <div class="wordoorio-loading-container">
                <!-- Мозг-иконка с анимацией пульсации -->
                <div class="wordoorio-brain-icon">🧠</div>
                
                <!-- Основное сообщение -->
                <div class="wordoorio-loading-message" id="wordoorio-loading-message">
                    ${loadingMessage}
                </div>
                
                <!-- Текущее анализируемое слово -->
                <div class="wordoorio-current-word" id="wordoorio-current-word">
                    ${this.words[0] || 'processing'}
                </div>
                
                <!-- Прогресс-бар -->
                <div class="wordoorio-progress-container">
                    <div class="wordoorio-progress-bar" id="wordoorio-progress-bar"></div>
                </div>
                
                <!-- Дополнительная информация -->
                <div class="wordoorio-loading-hint">
                    Ищем выразительную лексику в вашем тексте...
                </div>
            </div>
        `;
    }
    
    /**
     * Запускает анимацию смены слов
     */
    startWordAnimation() {
        const wordElement = document.getElementById('wordoorio-current-word');
        const progressBar = document.getElementById('wordoorio-progress-bar');
        
        if (!wordElement || !this.isAnimating) return;
        
        this.animationInterval = setInterval(() => {
            if (!this.isAnimating) {
                clearInterval(this.animationInterval);
                return;
            }
            
            // Получаем текущее слово
            const currentWord = this.words[this.currentWordIndex];
            
            // Анимация смены слова
            wordElement.style.opacity = '0';
            wordElement.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                wordElement.textContent = currentWord;
                wordElement.style.opacity = '1';
                wordElement.style.transform = 'translateY(0)';
                
                // Добавляем bounce эффект
                wordElement.style.animation = 'none';
                setTimeout(() => {
                    wordElement.style.animation = 'wordoorio-word-bounce 0.6s ease-out';
                }, 10);
            }, 200);
            
            // Обновляем прогресс
            const progress = ((this.currentWordIndex + 1) / this.words.length) * this.config.progressMaxPercent;
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            
            // Переходим к следующему слову
            this.currentWordIndex = (this.currentWordIndex + 1) % this.words.length;
            
        }, this.config.wordChangeInterval);
    }
    
    /**
     * Перемешивает массив (Fisher-Yates shuffle)
     * @param {Array} array - Массив для перемешивания
     */
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
    
    /**
     * Убеждается что CSS стили загружены
     */
    ensureStylesLoaded() {
        if (document.getElementById('wordoorio-loading-styles')) {
            return; // Стили уже загружены
        }
        
        const styleElement = document.createElement('style');
        styleElement.id = 'wordoorio-loading-styles';
        styleElement.textContent = this.getCSS();
        document.head.appendChild(styleElement);
    }
    
    /**
     * Возвращает CSS стили для анимации
     * @returns {string} CSS код
     */
    getCSS() {
        return `
            .wordoorio-loading-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                text-align: center;
                min-height: 200px;
            }
            
            .wordoorio-brain-icon {
                font-size: 4rem;
                margin-bottom: 20px;
                animation: wordoorio-brain-pulse 2s ease-in-out infinite;
                filter: drop-shadow(0 4px 8px rgba(76, 175, 80, 0.3));
            }
            
            .wordoorio-loading-message {
                font-size: 1.3rem;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 15px;
                letter-spacing: 0.5px;
            }
            
            .wordoorio-current-word {
                font-size: 1.1rem;
                font-weight: 700;
                color: #4CAF50;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 15px 0;
                padding: 8px 16px;
                background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(69, 160, 73, 0.1));
                border-radius: 20px;
                border: 2px solid rgba(76, 175, 80, 0.2);
                min-width: 120px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .wordoorio-current-word::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -100%;
                width: 100%;
                height: calc(100% + 4px);
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                transition: left 0.5s;
            }
            
            .wordoorio-current-word:hover::before {
                left: 100%;
            }
            
            .wordoorio-progress-container {
                width: 250px;
                height: 4px;
                background: linear-gradient(90deg, #e2e8f0, #cbd5e0);
                border-radius: 2px;
                margin: 20px 0;
                overflow: hidden;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .wordoorio-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50, #45A049, #66BB6A);
                border-radius: 2px;
                transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                width: 0%;
                position: relative;
                overflow: hidden;
            }
            
            .wordoorio-progress-bar::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(255, 255, 255, 0.6), 
                    transparent
                );
                animation: wordoorio-shimmer 2s infinite linear;
            }
            
            .wordoorio-loading-hint {
                font-size: 0.9rem;
                color: #718096;
                margin-top: 15px;
                font-style: italic;
                opacity: 0.8;
            }
            
            /* Анимации */
            @keyframes wordoorio-brain-pulse {
                0%, 100% { 
                    transform: scale(1); 
                    opacity: 1;
                }
                50% { 
                    transform: scale(1.1); 
                    opacity: 0.8;
                }
            }
            
            @keyframes wordoorio-word-bounce {
                0% { transform: translateY(-10px) scale(0.95); opacity: 0.7; }
                50% { transform: translateY(-2px) scale(1.05); opacity: 1; }
                100% { transform: translateY(0) scale(1); opacity: 1; }
            }
            
            @keyframes wordoorio-shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(200%); }
            }
            
            /* Адаптивность */
            @media (max-width: 768px) {
                .wordoorio-loading-container {
                    padding: 30px 15px;
                }
                
                .wordoorio-brain-icon {
                    font-size: 3rem;
                }
                
                .wordoorio-loading-message {
                    font-size: 1.1rem;
                }
                
                .wordoorio-current-word {
                    font-size: 1rem;
                    min-width: 100px;
                }
                
                .wordoorio-progress-container {
                    width: 200px;
                }
            }
            
            @media (max-width: 480px) {
                .wordoorio-progress-container {
                    width: 150px;
                }
                
                .wordoorio-loading-hint {
                    font-size: 0.8rem;
                }
            }
            
            /* Темная тема (опционально) */
            @media (prefers-color-scheme: dark) {
                .wordoorio-loading-message {
                    color: #f7fafc;
                }
                
                .wordoorio-loading-hint {
                    color: #a0aec0;
                }
                
                .wordoorio-progress-container {
                    background: linear-gradient(90deg, #4a5568, #2d3748);
                }
            }
        `;
    }
}

// Экспортируем для использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WordoorioLoadingAnimation;
} else {
    window.WordoorioLoadingAnimation = WordoorioLoadingAnimation;
}

// Удобная функция для быстрого создания
window.createWordoorioLoader = function(containerSelector) {
    return new WordoorioLoadingAnimation(containerSelector);
};