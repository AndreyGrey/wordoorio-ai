import os
import asyncio
import json
import sys
sys.path.append('.')

from yandex_ai_client import YandexAIClient
from agent_2_ai_powered import AIVocabularyAnalyzer

def handler(event, context):
    """Cloud Function для Wordoorio AI"""
    
    try:
        # GET запрос - возвращаем HTML интерфейс
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/html; charset=utf-8'},
                'body': get_html_interface()
            }
        
        # POST запрос - анализ текста
        body = json.loads(event.get('body', '{}'))
        text = body.get('text', '').strip()
        
        if not text:
            return error_response('Введите текст для анализа')
        
        if len(text.split()) < 5:
            return error_response('Текст слишком короткий (минимум 5 слов)')
        
        # Настройка переменных окружения для AI клиента
        try:
            if hasattr(context, 'token') and context.token and 'access_token' in context.token:
                os.environ['YANDEX_IAM_TOKEN'] = context.token['access_token']
            else:
                # Fallback - использовать IAM из переменных окружения
                os.environ['YANDEX_IAM_TOKEN'] = os.environ.get('YANDEX_IAM_TOKEN', '')
            os.environ['YANDEX_FOLDER_ID'] = os.environ.get('YANDEX_FOLDER_ID', '')
        except Exception as e:
            print(f"Ошибка настройки окружения: {e}")
            os.environ['YANDEX_IAM_TOKEN'] = ''
            os.environ['YANDEX_FOLDER_ID'] = os.environ.get('YANDEX_FOLDER_ID', '')
        
        # Используем настоящий AI анализ
        analyzer = AIVocabularyAnalyzer()
        result = analyzer.analyze_text(text)
        
        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json; charset=utf-8'},
                'body': json.dumps(result, ensure_ascii=False)
            }
        else:
            return error_response(result.get('error', 'Ошибка анализа'))
            
    except Exception as e:
        return error_response(f'Системная ошибка: {str(e)}')

def error_response(message):
    """Возврат ошибки"""
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'application/json; charset=utf-8'},
        'body': json.dumps({'error': message, 'success': False}, ensure_ascii=False)
    }

def get_html_interface():
    """HTML интерфейс"""
    return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Wordoorio AI</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #C8E3BF 0%, #A8D49A 20%, #B8DBA9 40%, #C8E3BF 70%, #D4EBC7 100%); 
            min-height: 100vh; 
            color: #2d3748;
        }
        
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 40px 20px; 
        }
        
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .logo {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
        }
        
        .header h1 { 
            color: #2d3748; 
            font-size: 2.5rem; 
            font-weight: 700; 
            margin-bottom: 10px; 
            text-shadow: 0 2px 4px rgba(255,255,255,0.3);
        }
        
        .header p { 
            color: #4a5568; 
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .input-section { 
            background: white; 
            padding: 40px; 
            border-radius: 16px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.15); 
            margin-bottom: 30px; 
        }
        
        textarea { 
            width: 100%; 
            height: 160px; 
            padding: 20px; 
            border: 2px solid #e2e8f0; 
            border-radius: 12px; 
            font-size: 16px; 
            font-family: inherit;
            resize: vertical; 
            transition: all 0.2s ease;
            line-height: 1.6;
        }
        
        textarea:focus { 
            outline: none; 
            border-color: #667eea; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button { 
            background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%); 
            color: white; 
            padding: 16px 32px; 
            border: none; 
            border-radius: 12px; 
            font-size: 16px; 
            font-weight: 600;
            cursor: pointer; 
            margin-top: 20px; 
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        }
        
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
        }
        
        .button:disabled { 
            background: #cbd5e0; 
            cursor: not-allowed; 
            transform: none;
            box-shadow: none;
        }
        
        .results { 
            background: white; 
            padding: 40px; 
            border-radius: 16px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.15); 
            display: none; 
        }
        
        .highlight-item { 
            background: #ffffff; 
            padding: 24px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border-left: 4px solid #4CAF50; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        
        .highlight-item:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            transform: translateY(-1px);
        }
        
        .highlight-word { 
            font-size: 1.25rem; 
            font-weight: 600; 
            color: #2d3748; 
            margin-bottom: 8px;
        }
        
        .highlight-translation {
            color: #4CAF50;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 12px;
        }
        
        .highlight-meaning {
            color: #4a5568;
            font-size: 0.95rem;
            margin-bottom: 12px;
            padding: 12px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 3px solid #4CAF50;
        }
        
        .highlight-context { 
            color: #718096; 
            font-style: italic; 
            font-size: 0.95rem;
            line-height: 1.6;
        }
        
        .highlighted-word {
            background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            font-style: normal;
        }
        
        .error { 
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%); 
            color: #c53030; 
            padding: 20px; 
            border-radius: 12px; 
            margin-top: 20px; 
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <svg class="logo" viewBox="0 0 694 700" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M46.8948 79.2285C58.0378 65.4675 70.7668 53.0715 84.8178 42.2965C111.08 22.1415 143.443 8.81249 175.948 3.08349C198.505 -0.891508 227.139 0.116486 250.525 0.108486L442.413 0.123485C464.872 0.0914851 489.768 -0.68651 511.862 2.19749C561.182 8.63349 614.947 39.0545 645.206 78.7255C693.905 139.994 692.901 182.274 693.036 256.165L693.04 459.32C693.041 476.08 693.748 493.705 692.012 510.136C682.139 603.533 610.965 677.987 519.386 696.13C492.594 701.438 469.52 699.547 442.382 699.491L349.562 699.462L249.155 699.568C229.574 699.564 204.676 700.404 185.815 698.12C130.951 691.477 79.9688 661.983 45.8698 618.796C25.1558 592.636 10.8089 562.018 3.96085 529.361C-1.38715 503.041 0.234853 476.024 0.219853 449.188L0.609853 334.896L0.602849 245.674C0.602849 228.878 -0.0831524 205.819 1.88285 189.618C6.50785 149.398 22.0768 111.215 46.8948 79.2285Z" fill="#1B7A94"/>
                <path d="M134.195 168.688C165.457 75.0275 288.156 68.6385 330.927 156.393C334.22 163.1 336.667 170.191 338.212 177.502C342.271 196.109 341.903 213.252 336.434 231.595C328.524 257.573 310.791 279.441 287.006 292.548C202.866 337.907 105.639 259.497 134.195 168.688Z" fill="#C8E3BF"/>
                <path d="M357.07 178.018C367.1 131.474 407.005 97.3765 454.544 94.7305C502.084 92.0845 545.526 121.543 560.66 166.687C574.836 208.976 560.948 255.613 525.947 283.257C490.945 310.901 442.359 313.606 404.506 290.017C366.652 266.428 347.674 221.619 357.07 178.018Z" fill="#C8E3BF"/>
                <path d="M368.875 422.083C391.161 420.242 402.238 434.678 407.262 454.49C408.225 449.181 409.218 446.078 411.62 441.128C417.418 426.012 443.436 416.678 457.051 425.88C486.269 445.625 477.375 487.069 443.918 495.95C421.604 497.597 411.935 484.052 407.144 464.15C403.777 479.205 396.936 491.477 380.971 496.089C373.23 498.325 365.122 496.628 358.271 492.553C349.59 487.364 343.342 478.926 340.915 469.113C335.901 448.451 347.674 427.042 368.875 422.083Z" fill="#F8F9F6"/>
            </svg>
            <h1>Wordoorio AI</h1>
            <p>AI-powered анализ выразительной английской лексики</p>
        </div>

        <div class="input-section">
            <h2>📝 Анализ текста</h2>
            <p style="color: #718096; margin-bottom: 15px;">Вставьте английский текст для получения лингвистических хайлайтов:</p>
            <textarea id="textInput" placeholder="Machine learning algorithms revolutionize artificial intelligence research..."></textarea>
            <button class="button" onclick="analyzeText()">🔍 Анализировать</button>
            <div id="error" class="error" style="display: none;"></div>
        </div>

        <div id="results" class="results">
            <h2>📊 Результаты анализа</h2>
            <div id="highlightsList"></div>
        </div>
    </div>

    <script>
        async function analyzeText() {
            const textInput = document.getElementById('textInput');
            const text = textInput.value.trim();
            const button = document.querySelector('.button');
            const errorDiv = document.getElementById('error');
            const resultsDiv = document.getElementById('results');

            if (!text) {
                showError('Пожалуйста, введите текст для анализа');
                return;
            }

            button.disabled = true;
            button.textContent = '🔄 Анализирую...';
            errorDiv.style.display = 'none';
            resultsDiv.style.display = 'none';

            try {
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ text: text })
                });

                const data = await response.json();

                if (data.success) {
                    showResults(data);
                } else {
                    showError(data.error || 'Неизвестная ошибка');
                }
            } catch (error) {
                showError('Ошибка соединения с сервером');
            } finally {
                button.disabled = false;
                button.textContent = '🔍 Анализировать';
            }
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function showResults(data) {
            const highlightsList = document.getElementById('highlightsList');
            highlightsList.innerHTML = `<p style="color:#718096;margin-bottom:24px">Найдено ${data.stats.total_highlights} хайлайтов из ${data.stats.total_words} слов</p>`;

            data.highlights.forEach((highlight, index) => {
                const item = document.createElement('div');
                item.className = 'highlight-item';
                
                // Проверяем, есть ли валидные определения
                const hasValidMeanings = highlight.dictionary_meanings && 
                    highlight.dictionary_meanings.length > 0;
                
                const meaningsHtml = hasValidMeanings 
                    ? `<div class="highlight-meaning">
                         <strong>Другие значения:</strong> ${highlight.dictionary_meanings.join('; ')}
                       </div>`
                    : '';
                
                // Подсвечиваем хайлайт в контексте
                let contextWithHighlight = highlight.context;
                try {
                    const regex = new RegExp(`\\\\b${highlight.highlight.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}\\\\b`, 'gi');
                    if (regex.test(contextWithHighlight)) {
                        contextWithHighlight = contextWithHighlight.replace(regex, 
                            `<span class="highlighted-word">${highlight.highlight}</span>`);
                    }
                } catch(e) {
                    // Если regex не работает, оставляем как есть
                }
                
                item.innerHTML = `
                    <div class="highlight-word">
                        ${index + 1}. ${highlight.highlight}
                    </div>
                    <div class="highlight-translation">${highlight.context_translation}</div>
                    ${meaningsHtml}
                    <div class="highlight-context">"${contextWithHighlight}"</div>
                `;
                highlightsList.appendChild(item);
            });

            document.getElementById('results').style.display = 'block';
        }

        // Анализ по Ctrl+Enter
        document.getElementById('textInput').addEventListener('keypress', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                analyzeText();
            }
        });
    </script>
</body>
</html>'''