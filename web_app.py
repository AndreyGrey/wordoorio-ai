#!/usr/bin/env python3
"""
Простой веб-интерфейс для демонстрации AI анализа лексики
"""

from flask import Flask, render_template, request, jsonify, session
import json
import sys
import os
from dotenv import load_dotenv
from database import WordoorioDatabase
import uuid

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к агентам
sys.path.append('.')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'wordoorio-secret-key-12345')

# Инициализируем базу данных
db = WordoorioDatabase()

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
        from agents.agent_2 import AIVocabularyAnalyzer
        analyzer = AIVocabularyAnalyzer()
        result = analyzer.analyze_text(text)
        
        if result['success']:
            if not result['highlights']:
                return jsonify({
                    'error': 'Для AI анализа нужны токены Yandex GPT. Без них система не может генерировать качественные хайлайты.',
                    'need_tokens': True
                })
            
            # Генерируем session_id если его нет
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            # Сохраняем анализ в базу данных
            try:
                analysis_id = db.save_analysis(
                    original_text=text,
                    highlights=result['highlights'],
                    stats=result['stats'],
                    session_id=session['session_id'],
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    'success': True,
                    'stats': result['stats'],
                    'highlights': result['highlights'],
                    'analysis_id': analysis_id
                })
            except Exception as db_error:
                # Если БД не работает, возвращаем результат без сохранения
                print(f"Database error: {db_error}")
                
                return jsonify({
                    'success': True,
                    'stats': result['stats'],
                    'highlights': result['highlights'],
                    'warning': 'Анализ выполнен, но не сохранен в историю'
                })
        else:
            return jsonify({'error': f"Ошибка анализа: {result.get('error', 'Неизвестная ошибка')}"})
            
    except Exception as e:
        return jsonify({'error': f'Критическая ошибка: {str(e)}'})

@app.route('/api/history', methods=['GET'])
def get_history():
    """API для получения истории анализов"""
    try:
        limit = request.args.get('limit', 10, type=int)
        analyses = db.get_recent_analyses(limit)
        return jsonify({
            'success': True,
            'analyses': analyses
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка получения истории: {str(e)}'})

@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """API для получения конкретного анализа"""
    try:
        analysis = db.get_analysis_by_id(analysis_id)
        if analysis:
            return jsonify({
                'success': True,
                'analysis': analysis
            })
        else:
            return jsonify({'error': 'Анализ не найден'}, 404)
    except Exception as e:
        return jsonify({'error': f'Ошибка получения анализа: {str(e)}'})

@app.route('/api/search', methods=['GET'])
def search_word():
    """API для поиска по словам"""
    try:
        word = request.args.get('word', '').strip()
        if not word:
            return jsonify({'error': 'Поисковый запрос не может быть пустым'})
        
        results = db.search_by_word(word)
        return jsonify({
            'success': True,
            'word': word,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка поиска: {str(e)}'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API для получения статистики"""
    try:
        stats = db.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': f'Ошибка получения статистики: {str(e)}'})

@app.route('/experimental')
def experimental_page():
    """🧪 Экспериментальная страница для dual-prompt анализа"""
    return render_template('experimental.html')

@app.route('/experimental/analyze', methods=['POST'])
def experimental_analyze():
    """🧪 API для экспериментального dual-prompt анализа"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'Текст не может быть пустым'})
        
        if len(text.split()) < 5:
            return jsonify({'error': 'Текст слишком короткий (минимум 5 слов)'})
        
        # Используем экспериментальный клиент
        import asyncio
        from core.experimental_ai_client import ExperimentalYandexAIClient
        
        client = ExperimentalYandexAIClient()
        
        # Асинхронный вызов
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(client.analyze_dual_highlights(text))
        
        if not result['words'] and not result['phrases']:
            return jsonify({
                'error': 'Для AI анализа нужны токены Yandex GPT.',
                'need_tokens': True
            })
        
        # Генерируем session_id если его нет
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # Объединяем и преобразуем в словари для совместимости с БД
        all_highlights = []
        for highlight in result['words'] + result['phrases']:
            if hasattr(highlight, 'to_dict'):
                all_highlights.append(highlight.to_dict())
            elif isinstance(highlight, dict):
                all_highlights.append(highlight)
            else:
                # Если это dataclass объект без to_dict
                from dataclasses import asdict
                all_highlights.append(asdict(highlight))
        
        # Сохраняем в БД (опционально)
        try:
            analysis_id = db.save_analysis(
                original_text=text,
                highlights=all_highlights,
                stats={
                    'total_words': len(text.split()),
                    'total_highlights': len(all_highlights)
                },
                session_id=session['session_id'],
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'experimental': True,
                'stats': {
                    'total_words': len(text.split()),
                    'total_word_highlights': len(result['words']),
                    'total_phrase_highlights': len(result['phrases']),
                    'total_highlights': len(all_highlights)
                },
                'words': [h.to_dict() for h in result['words']],
                'phrases': [h.to_dict() for h in result['phrases']],
                'analysis_id': analysis_id
            })
        except Exception as db_error:
            print(f"Database error: {db_error}")
            
            return jsonify({
                'success': True,
                'experimental': True,
                'stats': {
                    'total_words': len(text.split()),
                    'total_word_highlights': len(result['words']),
                    'total_phrase_highlights': len(result['phrases']),
                    'total_highlights': len(all_highlights)
                },
                'words': [h.to_dict() for h in result['words']],
                'phrases': [h.to_dict() for h in result['phrases']],
                'warning': 'Анализ выполнен, но не сохранен в историю'
            })
            
    except Exception as e:
        return jsonify({'error': f'Критическая ошибка: {str(e)}'})

@app.route('/api/v2/analyze', methods=['POST'])
def analyze_v2():
    """🚀 API V2 - использует новую архитектуру с версионированием промптов"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        page_id = data.get('page_id', 'main')  # "main" или "experimental"

        # Импортируем новую архитектуру
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_service import get_analysis_service
        from core.yandex_ai_client import YandexAIClient

        # Создаем запрос
        analysis_request = AnalysisRequest(
            text=text,
            page_id=page_id,
            user_session=session.get('session_id')
        )

        # Валидация
        error = analysis_request.validate()
        if error:
            return jsonify({'error': error})

        # Генерируем session_id если его нет
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        # Получаем сервис и клиент
        service = get_analysis_service()
        ai_client = YandexAIClient()

        # Анализируем (сервис сам выберет промпт и применит дедупликацию)
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            service.analyze_text(analysis_request, ai_client)
        )

        # Проверяем успех
        if not result.success:
            return jsonify({'error': result.error})

        if not result.highlights:
            return jsonify({
                'error': 'Для AI анализа нужны токены Yandex GPT.',
                'need_tokens': True
            })

        # Сохраняем в БД
        try:
            highlights_dicts = [h.to_dict() for h in result.highlights]

            analysis_id = db.save_analysis(
                original_text=text,
                highlights=highlights_dicts,
                stats=result.stats,
                session_id=session['session_id'],
                ip_address=request.remote_addr
            )

            return jsonify({
                'success': True,
                'api_version': 'v2',
                'page_id': page_id,
                'stats': result.stats,
                'highlights': highlights_dicts,
                'performance': result.performance,
                'analysis_id': analysis_id
            })
        except Exception as db_error:
            print(f"Database error: {db_error}")

            return jsonify({
                'success': True,
                'api_version': 'v2',
                'page_id': page_id,
                'stats': result.stats,
                'highlights': [h.to_dict() for h in result.highlights],
                'performance': result.performance,
                'warning': 'Анализ выполнен, но не сохранен в историю'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Критическая ошибка V2: {str(e)}'})

@app.route('/history')
def history_page():
    """Страница истории анализов"""
    return render_template('history.html')

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Wordoorio...")
    print("📱 Откройте http://localhost:8081 в браузере")
    app.run(debug=True, host='0.0.0.0', port=8081)