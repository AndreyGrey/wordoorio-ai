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
        os.environ['YANDEX_IAM_TOKEN'] = context.token['access_token']
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
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
        }
        
        .header h1 { 
            color: white; 
            font-size: 2.5rem; 
            font-weight: 700; 
            margin-bottom: 10px; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header p { 
            color: rgba(255,255,255,0.9); 
            font-size: 1.1rem; 
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 16px 32px; 
            border: none; 
            border-radius: 12px; 
            font-size: 16px; 
            font-weight: 600;
            cursor: pointer; 
            margin-top: 20px; 
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
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
            border-left: 4px solid #667eea; 
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
            color: #667eea;
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
            border-left: 3px solid #667eea;
        }
        
        .highlight-context { 
            color: #718096; 
            font-style: italic; 
            font-size: 0.95rem;
            line-height: 1.6;
        }
        
        .highlighted-word {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            <h1>🧠 Wordoorio AI</h1>
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