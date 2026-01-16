#!/usr/bin/env python3
"""
Telegram Bot для тренировки английских слов
Polling mode, интеграция с TrainingService и TestManager (YDB версия)
"""

import os
import asyncio
import logging
from typing import Dict
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Импорты из проекта
from database import WordoorioDatabase
from core.training_service import TrainingService
from core.test_manager import TestManager
from core.yandex_ai_client import YandexAIClient

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
db = WordoorioDatabase()
ai_client = YandexAIClient()
training_service = TrainingService(db)
test_manager = TestManager(db, ai_client)

# Тестовые аккаунты (синхронизированы с web_app.py)
TEST_ACCOUNTS = {
    'andrew': {'password': 'test123', 'user_id': 1},
    'friend1': {'password': 'test123', 'user_id': 2},
    'friend2': {'password': 'test123', 'user_id': 3},
}


def get_main_keyboard():
    """Создать основную клавиатуру с кнопками"""
    keyboard = [
        [KeyboardButton("💪 Начать тренировку")],
        [KeyboardButton("📊 Моя статистика"), KeyboardButton("📚 Мой словарь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    telegram_id = update.effective_user.id

    # Проверяем, привязан ли Telegram к аккаунту
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        # Пользователь уже авторизован - показываем основную клавиатуру
        username = user.get('username', 'пользователь')
        await update.message.reply_text(
            f"Привет, {username}! 👋\n\n"
            "Готов потренировать английские слова из твоего словаря?\n\n"
            "Используй кнопки ниже для быстрого доступа:",
            reply_markup=get_main_keyboard()
        )
    else:
        # Нужна авторизация
        await update.message.reply_text(
            "Привет! 👋\n\n"
            "Для начала тренировки нужно привязать Telegram к аккаунту.\n\n"
            "Используй команду:\n"
            "`/login username password`\n\n"
            "Например:\n"
            "`/login andrew test123`",
            parse_mode='Markdown'
        )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /login username password
    Привязывает Telegram ID к существующему аккаунту
    """
    telegram_id = update.effective_user.id

    # Проверяем аргументы
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Неверный формат команды.\n\n"
            "Используй:\n"
            "`/login username password`\n\n"
            "Например:\n"
            "`/login andrew test123`",
            parse_mode='Markdown'
        )
        return

    username = context.args[0].lower()
    password = context.args[1]

    # Проверяем логин/пароль
    if username not in TEST_ACCOUNTS:
        await update.message.reply_text(
            "❌ Неверный логин или пароль.\n\n"
            "Доступные тестовые аккаунты:\n"
            "• andrew / test123\n"
            "• friend1 / test123\n"
            "• friend2 / test123"
        )
        return

    account = TEST_ACCOUNTS[username]

    if account['password'] != password:
        await update.message.reply_text("❌ Неверный логин или пароль.")
        return

    user_id = account['user_id']

    # Привязываем Telegram к аккаунту
    success = db.link_telegram_to_user(user_id, telegram_id)

    if success:
        await update.message.reply_text(
            f"✅ Отлично! Telegram привязан к аккаунту `{username}`.\n\n"
            "Теперь можешь тренировать слова!\n\n"
            "Используй кнопки ниже для быстрого доступа:",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка привязки аккаунта. Попробуй позже."
        )


async def start_training_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки НАЧАТЬ - запуск тренировки"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id

    # Получаем пользователя по telegram_id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await query.edit_message_text(
            "❌ Сначала авторизуйтесь командой:\n"
            "`/login username password`",
            parse_mode='Markdown'
        )
        return

    user_id = user['id']

    # Отбираем 8 слов для тренировки
    try:
        words = training_service.select_words_for_training(user_id, count=8)
    except Exception as e:
        logger.error(f"Ошибка отбора слов: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка при отборе слов. Попробуйте позже."
        )
        return

    if not words:
        await query.edit_message_text(
            "📚 В твоем словаре пока нет слов.\n\n"
            "Добавь слова через веб-интерфейс и возвращайся!"
        )
        return

    # Создаем тесты (async!)
    await query.edit_message_text(
        "⏳ Генерирую тесты...\n\n"
        f"Слов для тренировки: {len(words)}"
    )

    try:
        test_ids = await test_manager.create_tests_batch(user_id, words)
    except Exception as e:
        logger.error(f"Ошибка создания тестов: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка при создании тестов. Попробуйте позже."
        )
        return

    if not test_ids:
        await query.edit_message_text(
            "⚠️ Не удалось создать тесты. Проверьте, что у слов есть переводы."
        )
        return

    # Сохраняем состояние в context
    context.user_data['test_ids'] = test_ids
    context.user_data['current_test_index'] = 0

    # Отправляем первый тест
    await send_next_test(query, context)


async def send_next_test(query_or_message, context: ContextTypes.DEFAULT_TYPE):
    """Отправка следующего теста"""
    test_ids = context.user_data.get('test_ids', [])
    index = context.user_data.get('current_test_index', 0)

    # Проверяем, все ли тесты пройдены
    if index >= len(test_ids):
        keyboard = [[InlineKeyboardButton("НАЧАТЬ ЕЩЁ 8 🚀", callback_data="start_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if hasattr(query_or_message, 'edit_message_text'):
            await query_or_message.edit_message_text(
                "🎉 Отлично! Все тесты пройдены!\n\nХочешь ещё?",
                reply_markup=reply_markup
            )
        else:
            await query_or_message.message.reply_text(
                "🎉 Отлично! Все тесты пройдены!\n\nХочешь ещё?",
                reply_markup=reply_markup
            )
        return

    # Получаем тест с перемешанными вариантами
    test_id = test_ids[index]
    test = test_manager.get_test_with_shuffled_options(test_id)

    if not test:
        # Пропускаем этот тест
        context.user_data['current_test_index'] += 1
        await send_next_test(query_or_message, context)
        return

    # Сохраняем варианты в контексте для проверки ответа
    context.user_data[f'test_{test_id}_options'] = test['options']

    # Создаем кнопки
    keyboard = []
    for option in test['options']:
        # callback_data содержит test_id и текст варианта
        callback_data = f"answer_{test_id}_{option['index']}"
        keyboard.append([InlineKeyboardButton(option['text'], callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"📝 Тест {index + 1}/{len(test_ids)}\n\n"
        f"🇬🇧 **{test['word']}**\n\n"
        f"Выберите правильный перевод:"
    )

    # Отправляем или редактируем сообщение
    if hasattr(query_or_message, 'edit_message_text'):
        await query_or_message.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await query_or_message.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответа на тест"""
    query = update.callback_query
    await query.answer()

    # Парсим callback_data
    parts = query.data.split('_')
    if len(parts) != 3 or parts[0] != 'answer':
        await query.edit_message_text("⚠️ Ошибка обработки ответа")
        return

    test_id = int(parts[1])
    option_index = int(parts[2])

    # Получаем сохраненные варианты
    options = context.user_data.get(f'test_{test_id}_options')
    if not options:
        await query.edit_message_text("⚠️ Тест не найден")
        return

    # Находим выбранный вариант
    selected_option = None
    for opt in options:
        if opt['index'] == option_index:
            selected_option = opt
            break

    if not selected_option:
        await query.edit_message_text("⚠️ Вариант не найден")
        return

    # Проверяем ответ через TestManager
    try:
        result = test_manager.submit_answer(test_id, selected_option['text'])
    except Exception as e:
        logger.error(f"Ошибка проверки ответа: {e}")
        await query.edit_message_text("⚠️ Произошла ошибка при проверке ответа")
        return

    # Показываем результат
    if result['is_correct']:
        text = f"✅ Правильно!\n\n"
    else:
        text = (
            f"❌ Неправильно\n\n"
            f"Правильный ответ: **{result['correct_translation']}**\n\n"
        )

    text += f"Слово: **{result['word']}**\n"
    text += f"Рейтинг: {result['new_rating']}/10\n"
    text += f"Статус: {result['new_status']}"

    await query.edit_message_text(text, parse_mode='Markdown')

    # Пауза 1.5 секунды
    await asyncio.sleep(1.5)

    # Переходим к следующему тесту
    context.user_data['current_test_index'] += 1
    await send_next_test(query, context)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (кнопки клавиатуры)"""
    text = update.message.text
    telegram_id = update.effective_user.id

    # Проверяем авторизацию
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "❌ Сначала авторизуйтесь командой:\n"
            "`/login username password`",
            parse_mode='Markdown'
        )
        return

    # Обработка кнопок
    if text == "💪 Начать тренировку":
        # Показываем inline кнопку для запуска
        keyboard = [[InlineKeyboardButton("НАЧАТЬ 🚀", callback_data="start_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💪 Готов потренировать слова?\n\n"
            "Нажми кнопку ниже для запуска теста из 8 слов.",
            reply_markup=reply_markup
        )

    elif text == "📊 Моя статистика":
        # Получаем статистику пользователя
        # TODO: Реализовать получение статистики из БД
        await update.message.reply_text(
            "📊 Статистика:\n\n"
            "Эта функция в разработке...",
            reply_markup=get_main_keyboard()
        )

    elif text == "📚 Мой словарь":
        # Показываем информацию о словаре
        # TODO: Получить реальные данные из БД
        await update.message.reply_text(
            "📚 Твой словарь:\n\n"
            "Эта функция в разработке...\n\n"
            "Добавляй слова через веб-интерфейс!",
            reply_markup=get_main_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")


async def post_init(application: Application):
    """Инициализация после запуска бота"""
    # Регистрируем команды бота
    commands = [
        BotCommand("start", "🚀 Начать работу с ботом"),
        BotCommand("login", "🔑 Привязать аккаунт (login password)"),
        BotCommand("train", "💪 Начать тренировку слов"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Команды бота зарегистрированы")


async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /train - быстрый запуск тренировки"""
    telegram_id = update.effective_user.id

    # Получаем пользователя по telegram_id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text(
            "❌ Сначала авторизуйтесь командой:\n"
            "`/login username password`",
            parse_mode='Markdown'
        )
        return

    # Показываем кнопку для запуска
    keyboard = [[InlineKeyboardButton("НАЧАТЬ 🚀", callback_data="start_training")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💪 Готов потренировать слова?\n\n"
        "Нажми кнопку ниже для запуска теста из 8 слов.",
        reply_markup=reply_markup
    )


def main():
    """Запуск бота"""
    # Получаем токен бота
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return

    # Убеждаемся, что тестовые пользователи существуют в БД
    logger.info("Проверяем тестовых пользователей в БД...")
    db.ensure_test_users_exist()

    # Создаем приложение
    app = Application.builder().token(token).post_init(post_init).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("train", train_command))
    app.add_handler(CallbackQueryHandler(start_training_callback, pattern="^start_training$"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^answer_"))

    # Обработчик текстовых сообщений (кнопки клавиатуры)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    # Запускаем бота (polling mode)
    logger.info("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
