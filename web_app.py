#!/usr/bin/env python3
"""
Простой веб-интерфейс для демонстрации AI анализа лексики
"""

from flask import Flask, render_template, request, jsonify, session, redirect
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
    """API для анализа текста - использует новую архитектуру"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        # Используем новую архитектуру
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_service import get_analysis_service
        from core.yandex_ai_client import YandexAIClient

        # Создаем запрос
        analysis_request = AnalysisRequest(
            text=text,
            page_id='main',
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

        # Анализируем
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
                'error': 'Для AI анализа нужны токены Yandex GPT. Без них система не может генерировать качественные хайлайты.',
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
                'stats': result.stats,
                'highlights': highlights_dicts,
                'analysis_id': analysis_id
            })
        except Exception as db_error:
            print(f"Database error: {db_error}")

            return jsonify({
                'success': True,
                'stats': result.stats,
                'highlights': [h.to_dict() for h in result.highlights],
                'warning': 'Анализ выполнен, но не сохранен в историю'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
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

@app.route('/main')
def main_page():
    """Главная страница анализа (алиас для /)"""
    return render_template('index.html')

@app.route('/experimental')
def experimental_page():
    """🧪 Экспериментальная страница для dual-prompt анализа"""
    return render_template('experimental.html')

@app.route('/my-highlights')
def my_highlights_page():
    """📚 Страница с сохраненными хайлайтами"""
    return render_template('my-highlights.html')

@app.route('/experimental/analyze', methods=['POST'])
def experimental_analyze():
    """🧪 API для экспериментального dual-prompt анализа - использует новую архитектуру"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        # Используем новую архитектуру
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_service import get_analysis_service
        from core.yandex_ai_client import YandexAIClient

        # Создаем запрос для experimental (использует v2_dual - dual prompt)
        analysis_request = AnalysisRequest(
            text=text,
            page_id='experimental',
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

        # Анализируем
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

            # Разделяем на слова и фразы для dual-prompt интерфейса (по типу)
            words = [h for h in highlights_dicts if h.get('type') == 'word']
            phrases = [h for h in highlights_dicts if h.get('type') == 'expression']

            analysis_id = db.save_analysis(
                original_text=text,
                highlights=highlights_dicts,
                stats=result.stats,
                session_id=session['session_id'],
                ip_address=request.remote_addr
            )

            return jsonify({
                'success': True,
                'experimental': True,
                'stats': {
                    'total_words': result.stats.get('total_words', 0),
                    'total_highlights': len(highlights_dicts),
                    'total_word_highlights': len(words),
                    'total_phrase_highlights': len(phrases)
                },
                'words': words,
                'phrases': phrases,
                'performance': result.performance,
                'analysis_id': analysis_id
            })
        except Exception as db_error:
            print(f"Database error: {db_error}")

            highlights_dicts = [h.to_dict() for h in result.highlights]

            # Разделяем на слова и фразы для dual-prompt интерфейса (по типу)
            words = [h for h in highlights_dicts if h.get('type') == 'word']
            phrases = [h for h in highlights_dicts if h.get('type') == 'expression']

            return jsonify({
                'success': True,
                'experimental': True,
                'stats': {
                    'total_words': result.stats.get('total_words', 0),
                    'total_highlights': len(highlights_dicts),
                    'total_word_highlights': len(words),
                    'total_phrase_highlights': len(phrases)
                },
                'words': words,
                'phrases': phrases,
                'performance': result.performance,
                'warning': 'Анализ выполнен, но не сохранен в историю'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Критическая ошибка: {str(e)}'})


# ============================================================================
# 🚀 V3 ADAPTIVE PROMPT ROUTES
# ============================================================================

@app.route('/v3')
def v3_page():
    """🚀 V3 страница с adaptive prompt"""
    return render_template('v3.html')

@app.route('/v3/analyze', methods=['POST'])
def v3_analyze():
    """🚀 API для V3 adaptive prompt анализа"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        # Используем новую архитектуру
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_service import get_analysis_service
        from core.yandex_ai_client import YandexAIClient

        # Создаем запрос для v3
        analysis_request = AnalysisRequest(
            text=text,
            page_id='v3',
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

        # Анализируем
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
                'success': True,
                'highlights': [],
                'message': 'Не найдено интересных слов'
            })

        # Возвращаем результат
        return jsonify({
            'success': True,
            'highlights': [h.to_dict() for h in result.highlights],
            'stats': result.get_stats()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
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

# ===== YOUTUBE ROUTES =====

@app.route('/youtube/analyze', methods=['POST'])
def analyze_youtube():
    """
    Извлечение транскрипта из YouTube и редирект на /experimental
    """
    try:
        data = request.get_json()
        video_url = data.get('video_url', '').strip()

        if not video_url:
            return jsonify({
                'success': False,
                'error': 'URL видео не указан'
            })

        # Извлечение транскрипта через Agent 1
        from agents.youtube_agent import YouTubeTranscriptAgent
        agent = YouTubeTranscriptAgent()
        transcript_result = agent.extract_transcript(video_url)

        if not transcript_result['success']:
            return jsonify(transcript_result)

        # Возвращаем success с транскриптом для localStorage редиректа
        return jsonify({
            'success': True,
            'redirect': '/experimental',
            'transcript': transcript_result['transcript'],
            'video_title': transcript_result.get('video_title'),
            'video_url': video_url,
            'word_count': transcript_result['word_count']
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        })

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Wordoorio...")
    print("📱 Откройте http://localhost:8081 в браузере")
    app.run(debug=True, host='0.0.0.0', port=8081)