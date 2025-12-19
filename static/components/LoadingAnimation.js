/**
 * 🎨 LOADING ANIMATION COMPONENT V4
 *
 * Wordoorio — AI-powered анализ выразительной английской лексики
 * Анимация загрузки с динамическими статусами
 */

// ========== СТАТУСЫ ==========
const STATUS_MESSAGES = [
    'LAUNCHING THE SYSTEM',
    'CONNECTING TO AI-AGENTS',
    'SCANNING YOUR TEXT',
    'HUNTING FOR COOL EXPRESSIONS',
    'AI-AGENTS ARE WORKING HARD',
    'PICKING UP SOME GOOD STUFF',
    'CHECKING WORD CONTEXTS',
    'LEMMATIZING & CLEANING UP',
    'CONSULTING DICTIONARIES',
    'POLISHING THE RESULTS',
    // После 10-й — цикл 11-14
    'ALMOST THERE...',
    'JUST A FEW MORE SECONDS',
    'TAKING A BIT LONGER, HANG TIGHT',
    'STILL CRUNCHING, WORTH THE WAIT'
];

let currentStatusIndex = 0;
let statusInterval = null;

/**
 * Создает HTML разметку анимации загрузки
 * @returns {string} HTML разметка
 */
function createLoadingAnimationHTML() {
    return `
        <div id="loadingOverlay" class="loading-overlay">
            <div class="sparkles-bg" id="sparklesBg"></div>
            <div class="letters-rain" id="lettersRain"></div>

            <div class="loading-animation">
                <div class="discovery-title">
                    <span class="title-line-1">
                        <span class="w-symbol w-left">
                            <span class="slash-char" data-char="1">\\</span><span class="slash-char" data-char="2">/</span><span class="slash-char" data-char="3">\\</span><span class="slash-char" data-char="4">/</span>
                        </span>
                        <span class="title-text">Wordoorio loves you!</span>
                        <span class="w-symbol w-right">
                            <span class="slash-char" data-char="5">\\</span><span class="slash-char" data-char="6">/</span><span class="slash-char" data-char="7">\\</span><span class="slash-char" data-char="8">/</span>
                        </span>
                    </span>
                    <span class="title-line-2">LET'S SPOT SOME JUICY WORDS</span>
                </div>

                <div class="word-discovery" id="wordDiscovery">
                    <!-- Область для летающих слов -->
                </div>

                <div class="excitement-message-container" id="statusContainer">
                    <!-- Статусы добавляются динамически -->
                </div>

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
        /* ===== LOADING ANIMATION STYLES V4 ===== */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(200, 227, 191, 0.80);
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
            color: #39A0B3;
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
            color: #0A3A4D;
            animation: happy-bounce 2s ease-in-out infinite;
            text-shadow: 0 2px 8px rgba(57, 160, 179, 0.2);
            letter-spacing: 1px;
            line-height: 1.4;
            text-align: center;
        }

        .title-line-1 {
            font-size: 1.6rem;
            font-weight: 500;
            color: #39A0B3;
            display: block;
            margin-bottom: 8px;
        }

        .title-text {
            display: inline;
            color: #39A0B3;
        }

        /* ===== W-SYMBOL ANIMATION ===== */
        .w-symbol {
            display: inline-block;
            position: relative;
            margin: 0 5px;
        }

        .slash-char {
            display: inline-block;
            font-weight: 700;
            color: #39A0B3;
            transition: all 0.3s ease;
            animation: slash-dance 4s ease-in-out infinite;
        }

        .slash-char[data-char="1"] { animation-delay: 0s; }
        .slash-char[data-char="2"] { animation-delay: 0.1s; }
        .slash-char[data-char="3"] { animation-delay: 0.2s; }
        .slash-char[data-char="4"] { animation-delay: 0.3s; }
        .slash-char[data-char="5"] { animation-delay: 0s; }
        .slash-char[data-char="6"] { animation-delay: 0.1s; }
        .slash-char[data-char="7"] { animation-delay: 0.2s; }
        .slash-char[data-char="8"] { animation-delay: 0.3s; }

        @keyframes slash-dance {
            0% {
                transform: translateY(0) rotate(0deg) scale(1);
                opacity: 1;
            }
            15% {
                transform: translateY(-12px) rotate(-15deg) scale(1.2);
            }
            30% {
                transform: translateY(5px) rotate(10deg) scale(0.9);
            }
            45%, 55% {
                transform: translateY(0) rotate(0deg) scale(1.1);
                opacity: 1;
                text-shadow: 0 0 10px #39A0B3, 0 0 20px #39A0B3;
            }
            70% {
                transform: translateY(-8px) rotate(12deg) scale(1.15);
            }
            85% {
                transform: translateY(3px) rotate(-8deg) scale(0.95);
            }
            100% {
                transform: translateY(0) rotate(0deg) scale(1);
                opacity: 1;
            }
        }

        .w-symbol {
            animation: w-pulse 4s ease-in-out infinite;
        }

        @keyframes w-pulse {
            0%, 40%, 60%, 100% {
                filter: drop-shadow(0 0 0 transparent);
            }
            45%, 55% {
                filter: drop-shadow(0 0 15px rgba(57, 160, 179, 0.6));
            }
        }

        .title-line-2 {
            font-size: 2.8rem;
            font-weight: 700;
            color: #FF7964;
            display: block;
            position: relative;
            animation: title-glow 3s ease-in-out infinite;
        }

        @keyframes title-glow {
            0%, 100% {
                text-shadow: 0 2px 8px rgba(255, 121, 100, 0.3);
                transform: scale(1);
            }
            50% {
                text-shadow: 0 4px 20px rgba(255, 121, 100, 0.6);
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
            background: linear-gradient(135deg, #39A0B3, #1B7A94);
            color: white;
            box-shadow: 0 4px 15px rgba(57, 160, 179, 0.3);
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
            color: #A4CE96;
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

        /* ===== EXCITEMENT MESSAGE — FERRARI EFFECT ===== */
        .excitement-message-container {
            position: relative;
            height: 60px;
            margin-top: 40px;
            overflow: hidden;
        }

        .excitement-message {
            position: absolute;
            width: 100%;
            font-size: 1.4rem;
            font-weight: 700;
            color: #0A3A4D;
            white-space: nowrap;
            text-align: center;
            left: 0;
        }

        @keyframes ferrari-enter {
            0% {
                transform: translateX(120%) scale(0.8);
                opacity: 0;
            }
            8% {
                transform: translateX(20%) scale(1);
                opacity: 1;
            }
            12% {
                transform: translateX(-3%) scale(1.05);
            }
            16% {
                transform: translateX(0) scale(1.15);
            }
            20% {
                transform: translateX(0) scale(1.1);
            }
            22% { transform: translateX(2px) scale(1.1); }
            24% { transform: translateX(-2px) scale(1.1); }
            26% { transform: translateX(1px) scale(1.1); }
            28% { transform: translateX(-1px) scale(1.1); }
            30% { transform: translateX(0) scale(1.1); }
            35% { transform: translateX(0) scale(1.08); color: #39A0B3; }
            45% { transform: translateX(0) scale(1.12); color: #0A3A4D; }
            55% { transform: translateX(0) scale(1.08); color: #39A0B3; }
            65% { transform: translateX(0) scale(1.1); color: #0A3A4D; }
            75% { transform: translateX(0) scale(1.08); color: #39A0B3; }
            82% {
                transform: translateX(0) scale(1.1);
                opacity: 1;
            }
            100% {
                transform: translateX(-120%) scale(0.9);
                opacity: 0;
            }
        }

        .excitement-message.ferrari {
            animation: ferrari-enter 8s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
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
            background: #39A0B3;
            margin: 0 8px;
            animation: dot-bounce 1.4s ease-in-out infinite;
        }

        .discovery-dot:nth-child(1) { animation-delay: 0s; }
        .discovery-dot:nth-child(2) { animation-delay: 0.2s; }
        .discovery-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dot-bounce {
            0%, 80%, 100% {
                transform: scale(0.8) translateY(0);
                background: #39A0B3;
            }
            40% {
                transform: scale(1.2) translateY(-10px);
                background: #1B7A94;
            }
        }

        /* ===== АДАПТИВНОСТЬ ===== */
        @media (max-width: 768px) {
            .discovery-title {
                font-size: 1.8rem;
                margin-bottom: 20px;
                padding: 0 10px;
            }

            .title-line-1 {
                font-size: 1.2rem;
            }

            .title-line-2 {
                font-size: 2rem;
            }

            .word-discovery {
                width: 95%;
                height: 200px;
                margin: 20px auto;
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
            }
        }

        @media (max-width: 480px) {
            .discovery-title {
                font-size: 1.5rem;
            }

            .title-line-1 {
                font-size: 1rem;
            }

            .title-line-2 {
                font-size: 1.7rem;
            }

            .word-discovery {
                height: 150px;
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
 * Показывает следующий статус с эффектом "Феррари"
 */
function showNextStatus() {
    const container = document.getElementById('statusContainer');
    if (!container) return;

    let index;
    if (currentStatusIndex < 10) {
        index = currentStatusIndex;
    } else {
        index = 10 + ((currentStatusIndex - 10) % 4);
    }

    const newMessage = document.createElement('div');
    newMessage.className = 'excitement-message ferrari';
    newMessage.textContent = STATUS_MESSAGES[index];
    
    container.appendChild(newMessage);
    currentStatusIndex++;

    setTimeout(() => {
        if (newMessage.parentNode) {
            newMessage.remove();
        }
    }, 8000);
}

/**
 * Запускает цикл статусов
 */
function startStatusCycle() {
    currentStatusIndex = 0;
    showNextStatus();
    
    statusInterval = setInterval(() => {
        showNextStatus();
    }, 6500);
}

/**
 * Останавливает цикл статусов
 */
function stopStatusCycle() {
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    currentStatusIndex = 0;
    
    const container = document.getElementById('statusContainer');
    if (container) {
        container.innerHTML = '';
    }
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

    startSparkles();
    startLettersRain();
    startDiscoveryWords(inputText);
    startStatusCycle();
}

/**
 * Скрывает анимацию загрузки
 */
function hideLoadingAnimation() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }

    clearDiscoveryAnimations();
    stopStatusCycle();
}

/**
 * Запускает анимацию блесток
 */
function startSparkles() {
    const sparklesBg = document.getElementById('sparklesBg');
    if (!sparklesBg) return;

    const sparkleChars = ['✨', '⭐', '💫', '🌟', '✦', '✧', '⋆'];

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

    let discoveryWords = extractInterestingWords(inputText);

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

    if (discoveryWords.length < 12) {
        const shuffledSophisticated = sophisticatedWords.sort(() => Math.random() - 0.5);
        discoveryWords = [...discoveryWords, ...shuffledSophisticated].slice(0, 20);
    }

    let wordIndex = 0;
    window.discoveryWordsInterval = setInterval(() => {
        if (!wordDiscovery) return;

        const wordsToCreate = Math.floor(Math.random() * 3) + 1;

        for (let i = 0; i < wordsToCreate; i++) {
            const wordElement = document.createElement('div');
            wordElement.className = 'flying-word';
            wordElement.textContent = discoveryWords[wordIndex % discoveryWords.length];

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

            if (isMobile) {
                wordElement.style.fontSize = '1.1rem';
                wordElement.style.padding = '6px 12px';
            }

            wordDiscovery.appendChild(wordElement);
            wordIndex++;

            setTimeout(() => {
                if (wordElement.parentNode) {
                    wordElement.parentNode.removeChild(wordElement);
                }
            }, 5000);
        }
    }, 800);
}

/**
 * Извлекает интересные слова из текста
 * @param {string} text - Исходный текст
 * @returns {Array<string>} Массив интересных слов
 */
function extractInterestingWords(text) {
    if (!text) return [];

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

    const words = text.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(word =>
            word.length >= 6 &&
            word.length <= 16 &&
            !boringWords.has(word) &&
            /^[a-z]+$/.test(word)
        );

    const sortedWords = words.sort((a, b) => b.length - a.length);
    const uniqueWords = [...new Set(sortedWords)];

    return uniqueWords.slice(0, 15);
}

/**
 * Очищает все анимации
 */
function clearDiscoveryAnimations() {
    if (window.letterRainInterval) {
        clearInterval(window.letterRainInterval);
    }
    if (window.discoveryWordsInterval) {
        clearInterval(window.discoveryWordsInterval);
    }

    const sparklesBg = document.getElementById('sparklesBg');
    const lettersRain = document.getElementById('lettersRain');
    const wordDiscovery = document.getElementById('wordDiscovery');

    if (sparklesBg) sparklesBg.innerHTML = '';
    if (lettersRain) lettersRain.innerHTML = '';

    if (wordDiscovery) {
        const dynamicWords = wordDiscovery.querySelectorAll('.flying-word');
        dynamicWords.forEach(word => word.remove());
    }
}

// ========== АВТОИНИЦИАЛИЗАЦИЯ ==========
(function() {
    const styleTag = document.createElement('style');
    styleTag.innerHTML = getLoadingAnimationStyles();
    document.head.appendChild(styleTag);

    const loadingHTML = createLoadingAnimationHTML();

    if (document.body) {
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            document.body.insertAdjacentHTML('beforeend', loadingHTML);
        });
    }
})();

// ========== ЭКСПОРТ ==========
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createLoadingAnimationHTML,
        getLoadingAnimationStyles,
        showLoadingAnimation,
        hideLoadingAnimation
    };
}
