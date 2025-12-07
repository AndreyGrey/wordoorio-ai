/**
 * 🎨 LOADING ANIMATION COMPONENT V1
 *
 * Радостная анимация загрузки для всех страниц
 * Показывает процесс анализа и поиска интересных слов
 */

/**
 * Создает HTML разметку анимации загрузки
 * @param {string} titleLine1 - Первая строка заголовка
 * @param {string} titleLine2 - Вторая строка заголовка (основная)
 * @param {string} message - Сообщение под анимацией
 * @returns {string} HTML разметка
 */
function createLoadingAnimationHTML(
    titleLine1 = 'АНАЛИЗИРУЮ И СОБИРАЮ',
    titleLine2 = 'КРУТУЮ ЛЕКСИКУ',
    message = 'Скоро откроем что-то интересное!'
) {
    return `
        <div id="loadingOverlay" class="loading-overlay">
            <div class="sparkles-bg" id="sparklesBg"></div>
            <div class="letters-rain" id="lettersRain"></div>

            <div class="loading-animation">
                <div class="discovery-title">
                    <span class="title-line-1">${titleLine1}</span><br>
                    <span class="title-line-2">${titleLine2}</span>
                </div>

                <div class="word-discovery" id="wordDiscovery">
                    <div class="mystery-cards" id="mysteryCards">
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                        <div class="mystery-card"></div>
                    </div>
                    <div class="book-pages">
                        <div class="page"></div>
                        <div class="page"></div>
                        <div class="page"></div>
                    </div>
                    <div class="lightbulb">💡</div>
                </div>

                <div class="excitement-message">${message}</div>

                <div class="discovery-dots">
                    <div class="discovery-dot"></div>
                    <div class="discovery-dot"></div>
                    <div class="discovery-dot"></div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Возвращает CSS стили для анимации загрузки
 * @returns {string} CSS стили
 */
function getLoadingAnimationStyles() {
    return `
        /* ===== LOADING ANIMATION STYLES V1 ===== */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(200, 227, 191, 0.95);
            backdrop-filter: blur(10px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            overflow: hidden;
        }

        .sparkles-bg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        .sparkle {
            position: absolute;
            color: #4CAF50;
            font-size: 20px;
            animation: sparkle-twinkle 3s ease-in-out infinite;
            opacity: 0;
        }

        @keyframes sparkle-twinkle {
            0%, 100% {
                opacity: 0;
                transform: scale(0) rotate(0deg);
            }
            50% {
                opacity: 1;
                transform: scale(1.2) rotate(180deg);
            }
        }

        .loading-animation {
            text-align: center;
            position: relative;
            z-index: 10;
        }

        .discovery-title {
            font-family: 'Poppins', 'Inter', sans-serif;
            font-size: 2.4rem;
            font-weight: 600;
            margin-bottom: 30px;
            color: #2d3748;
            animation: happy-bounce 2s ease-in-out infinite;
            text-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
            letter-spacing: 1px;
            line-height: 1.4;
            text-align: center;
        }

        .title-line-1 {
            font-size: 2rem;
            font-weight: 500;
            color: #4a5568;
            display: block;
            margin-bottom: 8px;
        }

        .title-line-2 {
            font-size: 2.8rem;
            font-weight: 700;
            color: #4CAF50;
            display: block;
            position: relative;
            animation: title-glow 3s ease-in-out infinite;
        }

        @keyframes title-glow {
            0%, 100% {
                text-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
                transform: scale(1);
            }
            50% {
                text-shadow: 0 4px 20px rgba(76, 175, 80, 0.6);
                transform: scale(1.02);
            }
        }

        @keyframes happy-bounce {
            0%, 100% {
                transform: translateY(0) scale(1);
            }
            50% {
                transform: translateY(-10px) scale(1.05);
            }
        }

        .word-discovery {
            position: relative;
            width: 500px;
            height: 300px;
            margin: 40px auto;
        }

        .flying-word {
            position: absolute;
            font-size: 1.5rem;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 20px;
            background: linear-gradient(135deg, #4CAF50, #81C784);
            color: white;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            animation: word-discovery-dance 4s ease-in-out infinite;
            opacity: 0;
        }

        @keyframes word-discovery-dance {
            0% {
                opacity: 0;
                transform: translateY(50px) scale(0.8) rotate(-10deg);
            }
            25% {
                opacity: 1;
                transform: translateY(0) scale(1) rotate(0deg);
            }
            75% {
                opacity: 1;
                transform: translateY(-20px) scale(1.1) rotate(5deg);
            }
            100% {
                opacity: 0;
                transform: translateY(-80px) scale(0.8) rotate(10deg);
            }
        }

        .letters-rain {
            position: absolute;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        .letter-drop {
            position: absolute;
            font-size: 2rem;
            font-weight: 600;
            color: #4CAF50;
            opacity: 0.7;
            animation: letter-fall 5s linear infinite;
            font-family: 'Inter', sans-serif;
        }

        @keyframes letter-fall {
            0% {
                transform: translateY(-50px) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 0.7;
            }
            90% {
                opacity: 0.7;
            }
            100% {
                transform: translateY(400px) rotate(360deg);
                opacity: 0;
            }
        }

        .excitement-message {
            font-size: 1.3rem;
            font-weight: 600;
            color: #2d3748;
            margin-top: 40px;
            animation: excitement-pulse 1.8s ease-in-out infinite;
        }

        @keyframes excitement-pulse {
            0%, 100% {
                transform: scale(1);
                color: #2d3748;
            }
            50% {
                transform: scale(1.08);
                color: #4CAF50;
            }
        }

        .discovery-dots {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 30px;
        }

        .discovery-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            margin: 0 8px;
            animation: dot-bounce 1.4s ease-in-out infinite;
        }

        .discovery-dot:nth-child(1) { animation-delay: 0s; }
        .discovery-dot:nth-child(2) { animation-delay: 0.2s; }
        .discovery-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dot-bounce {
            0%, 80%, 100% {
                transform: scale(0.8) translateY(0);
                background: #4CAF50;
            }
            40% {
                transform: scale(1.2) translateY(-10px);
                background: #81C784;
            }
        }

        .mystery-cards {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            pointer-events: none;
        }

        .mystery-card {
            position: absolute;
            width: 25px;
            height: 35px;
            background: white;
            border: 2px solid #4CAF50;
            border-radius: 4px;
            box-shadow: 0 3px 8px rgba(76, 175, 80, 0.3);
            animation: mystery-reveal 5s ease-in-out infinite;
            opacity: 0;
        }

        /* Первая группа карточек - как будто слово из 6 букв */
        .mystery-card:nth-child(1) { animation-delay: 0s; top: 20%; left: 15%; }
        .mystery-card:nth-child(2) { animation-delay: 0.2s; top: 20%; left: 18%; }
        .mystery-card:nth-child(3) { animation-delay: 0.4s; top: 20%; left: 21%; }
        .mystery-card:nth-child(4) { animation-delay: 0.6s; top: 20%; left: 24%; }
        .mystery-card:nth-child(5) { animation-delay: 0.8s; top: 20%; left: 27%; }
        .mystery-card:nth-child(6) { animation-delay: 1.0s; top: 20%; left: 30%; }

        /* Вторая группа карточек - как будто слово из 8 букв */
        .mystery-card:nth-child(7) { animation-delay: 2s; bottom: 25%; right: 20%; }
        .mystery-card:nth-child(8) { animation-delay: 2.2s; bottom: 25%; right: 23%; }
        .mystery-card:nth-child(9) { animation-delay: 2.4s; bottom: 25%; right: 26%; }
        .mystery-card:nth-child(10) { animation-delay: 2.6s; bottom: 25%; right: 29%; }
        .mystery-card:nth-child(11) { animation-delay: 2.8s; bottom: 25%; right: 32%; }
        .mystery-card:nth-child(12) { animation-delay: 3.0s; bottom: 25%; right: 35%; }
        .mystery-card:nth-child(13) { animation-delay: 3.2s; bottom: 25%; right: 38%; }
        .mystery-card:nth-child(14) { animation-delay: 3.4s; bottom: 25%; right: 41%; }

        /* Третья группа - короткое слово из 4 букв */
        .mystery-card:nth-child(15) { animation-delay: 4.5s; top: 60%; left: 40%; }
        .mystery-card:nth-child(16) { animation-delay: 4.7s; top: 60%; left: 43%; }
        .mystery-card:nth-child(17) { animation-delay: 4.9s; top: 60%; left: 46%; }
        .mystery-card:nth-child(18) { animation-delay: 5.1s; top: 60%; left: 49%; }

        .book-pages {
            position: absolute;
            width: 80px;
            height: 100px;
            top: 50%;
            left: 20%;
            transform: translateY(-50%);
            opacity: 0.6;
        }

        .page {
            position: absolute;
            width: 60px;
            height: 80px;
            background: white;
            border: 2px solid #4CAF50;
            border-radius: 4px;
            animation: page-flip 3s ease-in-out infinite;
            transform-origin: left center;
        }

        .page:nth-child(1) { animation-delay: 0s; z-index: 3; }
        .page:nth-child(2) { animation-delay: 1s; z-index: 2; }
        .page:nth-child(3) { animation-delay: 2s; z-index: 1; }

        @keyframes mystery-reveal {
            0% {
                opacity: 0;
                transform: translateY(10px) rotateX(90deg);
                background: white;
            }
            20% {
                opacity: 1;
                transform: translateY(0) rotateX(0deg);
                background: white;
            }
            40% {
                transform: scale(1.1);
                background: #f0f8f0;
            }
            60% {
                transform: scale(1) rotateY(5deg);
                background: white;
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
            }
            80% {
                transform: rotateY(0deg);
                opacity: 1;
            }
            100% {
                opacity: 0;
                transform: translateY(-15px) rotateX(-90deg);
            }
        }

        @keyframes page-flip {
            0%, 80% {
                transform: rotateY(0deg);
            }
            90%, 100% {
                transform: rotateY(-180deg);
            }
        }

        .lightbulb {
            position: absolute;
            top: 20%;
            right: 20%;
            font-size: 3rem;
            animation: lightbulb-idea 2.5s ease-in-out infinite;
        }

        @keyframes lightbulb-idea {
            0%, 70% {
                transform: scale(1);
                filter: brightness(1);
            }
            85%, 100% {
                transform: scale(1.3);
                filter: brightness(1.5);
            }
        }

        /* ===== АДАПТИВНОСТЬ ===== */

        /* Планшеты (до 768px) */
        @media (max-width: 768px) {
            .discovery-title {
                font-size: 1.8rem;
                margin-bottom: 20px;
                padding: 0 10px;
            }

            .title-line-1 {
                font-size: 1.4rem;
            }

            .title-line-2 {
                font-size: 2rem;
            }

            .word-discovery {
                width: 95%;
                height: 200px;
                margin: 20px auto;
            }

            .mystery-card {
                width: 18px;
                height: 25px;
            }

            .flying-word {
                font-size: 1.1rem;
                padding: 6px 12px;
                max-width: 85%;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .excitement-message {
                font-size: 1.1rem;
                margin-top: 20px;
                padding: 0 15px;
            }

            .book-pages {
                width: 60px;
                height: 80px;
                left: 10%;
            }

            .page {
                width: 45px;
                height: 60px;
            }

            .lightbulb {
                font-size: 2rem;
                right: 15%;
            }
        }

        /* Мобильные (до 480px) */
        @media (max-width: 480px) {
            .discovery-title {
                font-size: 1.5rem;
            }

            .title-line-1 {
                font-size: 1.2rem;
            }

            .title-line-2 {
                font-size: 1.7rem;
            }

            .word-discovery {
                height: 150px;
            }

            .mystery-card {
                width: 15px;
                height: 20px;
            }

            .flying-word {
                font-size: 1rem;
                padding: 4px 8px;
            }

            .excitement-message {
                font-size: 1rem;
            }
        }
    `;
}

/**
 * Показывает анимацию загрузки
 * @param {string} inputText - Текст пользователя для извлечения интересных слов
 */
function showLoadingAnimation(inputText = '') {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        console.warn('Loading overlay not found. Make sure to inject HTML first.');
        return;
    }

    overlay.style.display = 'flex';

    // Запускаем блестки
    startSparkles();

    // Запускаем дождь из букв
    startLettersRain();

    // Запускаем летающие слова открытий из реального текста
    startDiscoveryWords(inputText);
}

/**
 * Скрывает анимацию загрузки
 */
function hideLoadingAnimation() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }

    // Очищаем все анимации
    clearDiscoveryAnimations();
}

/**
 * Запускает анимацию блесток
 */
function startSparkles() {
    const sparklesBg = document.getElementById('sparklesBg');
    if (!sparklesBg) return;

    const sparkleChars = ['✨', '⭐', '💫', '🌟', '✦', '✧', '⋆'];

    // Создаем блестки
    for (let i = 0; i < 30; i++) {
        setTimeout(() => {
            if (!document.getElementById('sparklesBg')) return;

            const sparkle = document.createElement('div');
            sparkle.className = 'sparkle';
            sparkle.textContent = sparkleChars[Math.floor(Math.random() * sparkleChars.length)];
            sparkle.style.left = Math.random() * 100 + '%';
            sparkle.style.top = Math.random() * 100 + '%';
            sparkle.style.animationDelay = Math.random() * 3 + 's';
            sparkle.style.animationDuration = (2 + Math.random() * 2) + 's';

            sparklesBg.appendChild(sparkle);

            // Удаляем блестку после анимации
            setTimeout(() => {
                if (sparkle.parentNode) {
                    sparkle.parentNode.removeChild(sparkle);
                }
            }, 4000);
        }, i * 150);
    }
}

/**
 * Запускает анимацию дождя из букв
 */
function startLettersRain() {
    const lettersRain = document.getElementById('lettersRain');
    if (!lettersRain) return;

    const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'];

    let letterIndex = 0;
    window.letterRainInterval = setInterval(() => {
        if (!lettersRain) return;

        const letter = document.createElement('div');
        letter.className = 'letter-drop';
        letter.textContent = letters[letterIndex % letters.length];
        letter.style.left = Math.random() * 100 + '%';
        letter.style.animationDelay = Math.random() * 2 + 's';
        letter.style.animationDuration = (4 + Math.random() * 2) + 's';

        lettersRain.appendChild(letter);
        letterIndex++;

        // Удаляем букву после анимации
        setTimeout(() => {
            if (letter.parentNode) {
                letter.parentNode.removeChild(letter);
            }
        }, 6000);
    }, 400);
}

/**
 * Запускает анимацию открытия слов
 * @param {string} inputText - Текст пользователя
 */
function startDiscoveryWords(inputText) {
    const wordDiscovery = document.getElementById('wordDiscovery');
    if (!wordDiscovery) return;

    // Извлекаем интересные слова из текста пользователя
    let discoveryWords = extractInterestingWords(inputText);

    // Добавляем более интересные и длинные слова
    const sophisticatedWords = [
        'orchestration', 'infrastructure', 'methodology', 'implementation',
        'sophisticated', 'comprehensive', 'extraordinary', 'revolutionary',
        'architecture', 'performance', 'optimization', 'transformation',
        'collaboration', 'integration', 'visualization', 'authentication',
        'personalization', 'configuration', 'administration', 'specification',
        'documentation', 'localization', 'internationalization', 'communication',
        'representation', 'interpretation', 'understanding', 'investigation',
        'conversation', 'information', 'explanation', 'demonstration'
    ];

    // Если не нашли достаточно слов, добавляем дефолтные длинные слова
    if (discoveryWords.length < 12) {
        const shuffledSophisticated = sophisticatedWords.sort(() => Math.random() - 0.5);
        discoveryWords = [...discoveryWords, ...shuffledSophisticated].slice(0, 20);
    }

    let wordIndex = 0;
    window.discoveryWordsInterval = setInterval(() => {
        if (!wordDiscovery) return;

        // Создаем 2-3 слова одновременно для более насыщенной анимации
        const wordsToCreate = Math.floor(Math.random() * 3) + 1;

        for (let i = 0; i < wordsToCreate; i++) {
            const wordElement = document.createElement('div');
            wordElement.className = 'flying-word';
            wordElement.textContent = discoveryWords[wordIndex % discoveryWords.length];

            // Адаптивные позиции в зависимости от размера экрана
            const isMobile = window.innerWidth <= 768;
            const positions = isMobile ? [
                { left: '15%', top: '30%' },
                { left: '50%', top: '15%' },
                { left: '75%', top: '45%' },
                { left: '30%', top: '70%' },
                { left: '65%', top: '25%' },
                { left: '20%', top: '55%' }
            ] : [
                { left: '5%', top: '25%' },
                { left: '25%', top: '15%' },
                { left: '45%', top: '35%' },
                { left: '65%', top: '20%' },
                { left: '85%', top: '40%' },
                { left: '15%', top: '65%' },
                { left: '75%', top: '70%' },
                { left: '35%', top: '75%' },
                { left: '55%', top: '55%' },
                { left: '10%', top: '45%' }
            ];

            const pos = positions[Math.floor(Math.random() * positions.length)];
            wordElement.style.left = pos.left;
            wordElement.style.top = pos.top;
            wordElement.style.animationDelay = (Math.random() * 2 + i * 0.3) + 's';

            // Адаптивный размер шрифта
            if (isMobile) {
                wordElement.style.fontSize = '1.1rem';
                wordElement.style.padding = '6px 12px';
            }

            wordDiscovery.appendChild(wordElement);
            wordIndex++;

            // Удаляем слово после анимации
            setTimeout(() => {
                if (wordElement.parentNode) {
                    wordElement.parentNode.removeChild(wordElement);
                }
            }, 5000);
        }
    }, 800); // Более частое появление слов
}

/**
 * Извлекает интересные слова из текста
 * @param {string} text - Исходный текст
 * @returns {Array<string>} Массив интересных слов
 */
function extractInterestingWords(text) {
    if (!text) return [];

    // Простые слова, которые не интересны
    const boringWords = new Set([
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'get', 'got', 'use', 'used', 'make', 'made', 'see', 'come', 'go',
        'know', 'take', 'give', 'think', 'way', 'work', 'time', 'good', 'new',
        'first', 'last', 'long', 'great', 'little', 'right', 'old', 'try'
    ]);

    // Извлекаем слова и фильтруем
    const words = text.toLowerCase()
        .replace(/[^\w\s]/g, ' ') // убираем пунктуацию
        .split(/\s+/)
        .filter(word =>
            word.length >= 6 && // минимум 6 букв для более интересных слов
            word.length <= 16 && // максимум 16 букв
            !boringWords.has(word) && // не скучные
            /^[a-z]+$/.test(word) // только английские буквы
        );

    // Сортируем по длине (длинные слова интереснее)
    const sortedWords = words.sort((a, b) => b.length - a.length);

    // Убираем дубликаты и берем самые длинные
    const uniqueWords = [...new Set(sortedWords)];

    // Берем топ слова по длине и перемешиваем
    return uniqueWords.slice(0, 15);
}

/**
 * Очищает все анимации
 */
function clearDiscoveryAnimations() {
    // Очищаем все интервалы
    if (window.letterRainInterval) {
        clearInterval(window.letterRainInterval);
    }
    if (window.discoveryWordsInterval) {
        clearInterval(window.discoveryWordsInterval);
    }

    // Очищаем контейнеры
    const sparklesBg = document.getElementById('sparklesBg');
    const lettersRain = document.getElementById('lettersRain');
    const wordDiscovery = document.getElementById('wordDiscovery');

    if (sparklesBg) sparklesBg.innerHTML = '';
    if (lettersRain) lettersRain.innerHTML = '';

    // Очищаем только динамические элементы, сохраняя статичные
    if (wordDiscovery) {
        const dynamicWords = wordDiscovery.querySelectorAll('.flying-word');
        dynamicWords.forEach(word => word.remove());
    }
}

// Автоматическая инициализация при загрузке скрипта
(function() {
    // Инжектим стили сразу
    const styleTag = document.createElement('style');
    styleTag.innerHTML = getLoadingAnimationStyles();
    document.head.appendChild(styleTag);

    // Инжектим HTML сразу (не ждем DOMContentLoaded)
    const loadingHTML = createLoadingAnimationHTML(
        'АНАЛИЗИРУЮ И СОБИРАЮ',
        'КРУТУЮ ЛЕКСИКУ',
        'Скоро откроем что-то интересное!'
    );

    // Если DOM еще не готов, ждем его
    if (document.body) {
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            document.body.insertAdjacentHTML('beforeend', loadingHTML);
        });
    }
})();

// Экспортируем функции (если используется модульная система)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createLoadingAnimationHTML,
        getLoadingAnimationStyles,
        showLoadingAnimation,
        hideLoadingAnimation
    };
}
