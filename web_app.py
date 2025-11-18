#!/usr/bin/env python3
"""
Простой веб-интерфейс для демонстрации AI анализа лексики
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к агентам
sys.path.append('.')

app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """API для анализа текста"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'Текст не может быть пустым'})
        
        if len(text.split()) < 5:
            return jsonify({'error': 'Текст слишком короткий (минимум 5 слов)'})
        
        # Используем AI Agent 2
        from agents.agent_2_ai_powered import AIVocabularyAnalyzer
        analyzer = AIVocabularyAnalyzer()
        result = analyzer.analyze_text(text)
        
        if result['success']:
            if not result['highlights']:
                return jsonify({
                    'error': 'Для AI анализа нужны токены Yandex GPT. Без них система не может генерировать качественные хайлайты.',
                    'need_tokens': True
                })
            
            
            return jsonify({
                'success': True,
                'stats': result['stats'],
                'highlights': result['highlights']  # Все хайлайты
            })
        else:
            return jsonify({'error': f"Ошибка анализа: {result.get('error', 'Неизвестная ошибка')}"})
            
    except Exception as e:
        return jsonify({'error': f'Критическая ошибка: {str(e)}'})

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Wordoorio...")
    print("📱 Откройте http://localhost:8081 в браузере")
    app.run(debug=True, host='0.0.0.0', port=8081)