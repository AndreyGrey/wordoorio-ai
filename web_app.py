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

        # Используем новую архитектуру с AnalysisOrchestrator
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_orchestrator import AnalysisOrchestrator
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

        # Создаем клиент и оркестратор
        ai_client = YandexAIClient()
        orchestrator = AnalysisOrchestrator(ai_client)

        # Анализируем
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            orchestrator.analyze_text(analysis_request)
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

@app.route('/my-highlights')
def my_highlights_page():
    """📚 Страница с сохраненными хайлайтами"""
    return render_template('my-highlights.html')

@app.route('/api/v2/analyze', methods=['POST'])
def analyze_v2():
    """🚀 API V2 - использует новую архитектуру с версионированием промптов"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        page_id = data.get('page_id', 'main')  # "main" или "experimental"

        # Импортируем новую архитектуру с AnalysisOrchestrator
        import asyncio
        from contracts.analysis_contracts import AnalysisRequest
        from core.analysis_orchestrator import AnalysisOrchestrator
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

        # Создаем клиент и оркестратор
        ai_client = YandexAIClient()
        orchestrator = AnalysisOrchestrator(ai_client)

        # Анализируем через оркестратор
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            orchestrator.analyze_text(analysis_request)
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

# ===== YOUTUBE ENDPOINT (DEPRECATED - будет удален) =====
# @app.route('/youtube/analyze', methods=['POST'])
# def analyze_youtube():
#     """
#     Извлечение транскрипта из YouTube и редирект на /experimental
#     DEPRECATED: YouTube функциональность удалена в Agent Refactoring v2.0
#     """
#     return jsonify({
#         'success': False,
#         'error': 'YouTube функциональность временно недоступна'
#     })

# ===== DICTIONARY ROUTES =====

@app.route('/api/dictionary/add', methods=['POST'])
def api_dictionary_add():
    """
    API для добавления слова в словарь

    Принимает:
    {
        "highlight": "give up",  # Уже лемматизировано!
        "type": "expression",
        "highlight_translation": "сдаться",
        "context": "Never give up...",
        "dictionary_meanings": ["бросить"]
    }
    """
    try:
        from core.dictionary_manager import DictionaryManager

        data = request.get_json()

        # Валидация
        required_fields = ['highlight', 'type', 'highlight_translation', 'context']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует поле: {field}'
                }), 400

        # Получаем session_id и user_id
        session_id = session.get('session_id', 'unknown')
        user_id = session.get('user_id')  # None если не авторизован

        # Если пользователь не авторизован, не сохраняем в базу
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authorization required. Please login with Telegram to save words.',
                'require_auth': True
            }), 401

        # Добавляем в словарь
        dict_manager = DictionaryManager()
        result = dict_manager.add_word(
            highlight_dict=data,
            session_id=session_id,
            user_id=user_id
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка добавления в словарь: {str(e)}'
        }), 500


@app.route('/api/dictionary/words', methods=['GET'])
def api_dictionary_words():
    """
    API для получения всех слов из словаря

    Query параметры:
    - type: "word" или "expression" (опционально)
    - status: "new", "learning", "learned" (опционально)
    """
    try:
        from core.dictionary_manager import DictionaryManager

        # Получаем фильтры из query parameters
        filters = {}

        word_type = request.args.get('type')
        if word_type:
            filters['type'] = word_type

        status = request.args.get('status')
        if status:
            filters['status'] = status

        # Получаем user_id
        user_id = session.get('user_id')

        # Если пользователь не авторизован, возвращаем пустой список
        if not user_id:
            return jsonify({
                'success': True,
                'words': [],
                'count': 0
            })

        # Получаем слова
        dict_manager = DictionaryManager()
        words = dict_manager.get_all_words(
            user_id=user_id,
            filters=filters if filters else None
        )

        return jsonify({
            'success': True,
            'words': words,
            'count': len(words)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка получения слов: {str(e)}'
        }), 500


@app.route('/api/dictionary/word/<lemma>', methods=['GET'])
def api_dictionary_word(lemma):
    """
    API для получения детальной информации о слове

    Возвращает:
    - Все переводы
    - Все примеры использования
    - Статус изучения
    """
    try:
        from core.dictionary_manager import DictionaryManager

        # Получаем user_id
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authorization required'
            }), 401

        dict_manager = DictionaryManager()
        word = dict_manager.get_word(
            lemma=lemma,
            user_id=user_id
        )

        if not word:
            return jsonify({
                'success': False,
                'error': 'Слово не найдено'
            }), 404

        return jsonify({
            'success': True,
            'word': word
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка получения слова: {str(e)}'
        }), 500


@app.route('/api/dictionary/word/<lemma>', methods=['DELETE'])
def api_dictionary_delete(lemma):
    """
    API для удаления слова из словаря
    """
    try:
        from core.dictionary_manager import DictionaryManager

        # Получаем user_id
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authorization required'
            }), 401

        dict_manager = DictionaryManager()
        result = dict_manager.delete_word(
            lemma=lemma,
            user_id=user_id
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка удаления слова: {str(e)}'
        }), 500


@app.route('/api/dictionary/stats', methods=['GET'])
def api_dictionary_stats():
    """
    API для получения статистики словаря

    Возвращает:
    - total_words: количество слов
    - total_phrases: количество фраз
    - total_count: всего записей
    - status_breakdown: разбивка по статусам
    """
    try:
        from core.dictionary_manager import DictionaryManager

        # Получаем user_id
        user_id = session.get('user_id')

        # Если пользователь не авторизован, возвращаем пустую статистику
        if not user_id:
            return jsonify({
                'success': True,
                'stats': {
                    'total_count': 0,
                    'total_words': 0,
                    'total_phrases': 0,
                    'status_breakdown': {'new': 0, 'learning': 0, 'learned': 0}
                }
            })

        dict_manager = DictionaryManager()
        stats = dict_manager.get_stats(user_id=user_id)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка получения статистики: {str(e)}'
        }), 500


# ===== AUTH API =====

@app.route('/api/auth/telegram', methods=['POST'])
def auth_telegram():
    """
    🔐 Обработка авторизации через Telegram Login Widget

    Принимает данные от Telegram, проверяет подпись и создает сессию
    """
    try:
        from core.auth_manager import AuthManager

        data = request.get_json()

        # Создаем AuthManager
        auth = AuthManager()

        # Проверяем подпись Telegram
        if not auth.verify_telegram_auth(data):
            return jsonify({
                'success': False,
                'error': 'Invalid Telegram signature'
            }), 403

        # Создаем или обновляем пользователя
        user_id = auth.create_or_update_user(data)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Failed to create user'
            }), 500

        # Сохраняем user_id в сессии
        session['user_id'] = user_id
        session['telegram_id'] = data.get('id')

        # Получаем данные пользователя
        user = auth.get_user_by_id(user_id)

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'telegram_id': user['telegram_id'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username'],
                'photo_url': user['photo_url']
            }
        })

    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка авторизации: {str(e)}'
        }), 500


@app.route('/api/auth/current', methods=['GET'])
def get_current_user():
    """
    👤 Получить текущего авторизованного пользователя
    """
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': True,
                'user': None
            })

        from core.auth_manager import AuthManager
        auth = AuthManager()
        user = auth.get_user_by_id(user_id)

        if not user:
            # Пользователь удален из базы, чистим сессию
            session.pop('user_id', None)
            session.pop('telegram_id', None)
            return jsonify({
                'success': True,
                'user': None
            })

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'telegram_id': user['telegram_id'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username'],
                'photo_url': user['photo_url']
            }
        })

    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка: {str(e)}'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    🚪 Выход из системы
    """
    session.pop('user_id', None)
    session.pop('telegram_id', None)
    return jsonify({'success': True})


@app.route('/api/auth/config', methods=['GET'])
def auth_config():
    """
    ⚙️ Получить конфигурацию авторизации (bot_username)
    """
    bot_username = os.getenv('TELEGRAM_BOT_USERNAME', '')
    return jsonify({
        'success': True,
        'bot_username': bot_username
    })


@app.route('/dictionary')
def dictionary_page():
    """📚 Страница личного словаря"""
    return render_template('dictionary.html')


@app.route('/training')
def training_page():
    """🎯 Страница тренировки слов"""
    return render_template('training.html')


@app.route('/api/training/start', methods=['POST'])
def api_training_start():
    """Начать новую тренировку - отобрать 8 слов и создать тесты"""
    try:
        from core.auth_manager import AuthManager
        from core.training_service import TrainingService
        from core.test_manager import TestManager
        from core.yandex_ai_client import YandexAIClient
        import asyncio

        # Проверяем авторизацию
        auth_manager = AuthManager(db.db_path)
        user_data = auth_manager.verify_session(session)

        if not user_data:
            return jsonify({'error': 'Требуется авторизация'}), 401

        user_id = user_data['id']

        # Отбираем слова для тренировки
        training_service = TrainingService(db)
        words = training_service.select_words_for_training(user_id, count=8)

        if not words:
            return jsonify({'error': 'В вашем словаре недостаточно слов для тренировки'}), 400

        # Создаем тесты
        ai_client = YandexAIClient()
        test_manager = TestManager(db, ai_client)

        # Используем asyncio для создания тестов
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        test_ids = loop.run_until_complete(
            test_manager.create_tests_batch(user_id, words)
        )

        if not test_ids:
            return jsonify({'error': 'Не удалось создать тесты'}), 500

        # Получаем тесты с перемешанными вариантами
        tests = []
        for test_id in test_ids:
            test = test_manager.get_test_with_shuffled_options(test_id)
            if test:
                tests.append(test)

        return jsonify({
            'success': True,
            'tests': tests,
            'total': len(tests)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка создания тренировки: {str(e)}'}), 500


@app.route('/api/training/answer', methods=['POST'])
def api_training_answer():
    """Отправить ответ на тест"""
    try:
        from core.auth_manager import AuthManager
        from core.test_manager import TestManager
        from core.yandex_ai_client import YandexAIClient

        # Проверяем авторизацию
        auth_manager = AuthManager(db.db_path)
        user_data = auth_manager.verify_session(session)

        if not user_data:
            return jsonify({'error': 'Требуется авторизация'}), 401

        data = request.get_json()
        test_id = data.get('test_id')
        answer = data.get('answer')

        if not test_id or not answer:
            return jsonify({'error': 'Неверные параметры'}), 400

        # Проверяем ответ
        ai_client = YandexAIClient()
        test_manager = TestManager(db, ai_client)

        result = test_manager.submit_answer(test_id, answer)

        return jsonify({
            'success': True,
            'is_correct': result['is_correct'],
            'correct_translation': result['correct_translation'],
            'word': result['word'],
            'new_rating': result['new_rating'],
            'new_status': result['new_status']
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка проверки ответа: {str(e)}'}), 500


if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Wordoorio...")
    print("📱 Откройте http://localhost:8081 в браузере")
    app.run(debug=True, host='0.0.0.0', port=8081)