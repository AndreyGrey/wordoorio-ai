#!/usr/bin/env python3
"""
Простой веб-интерфейс для демонстрации AI анализа лексики
"""

from flask import Flask, render_template, request, jsonify, session, redirect
import json
import sys
import os
import logging
import time
from dotenv import load_dotenv
from database import WordoorioDatabase
import uuid

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Устанавливаем уровень INFO для всех логгеров (включая core.yandex_ai_client)
logging.getLogger('core.yandex_ai_client').setLevel(logging.INFO)
logging.getLogger('core.test_manager').setLevel(logging.INFO)
logging.getLogger('core.training_service').setLevel(logging.INFO)

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

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """API для анализа текста через Yandex AI агентов"""
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

        # НЕ сохраняем в БД при анализе!
        # Данные сохраняются ТОЛЬКО при клике "+" в /api/dictionary/add
        highlights_dicts = [h.to_dict() for h in result.highlights]

        return jsonify({
            'success': True,
            'api_version': 'v2',
            'page_id': page_id,
            'stats': result.stats,
            'highlights': highlights_dicts,
            'performance': result.performance
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Критическая ошибка V2: {str(e)}'})

@app.route('/history')
def history_page():
    """Страница истории анализов"""
    return render_template('history.html')

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
        required_fields = ['highlight', 'highlight_translation', 'context']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует поле: {field}'
                }), 400

        # Автоопределение type если не передан
        if 'type' not in data:
            word_count = len(data['highlight'].split())
            data['type'] = 'word' if word_count == 1 else 'expression'

        # Получаем session_id и user_id
        session_id = session.get('session_id', 'unknown')
        user_id = session.get('user_id')  # None если не авторизован

        logger.info(f"[/api/dictionary/add] session_id={session_id}, user_id={user_id}, word={data.get('highlight')}")

        # Если пользователь не авторизован, не сохраняем в базу
        if not user_id:
            logger.warning(f"[/api/dictionary/add] Попытка добавить слово без авторизации: {data.get('highlight')}")
            return jsonify({
                'success': False,
                'error': 'Authorization required. Please login with Telegram to save words.',
                'require_auth': True
            }), 401

        # 1. Добавляем в словарь
        dict_manager = DictionaryManager()
        result = dict_manager.add_word(
            highlight_dict=data,
            session_id=session_id,
            user_id=user_id
        )

        logger.info(f"[/api/dictionary/add] Словарь: success={result.get('success')}, word_id={result.get('word_id')}")

        # 2. Также сохраняем в analyses + highlights (для истории)
        try:
            # Получаем word_id из результата добавления в словарь
            word_id = result.get('word_id')
            if not word_id:
                raise ValueError("word_id not returned from dict_manager.add_word()")

            # Получаем page_id (уникальный ID анализа текста) из данных
            page_id = data.get('page_id')
            logger.info(f"[/api/dictionary/add] page_id из запроса: {page_id}, user_id: {user_id}")

            # Ищем или создаем analysis для конкретного page_id
            analysis = None
            if page_id:
                # Ищем analysis по page_id (session_id совпадает с page_id для конкретного анализа)
                analysis = db.get_analysis_by_session(page_id, user_id)
                logger.info(f"[/api/dictionary/add] Результат поиска analysis: {analysis}")

            if not analysis:
                # Создаем новый analysis (БЕЗ highlights)
                analysis_session_id = page_id if page_id else session_id
                logger.info(f"[/api/dictionary/add] Создаем новый analysis с session_id={analysis_session_id}")
                analysis_id = db.save_analysis(
                    original_text=data.get('context', 'Manually added words'),
                    analysis_result={
                        'highlights': [],  # Пустой массив - highlights добавим отдельно
                        'total_words': 0
                    },
                    user_id=user_id,
                    session_id=analysis_session_id,  # Используем page_id как session_id для группировки
                    ip_address=request.remote_addr
                )
                logger.info(f"[/api/dictionary/add] Создан новый analysis #{analysis_id} (page_id={page_id}, session_id={analysis_session_id})")
            else:
                analysis_id = analysis['id']
                logger.info(f"[/api/dictionary/add] Найден существующий analysis #{analysis_id} (session_id={analysis.get('session_id')})")

            # Добавляем highlight (с word_id) к analysis
            db.add_highlight_to_analysis(analysis_id, word_id, user_id, session_id)
            logger.info(f"[/api/dictionary/add] Добавлен highlight word_id={word_id} к analysis #{analysis_id}")

            result['analysis_id'] = analysis_id
        except Exception as analysis_error:
            logger.warning(f"[/api/dictionary/add] Не удалось сохранить в analyses: {analysis_error}")
            # Не прерываем выполнение - слово в словаре уже сохранено

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Ошибка добавления в словарь: {str(e)}'
        }), 500


@app.route('/api/test/add-word', methods=['GET'])
def api_test_add_word():
    """
    ТЕСТОВЫЙ endpoint для проверки добавления слова в YDB
    Добавляет фиксированное тестовое слово

    Использование: просто откройте /api/test/add-word в браузере
    """
    try:
        from core.dictionary_manager import DictionaryManager

        # Фиксированные тестовые данные
        test_data = {
            'highlight': 'test',
            'type': 'word',
            'highlight_translation': 'тест',
            'context': 'This is a test sentence.',
            'dictionary_meanings': ['проверка', 'испытание']
        }

        logger.info(f"[TEST] Попытка добавить тестовое слово: {test_data}")

        # user_id=1 для теста
        dict_manager = DictionaryManager()
        result = dict_manager.add_word(
            highlight_dict=test_data,
            session_id='test_session_' + str(int(time.time())),
            user_id=1
        )

        logger.info(f"[TEST] Результат: {result}")

        return jsonify({
            'test_endpoint': True,
            'test_data': test_data,
            'result': result,
            'timestamp': time.time()
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[TEST] Ошибка: {error_trace}")
        return jsonify({
            'test_endpoint': True,
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }), 500


@app.route('/api/test/check-table', methods=['GET'])
def api_test_check_table():
    """
    ТЕСТОВЫЙ endpoint для проверки существования таблицы dictionary_words
    """
    try:
        from core.dictionary_manager import DictionaryManager

        dict_manager = DictionaryManager()

        # Простой запрос для проверки таблицы
        def check_table(session):
            query = "SELECT COUNT(*) as count FROM dictionary_words"
            return session.transaction().execute(query, commit_tx=True)

        result = dict_manager.pool.retry_operation_sync(check_table)

        # Получаем количество записей
        count = result[0].rows[0].count if result and result[0].rows else 0

        return jsonify({
            'test_endpoint': True,
            'table_exists': True,
            'records_count': count,
            'message': f'Таблица dictionary_words существует. Записей: {count}'
        })

    except Exception as e:
        error_msg = str(e)
        table_exists = 'does not exist' not in error_msg.lower()

        return jsonify({
            'test_endpoint': True,
            'table_exists': table_exists,
            'error': error_msg,
            'message': 'Таблица НЕ существует!' if not table_exists else 'Другая ошибка'
        }), 500 if not table_exists else 200


@app.route('/api/test/describe-table', methods=['GET'])
def api_test_describe_table():
    """
    ТЕСТОВЫЙ endpoint для получения схемы таблицы dictionary_words
    """
    try:
        from core.dictionary_manager import DictionaryManager

        dict_manager = DictionaryManager()

        # Получаем описание таблицы через table_client
        table_path = dict_manager.database + '/dictionary_words'

        def describe_table(session):
            return session.describe_table(table_path)

        description = dict_manager.driver.table_client.session().create().describe_table(table_path)

        # Формируем схему
        columns = []
        for column in description.columns:
            type_str = str(column.type)
            columns.append({
                'name': column.name,
                'type': type_str,
                'is_optional': 'Optional[' in type_str
            })

        primary_keys = list(description.primary_key)

        indexes = []
        for index in description.indexes:
            indexes.append({
                'name': index.name,
                'columns': list(index.index_columns)
            })

        return jsonify({
            'test_endpoint': True,
            'success': True,
            'table': 'dictionary_words',
            'columns': columns,
            'primary_key': primary_keys,
            'indexes': indexes
        })

    except Exception as e:
        import traceback
        return jsonify({
            'test_endpoint': True,
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
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


# ===== HIGHLIGHTS API =====

@app.route('/api/highlights', methods=['GET'])
def get_user_highlights_api():
    """
    Получить все хайлайты пользователя из базы данных
    """
    try:
        # Получаем user_id
        user_id = session.get('user_id')

        # Если пользователь не авторизован, возвращаем пустой список
        if not user_id:
            return jsonify({
                'success': True,
                'analyses': [],
                'message': 'Войдите для доступа к истории'
            })

        # Получаем хайлайты из БД
        analyses = db.get_user_highlights(user_id=user_id, limit=100)

        return jsonify({
            'success': True,
            'analyses': analyses
        })

    except Exception as e:
        logger.error(f"[/api/highlights] Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Ошибка получения хайлайтов: {str(e)}'
        }), 500


@app.route('/api/analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """
    Удалить анализ (сет хайлайтов) по ID
    """
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Требуется авторизация'
            }), 401

        # Удаляем анализ
        success = db.delete_analysis(analysis_id, user_id)

        if success:
            logger.info(f"[DELETE] Удален анализ {analysis_id} пользователя {user_id}")
            return jsonify({
                'success': True,
                'message': 'Анализ удален'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Анализ не найден или доступ запрещен'
            }), 404

    except Exception as e:
        logger.error(f"[DELETE] Ошибка удаления анализа {analysis_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Ошибка удаления: {str(e)}'
        }), 500


# ===== AUTH API =====

@app.route('/api/auth/current', methods=['GET'])
def get_current_user():
    """
    Получить текущего авторизованного пользователя
    """
    try:
        user_id = session.get('user_id')
        username = session.get('username')

        if not user_id:
            return jsonify({
                'success': True,
                'user': None
            })

        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': username
            }
        })

    except Exception as e:
        print(f"Ошибка получения пользователя: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка: {str(e)}'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    Выход из системы
    """
    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """
    Простая авторизация по логину-паролю для тестирования
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        # Тестовые аккаунты (TODO: позже заменить на нормальную БД)
        TEST_ACCOUNTS = {
            'andrew': {'password': 'test123', 'user_id': 1},
            'friend1': {'password': 'test123', 'user_id': 2},
            'friend2': {'password': 'test123', 'user_id': 3},
        }

        if username not in TEST_ACCOUNTS:
            return jsonify({
                'success': False,
                'error': 'Неверный логин или пароль'
            }), 401

        account = TEST_ACCOUNTS[username]

        if account['password'] != password:
            return jsonify({
                'success': False,
                'error': 'Неверный логин или пароль'
            }), 401

        # Сохраняем в сессии
        session['user_id'] = account['user_id']
        session['username'] = username

        return jsonify({
            'success': True,
            'user': {
                'id': account['user_id'],
                'username': username
            }
        })

    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ошибка сервера'
        }), 500


@app.route('/login')
def login_page():
    """Страница входа"""
    return render_template('login.html')


@app.route('/api/migrate-highlights', methods=['POST'])
def migrate_highlights():
    """
    Миграция localStorage хайлайтов на сервер
    Вызывается после успешного логина
    """
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Требуется авторизация'
            }), 401

        data = request.get_json()
        original_text = data.get('original_text', 'Migrated from localStorage')
        highlights = data.get('highlights', [])
        old_session_id = data.get('session_id')

        if not highlights:
            return jsonify({
                'success': True,
                'message': 'Нет хайлайтов для миграции'
            })

        # Сохраняем в БД
        analysis_id = db.save_analysis(
            original_text=original_text,
            analysis_result={
                'highlights': highlights,
                'total_words': 0
            },
            user_id=user_id,
            session_id=old_session_id or session.get('session_id'),
            ip_address=request.remote_addr
        )

        logger.info(f"[MIGRATION] Мигрировано {len(highlights)} хайлайтов для user_id={user_id}, analysis_id={analysis_id}")

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'highlights_count': len(highlights)
        })

    except Exception as e:
        logger.error(f"[MIGRATION] Ошибка: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== TELEGRAM WEBHOOK =====

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Тестовые аккаунты (синхронизированы с login API)
TELEGRAM_TEST_ACCOUNTS = {
    'andrew': {'password': 'test123', 'user_id': 1},
    'friend1': {'password': 'test123', 'user_id': 2},
    'friend2': {'password': 'test123', 'user_id': 3},
}


def telegram_send_message(chat_id: int, text: str, reply_markup: dict = None, parse_mode: str = 'Markdown'):
    """Отправить сообщение в Telegram"""
    import requests
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        resp = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"[TG] Ошибка отправки: {e}")
        return None


def telegram_edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict = None):
    """Редактировать сообщение в Telegram"""
    import requests
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        resp = requests.post(f"{TELEGRAM_API_URL}/editMessageText", json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"[TG] Ошибка редактирования: {e}")
        return None


def telegram_answer_callback(callback_query_id: str):
    """Ответить на callback query"""
    import requests
    try:
        requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery",
                     json={'callback_query_id': callback_query_id}, timeout=5)
    except:
        pass


@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """
    Webhook endpoint для Telegram бота

    Обрабатывает:
    - /start - приветствие
    - /login username password - авторизация
    - callback_query - нажатия на кнопки
    """
    try:
        update = request.get_json()
        logger.info(f"[TG Webhook] Update: {json.dumps(update, ensure_ascii=False)[:500]}")

        # Обработка сообщений
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            telegram_id = message['from']['id']
            text = message.get('text', '')

            # /start
            if text.startswith('/start'):
                user = db.get_user_by_telegram_id(telegram_id)
                if user:
                    keyboard = {'inline_keyboard': [[{'text': 'НАЧАТЬ 🚀', 'callback_data': 'start_training'}]]}
                    telegram_send_message(
                        chat_id,
                        f"Привет, {user.get('username', 'пользователь')}! 👋\n\n"
                        "Готов потренировать английские слова?\n\n"
                        "Нажми НАЧАТЬ для запуска теста из 8 слов.",
                        reply_markup=keyboard
                    )
                else:
                    telegram_send_message(
                        chat_id,
                        "Привет! 👋\n\n"
                        "Для тренировки нужно привязать Telegram к аккаунту.\n\n"
                        "Используй команду:\n"
                        "`/login username password`\n\n"
                        "Например:\n"
                        "`/login andrew test123`"
                    )

            # /login
            elif text.startswith('/login'):
                parts = text.split()
                if len(parts) != 3:
                    telegram_send_message(
                        chat_id,
                        "❌ Формат: `/login username password`\n\n"
                        "Пример: `/login andrew test123`"
                    )
                else:
                    username = parts[1].lower()
                    password = parts[2]

                    if username not in TELEGRAM_TEST_ACCOUNTS:
                        telegram_send_message(chat_id, "❌ Неверный логин или пароль.")
                    elif TELEGRAM_TEST_ACCOUNTS[username]['password'] != password:
                        telegram_send_message(chat_id, "❌ Неверный логин или пароль.")
                    else:
                        user_id = TELEGRAM_TEST_ACCOUNTS[username]['user_id']
                        db.ensure_test_users_exist()
                        success = db.link_telegram_to_user(user_id, telegram_id)

                        if success:
                            keyboard = {'inline_keyboard': [[{'text': 'НАЧАТЬ ТРЕНИРОВКУ 🚀', 'callback_data': 'start_training'}]]}
                            telegram_send_message(
                                chat_id,
                                f"✅ Telegram привязан к аккаунту `{username}`!\n\n"
                                "Теперь можешь тренировать слова!",
                                reply_markup=keyboard
                            )
                        else:
                            telegram_send_message(chat_id, "❌ Ошибка привязки. Попробуй позже.")

            # /train
            elif text.startswith('/train'):
                user = db.get_user_by_telegram_id(telegram_id)
                if user:
                    keyboard = {'inline_keyboard': [[{'text': 'НАЧАТЬ 🚀', 'callback_data': 'start_training'}]]}
                    telegram_send_message(
                        chat_id,
                        "💪 Готов потренировать слова?\n\n"
                        "Нажми кнопку ниже для запуска теста из 8 слов.",
                        reply_markup=keyboard
                    )
                else:
                    telegram_send_message(
                        chat_id,
                        "❌ Сначала авторизуйтесь командой:\n"
                        "`/login username password`"
                    )

        # Обработка callback_query (нажатия кнопок)
        elif 'callback_query' in update:
            callback = update['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            telegram_id = callback['from']['id']
            data = callback.get('data', '')

            telegram_answer_callback(callback_id)

            # start_training
            if data == 'start_training':
                try:
                    user = db.get_user_by_telegram_id(telegram_id)
                    if not user:
                        telegram_edit_message(chat_id, message_id, "❌ Сначала авторизуйтесь: `/login username password`")
                        return jsonify({'ok': True})

                    user_id = user['id']
                    logger.info(f"[TG Webhook] start_training для user_id={user_id}")

                    # Импортируем сервисы
                    from core.training_service import TrainingService
                    from core.test_manager import TestManager
                    from core.yandex_ai_client import YandexAIClient
                    import asyncio

                    training_service = TrainingService(db)
                    words = training_service.select_words_for_training(user_id, count=8)
                    logger.info(f"[TG Webhook] Отобрано слов: {len(words) if words else 0}")

                    if not words:
                        telegram_edit_message(chat_id, message_id, "📚 В твоем словаре пока нет слов.\n\nДобавь слова через веб-интерфейс!")
                        return jsonify({'ok': True})

                    # Проверяем минимальное количество слов (хотя бы 1 слово)
                    MIN_WORDS = 1
                    if len(words) < MIN_WORDS:
                        telegram_edit_message(
                            chat_id, message_id,
                            f"📚 В словаре недостаточно слов для тренировки.\n\n"
                            f"Сейчас: {len(words)} слов\n"
                            f"Минимум: {MIN_WORDS} слово\n\n"
                            f"Добавь ещё слов через веб-интерфейс!"
                        )
                        return jsonify({'ok': True})

                    telegram_edit_message(chat_id, message_id, f"⏳ Генерирую тесты...\n\nСлов: {len(words)}")

                    # Создаем тесты
                    ai_client = YandexAIClient()
                    test_manager = TestManager(db, ai_client)

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    test_ids = loop.run_until_complete(test_manager.create_tests_batch(user_id, words))
                    loop.close()
                    logger.info(f"[TG Webhook] Создано тестов: {len(test_ids) if test_ids else 0}")

                    if not test_ids:
                        telegram_edit_message(chat_id, message_id, "⚠️ Не удалось создать тесты. Попробуй ещё раз.")
                        return jsonify({'ok': True})

                    # Отправляем первый тест
                    send_telegram_test(chat_id, message_id, test_manager, test_ids, 0)

                except Exception as e:
                    import traceback
                    error_details = str(e)[:200]  # Первые 200 символов ошибки
                    logger.error(f"[TG Webhook] Ошибка start_training: {e}", exc_info=True)
                    keyboard = {'inline_keyboard': [[{'text': '🔄 Попробовать снова', 'callback_data': 'start_training'}]]}
                    telegram_edit_message(
                        chat_id, message_id,
                        f"⚠️ Ошибка при запуске тренировки:\n\n`{error_details}`",
                        reply_markup=keyboard
                    )

            # answer_X_Y (ответ на тест)
            elif data.startswith('answer_'):
                parts = data.split('_')
                if len(parts) == 3:
                    test_id = int(parts[1])
                    option_idx = int(parts[2])

                    from core.test_manager import TestManager
                    from core.yandex_ai_client import YandexAIClient

                    ai_client = YandexAIClient()
                    test_manager = TestManager(db, ai_client)

                    # Получаем тест для определения выбранного варианта
                    test = test_manager.get_test_with_shuffled_options(test_id)
                    if not test:
                        telegram_edit_message(chat_id, message_id, "⚠️ Тест не найден")
                        return jsonify({'ok': True})

                    # Находим выбранный вариант по индексу
                    selected = None
                    for opt in test['options']:
                        if opt['index'] == option_idx:
                            selected = opt['text']
                            break

                    if not selected:
                        telegram_edit_message(chat_id, message_id, "⚠️ Вариант не найден")
                        return jsonify({'ok': True})

                    # Проверяем ответ
                    result = test_manager.submit_answer(test_id, selected)

                    if result['is_correct']:
                        text = f"✅ Правильно!\n\n"
                    else:
                        text = f"❌ Неправильно\n\nПравильный ответ: **{result['correct_translation']}**\n\n"

                    text += f"Слово: **{result['word']}**\n"
                    text += f"Рейтинг: {result['new_rating']}/10\n"
                    text += f"Статус: {result['new_status']}"

                    # Кнопка "Дальше"
                    keyboard = {'inline_keyboard': [[{'text': 'Дальше ➡️', 'callback_data': f'next_{test_id}'}]]}
                    telegram_edit_message(chat_id, message_id, text, reply_markup=keyboard)

            # next_X (следующий тест)
            elif data.startswith('next_'):
                user = db.get_user_by_telegram_id(telegram_id)
                if not user:
                    return jsonify({'ok': True})

                # Проверяем есть ли ещё тесты
                from core.test_manager import TestManager
                from core.yandex_ai_client import YandexAIClient

                ai_client = YandexAIClient()
                test_manager = TestManager(db, ai_client)

                pending = test_manager.get_pending_tests(user['id'])
                if not pending:
                    keyboard = {'inline_keyboard': [[{'text': 'ЕЩЁ 8 СЛОВ 🚀', 'callback_data': 'start_training'}]]}
                    telegram_edit_message(chat_id, message_id, "🎉 Все тесты пройдены!\n\nХочешь ещё?", reply_markup=keyboard)
                else:
                    test_ids = [t['id'] for t in pending]
                    send_telegram_test(chat_id, message_id, test_manager, test_ids, 0)

        return jsonify({'ok': True})

    except Exception as e:
        logger.error(f"[TG Webhook] Error: {e}", exc_info=True)
        return jsonify({'ok': True})  # Всегда возвращаем 200 чтобы Telegram не ретраил


@app.route('/telegram/set-webhook', methods=['GET'])
def telegram_set_webhook():
    """
    Установить webhook для Telegram бота
    Вызывать один раз после деплоя: /telegram/set-webhook?url=https://your-domain.com
    """
    import requests

    # Получаем URL из параметра или используем дефолтный
    base_url = request.args.get('url', '')
    if not base_url:
        return jsonify({
            'error': 'Укажи URL: /telegram/set-webhook?url=https://your-domain.com'
        }), 400

    webhook_url = f"{base_url}/telegram/webhook"

    try:
        resp = requests.post(
            f"{TELEGRAM_API_URL}/setWebhook",
            json={'url': webhook_url},
            timeout=10
        )
        result = resp.json()

        if result.get('ok'):
            return jsonify({
                'success': True,
                'message': f'Webhook установлен: {webhook_url}',
                'telegram_response': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('description', 'Unknown error'),
                'telegram_response': result
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/telegram/set-commands', methods=['GET'])
def telegram_set_commands():
    """
    Установить команды бота в меню Telegram
    Вызывать после деплоя: /telegram/set-commands
    """
    import requests

    commands = [
        {"command": "start", "description": "🚀 Начать работу с ботом"},
        {"command": "login", "description": "🔑 Привязать аккаунт (login password)"},
        {"command": "train", "description": "💪 Начать тренировку слов"},
    ]

    try:
        resp = requests.post(
            f"{TELEGRAM_API_URL}/setMyCommands",
            json={'commands': commands},
            timeout=10
        )
        result = resp.json()

        if result.get('ok'):
            return jsonify({
                'success': True,
                'message': 'Команды бота установлены',
                'commands': commands,
                'telegram_response': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('description', 'Unknown error'),
                'telegram_response': result
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/telegram/webhook-info', methods=['GET'])
def telegram_webhook_info():
    """Получить информацию о текущем webhook"""
    import requests

    try:
        resp = requests.get(f"{TELEGRAM_API_URL}/getWebhookInfo", timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/telegram/test-send', methods=['GET'])
def telegram_test_send():
    """Тест отправки сообщения в Telegram"""
    chat_id = request.args.get('chat_id')
    if not chat_id:
        return jsonify({'error': 'Укажи chat_id: /telegram/test-send?chat_id=123456'}), 400

    # Тест 1: проверяем токен
    token_status = "OK" if TELEGRAM_BOT_TOKEN else "EMPTY!"

    # Тест 2: проверяем YDB
    ydb_status = "OK"
    try:
        db.ensure_test_users_exist()
    except Exception as e:
        ydb_status = f"ERROR: {str(e)}"

    # Тест 3: отправляем сообщение (без Markdown чтобы избежать ошибок парсинга)
    result = telegram_send_message(
        int(chat_id),
        f"🧪 Тест webhook!\n\nToken: {token_status}\nYDB: {ydb_status}",
        parse_mode=None
    )

    return jsonify({
        'token_status': token_status,
        'ydb_status': ydb_status,
        'telegram_response': result
    })


def send_telegram_test(chat_id: int, message_id: int, test_manager, test_ids: list, index: int):
    """Отправить тест в Telegram"""
    if index >= len(test_ids):
        keyboard = {'inline_keyboard': [[{'text': 'ЕЩЁ 8 СЛОВ 🚀', 'callback_data': 'start_training'}]]}
        telegram_edit_message(chat_id, message_id, "🎉 Все тесты пройдены!\n\nХочешь ещё?", reply_markup=keyboard)
        return

    test_id = test_ids[index]
    test = test_manager.get_test_with_shuffled_options(test_id)

    if not test:
        # Пропускаем этот тест
        send_telegram_test(chat_id, message_id, test_manager, test_ids, index + 1)
        return

    # Создаем кнопки
    buttons = []
    for opt in test['options']:
        buttons.append([{'text': opt['text'], 'callback_data': f"answer_{test_id}_{opt['index']}"}])

    keyboard = {'inline_keyboard': buttons}

    text = (
        f"📝 Тест {index + 1}/{len(test_ids)}\n\n"
        f"🇬🇧 **{test['word']}**\n\n"
        f"Выберите правильный перевод:"
    )

    telegram_edit_message(chat_id, message_id, text, reply_markup=keyboard)


@app.route('/dictionary')
def dictionary_page():
    """📚 Страница личного словаря"""
    return render_template('dictionary-v2.html')


@app.route('/training')
def training_page():
    """🎯 Страница тренировки слов"""
    return render_template('training.html')


@app.route('/api/training/start', methods=['POST'])
def api_training_start():
    """Начать новую тренировку - отобрать 8 слов и создать тесты"""
    try:
        from core.training_service import TrainingService
        from core.test_manager import TestManager
        from core.yandex_ai_client import YandexAIClient
        import asyncio

        # Проверяем авторизацию
        user_id = session.get('user_id')
        logger.info(f"[/api/training/start] user_id из сессии: {user_id}")

        if not user_id:
            return jsonify({'error': 'Требуется авторизация'}), 401

        # Отбираем слова для тренировки
        training_service = TrainingService(db)
        words = training_service.select_words_for_training(user_id, count=3)  # ВРЕМЕННО: 3 слова для отладки
        logger.info(f"[/api/training/start] TrainingService вернул {len(words)} слов")

        if not words:
            logger.warning(f"[/api/training/start] Не удалось отобрать слова для user_id={user_id}")
            return jsonify({'error': 'В вашем словаре недостаточно слов для тренировки'}), 400

        # Создаем тесты
        logger.info(f"[/api/training/start] Создаем тесты для {len(words)} слов")
        ai_client = YandexAIClient()
        test_manager = TestManager(db, ai_client)

        # Используем asyncio для создания тестов
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        logger.info(f"[/api/training/start] Вызываем create_tests_batch")
        test_ids = loop.run_until_complete(
            test_manager.create_tests_batch(user_id, words)
        )
        logger.info(f"[/api/training/start] create_tests_batch вернул {len(test_ids) if test_ids else 0} test_ids")

        if not test_ids:
            logger.error(f"[/api/training/start] test_ids пустой!")
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
        from core.test_manager import TestManager
        from core.yandex_ai_client import YandexAIClient

        # Проверяем авторизацию
        user_id = session.get('user_id')

        if not user_id:
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


# =============================================================================
# TEST ENDPOINTS - AI Agent Testing
# =============================================================================

@app.route('/test-ai-agent')
def test_ai_agent_page():
    """Страница для тестирования AI агента"""
    return render_template('test-ai-agent.html')


@app.route('/api/test/ai-agent', methods=['POST'])
def test_ai_agent():
    """
    Прямой вызов AI агента для тестирования

    Body: {
        "words": [
            {"word": "velocity", "correct_translation": "скорость"}
        ]
    }
    """
    try:
        import asyncio
        data = request.get_json()
        words = data.get('words', [])

        if not words:
            return jsonify({'error': 'Нужен массив words'}), 400

        # Вызываем агента напрямую
        from core.yandex_ai_client import YandexAIClient
        ai_client = YandexAIClient()

        logger.info(f"[TEST] Вызов агента с {len(words)} словами")

        # Используем тот же паттерн что и в /api/analyze
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            ai_client.generate_test_options(words)
        )

        logger.info(f"[TEST] Агент вернул: {result}")

        return jsonify({
            'success': True,
            'raw_response': result,
            'tests_count': len(result.get('tests', []))
        })

    except Exception as e:
        logger.error(f"[TEST] Ошибка: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500


@app.route('/api/test/create-tests', methods=['POST'])
def test_create_tests():
    """
    Тест создания тестов через TestManager (как в боте)

    Body: {
        "user_id": 1,
        "count": 3
    }
    """
    try:
        import asyncio
        data = request.get_json()
        user_id = data.get('user_id', 1)
        count = data.get('count', 3)

        # Получаем слова
        from core.training_service import TrainingService
        training_service = TrainingService(db)

        words = training_service.select_words_for_training(user_id, count)
        logger.info(f"[TEST] Отобрано {len(words)} слов для тренировки")

        # Создаём тесты
        from core.yandex_ai_client import YandexAIClient
        from core.test_manager import TestManager

        ai_client = YandexAIClient()
        test_manager = TestManager(db, ai_client)

        # Используем тот же паттерн что и в /api/analyze
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        test_ids = loop.run_until_complete(
            test_manager.create_tests_batch(user_id, words)
        )

        logger.info(f"[TEST] Создано {len(test_ids)} тестов")

        return jsonify({
            'success': True,
            'test_ids': test_ids,
            'words_selected': len(words),
            'tests_created': len(test_ids)
        })

    except Exception as e:
        logger.error(f"[TEST] Ошибка создания тестов: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500


if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса Wordoorio...")
    print("📱 Откройте http://localhost:8081 в браузере")
    app.run(debug=True, host='0.0.0.0', port=8081)