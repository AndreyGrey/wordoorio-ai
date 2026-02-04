#!/usr/bin/env python3
"""
Telegram Bot для тренировки английских слов
Polling mode, интеграция с TrainingService и TestManager (YDB версия)
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
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
    ConversationHandler,
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

# Состояния ConversationHandler
TRAINING = 1


def get_main_keyboard():
    """Создать основную клавиатуру с кнопками"""
    keyboard = [
        [KeyboardButton("💪 Начать тренировку")],
        [KeyboardButton("📊 Моя статистика"), KeyboardButton("📚 Мой словарь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_user_id_from_telegram(telegram_id: int) -> Optional[int]:
    """Получить user_id по telegram_id"""
    user = db.get_user_by_telegram_id(telegram_id)
    if user:
        return user.get('id')
    return None


# =============================================================================
# КОМАНДЫ
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        username = user.get('username', 'пользователь')
        await update.message.reply_text(
            f"Привет, {username}! 👋\n\n"
            "Готов потренировать английские слова из твоего словаря?\n\n"
            "Используй кнопки ниже:",
            reply_markup=get_main_keyboard()
        )
    else:
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
    """Обработчик команды /login username password"""
    telegram_id = update.effective_user.id

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
    success = db.link_telegram_to_user(user_id, telegram_id)

    if success:
        await update.message.reply_text(
            f"✅ Telegram привязан к аккаунту `{username}`.\n\n"
            "Теперь можешь тренировать слова!",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка привязки аккаунта. Попробуй позже."
        )


async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /train"""
    telegram_id = update.effective_user.id
    user_id = get_user_id_from_telegram(telegram_id)

    if not user_id:
        await update.message.reply_text(
            "❌ Сначала авторизуйтесь:\n`/login username password`",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    # Начинаем тренировку
    return await start_training(update, context, user_id)


# =============================================================================
# ТРЕНИРОВКА
# =============================================================================

async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
    """Запуск тренировки - загрузка тестов"""

    # Определяем user_id
    if user_id is None:
        telegram_id = update.effective_user.id
        user_id = get_user_id_from_telegram(telegram_id)

        if not user_id:
            await update.message.reply_text(
                "❌ Сначала авторизуйтесь:\n`/login username password`",
                parse_mode='Markdown'
            )
            return ConversationHandler.END

    # Отправляем сообщение о загрузке
    loading_msg = await update.message.reply_text(
        "⏳ Генерирую тесты...\n\n"
        "AI подбирает варианты ответов для твоих слов."
    )

    try:
        # 1. Отбираем слова для тренировки
        words = training_service.select_words_for_training(user_id, count=8)

        if not words:
            await loading_msg.edit_text(
                "📚 В твоём словаре пока нет слов.\n\n"
                "Добавь слова через веб-интерфейс и возвращайся!"
            )
            return ConversationHandler.END

        # 2. Создаем тесты через AI
        test_ids = await test_manager.create_tests_batch(user_id, words)

        if not test_ids:
            await loading_msg.edit_text(
                "⚠️ Не удалось создать тесты.\n"
                "Проверь, что у слов есть переводы."
            )
            return ConversationHandler.END

        # 3. Загружаем все тесты с перемешанными вариантами
        tests = []
        for test_id in test_ids:
            test = test_manager.get_test_with_shuffled_options(test_id)
            if test:
                tests.append(test)

        if not tests:
            await loading_msg.edit_text("⚠️ Ошибка загрузки тестов.")
            return ConversationHandler.END

        # 4. Сохраняем состояние тренировки
        context.user_data['tests'] = tests
        context.user_data['current_index'] = 0
        context.user_data['correct_count'] = 0
        context.user_data['incorrect_count'] = 0
        context.user_data['loading_msg_id'] = loading_msg.message_id

        # 5. Удаляем сообщение о загрузке и показываем первый тест
        await loading_msg.delete()
        return await show_current_test(update, context)

    except Exception as e:
        logger.error(f"Ошибка запуска тренировки: {e}")
        await loading_msg.edit_text(
            f"⚠️ Произошла ошибка:\n{str(e)}\n\n"
            "Попробуй позже."
        )
        return ConversationHandler.END


async def show_current_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущий тест"""
    tests = context.user_data.get('tests', [])
    index = context.user_data.get('current_index', 0)

    # Проверяем, все ли тесты пройдены
    if index >= len(tests):
        return await show_results(update, context)

    test = tests[index]
    total = len(tests)

    # Формируем прогресс-бар
    progress = int((index / total) * 10)
    progress_bar = "▓" * progress + "░" * (10 - progress)

    # Формируем кнопки с вариантами
    keyboard = []
    for i, option in enumerate(test['options']):
        keyboard.append([
            InlineKeyboardButton(
                option['text'],
                callback_data=f"ans:{i}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем текст сообщения
    text = (
        f"📝 Тест {index + 1}/{total}\n"
        f"{progress_bar}\n\n"
        f"🔤 *{test['word']}*\n\n"
        f"Выбери перевод:"
    )

    # Отправляем или редактируем сообщение
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    return TRAINING


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на тест"""
    query = update.callback_query
    await query.answer()

    # Парсим callback_data
    data = query.data
    if not data.startswith("ans:"):
        return TRAINING

    option_index = int(data.split(":")[1])

    # Получаем текущий тест
    tests = context.user_data.get('tests', [])
    index = context.user_data.get('current_index', 0)

    if index >= len(tests):
        return await show_results(update, context)

    test = tests[index]
    selected_option = test['options'][option_index]
    is_correct = selected_option['is_correct']

    # Находим правильный ответ
    correct_option = next(opt for opt in test['options'] if opt['is_correct'])

    # Обновляем счетчики
    if is_correct:
        context.user_data['correct_count'] = context.user_data.get('correct_count', 0) + 1
    else:
        context.user_data['incorrect_count'] = context.user_data.get('incorrect_count', 0) + 1

    # Отправляем результат в БД (асинхронно, не блокируем UI)
    try:
        result = test_manager.submit_answer(test['test_id'], selected_option['text'])
        logger.info(f"[BOT] submit_answer result: {result}")
        new_rating = result.get('new_rating', 0)
        new_status = result.get('new_status', 'learning')
        additional_meanings = result.get('additional_meanings', [])
        logger.info(f"[BOT] additional_meanings: {additional_meanings}")
    except Exception as e:
        logger.error(f"Ошибка сохранения ответа: {e}")
        import traceback
        logger.error(traceback.format_exc())
        new_rating = 0
        new_status = "?"
        additional_meanings = []

    # Строка с дополнительными значениями
    meanings_line = ""
    if additional_meanings:
        # Экранируем спецсимволы Markdown
        escaped = [m.replace('_', '\\_').replace('*', '\\*') for m in additional_meanings]
        meanings_line = f"\n📖 А ещё: {', '.join(escaped)}"

    # Формируем сообщение с результатом
    if is_correct:
        # Рейтинг со звездочками
        stars = "⭐" * min(new_rating, 10)
        if new_rating >= 10:
            status_text = "🎓 Выучено!"
        else:
            status_text = f"Рейтинг: {new_rating}/10"

        text = (
            f"✅ *Верно!*\n\n"
            f"{test['word']} → {correct_option['text']}"
            f"{meanings_line}\n\n"
            f"{status_text} {stars}"
        )
    else:
        text = (
            f"❌ *Неверно*\n\n"
            f"{test['word']} → *{correct_option['text']}*\n"
            f"(не \"{selected_option['text']}\")"
            f"{meanings_line}\n\n"
            f"Рейтинг сброшен: 0/10"
        )

    # Кнопка "Дальше"
    keyboard = [[InlineKeyboardButton("Дальше →", callback_data="next")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return TRAINING


async def next_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к следующему тесту"""
    query = update.callback_query
    await query.answer()

    # Увеличиваем индекс
    context.user_data['current_index'] = context.user_data.get('current_index', 0) + 1

    return await show_current_test(update, context)


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать итоговые результаты тренировки"""
    correct = context.user_data.get('correct_count', 0)
    incorrect = context.user_data.get('incorrect_count', 0)
    total = correct + incorrect

    accuracy = round((correct / total) * 100) if total > 0 else 0

    # Выбираем эмодзи в зависимости от результата
    if accuracy >= 80:
        emoji = "🎉"
        comment = "Отличный результат!"
    elif accuracy >= 60:
        emoji = "👍"
        comment = "Хороший результат!"
    elif accuracy >= 40:
        emoji = "💪"
        comment = "Есть над чем поработать"
    else:
        emoji = "📚"
        comment = "Нужно больше практики"

    text = (
        f"{emoji} *Тренировка завершена!*\n\n"
        f"{comment}\n\n"
        f"📊 *Результаты:*\n"
        f"✅ Верно: {correct}\n"
        f"❌ Ошибок: {incorrect}\n"
        f"🎯 Точность: {accuracy}%"
    )

    keyboard = [[InlineKeyboardButton("🔄 Ещё раз", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Очищаем состояние
    context.user_data.clear()

    return ConversationHandler.END


async def restart_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск тренировки"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    user_id = get_user_id_from_telegram(telegram_id)

    if not user_id:
        await query.edit_message_text(
            "❌ Сначала авторизуйтесь:\n`/login username password`",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    # Удаляем старое сообщение
    await query.message.delete()

    # Создаем fake update с message для start_training
    class FakeUpdate:
        def __init__(self, message):
            self.message = message
            self.effective_user = query.from_user

    # Отправляем новое сообщение
    msg = await query.message.chat.send_message("⏳ Генерирую тесты...")

    class FakeMessage:
        def __init__(self, msg):
            self._msg = msg
            self.chat = msg.chat

        async def reply_text(self, text, **kwargs):
            return await self.chat.send_message(text, **kwargs)

    fake_update = FakeUpdate(FakeMessage(msg))

    # Удаляем временное сообщение
    await msg.delete()

    return await start_training(fake_update, context, user_id)


async def cancel_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена тренировки"""
    context.user_data.clear()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Тренировка отменена.\n\n"
            "Используй кнопки ниже для продолжения.",
            reply_markup=None
        )
    else:
        await update.message.reply_text(
            "Тренировка отменена.",
            reply_markup=get_main_keyboard()
        )

    return ConversationHandler.END


# =============================================================================
# СТАТИСТИКА И СЛОВАРЬ
# =============================================================================

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику пользователя"""
    telegram_id = update.effective_user.id
    user_id = get_user_id_from_telegram(telegram_id)

    if not user_id:
        await update.message.reply_text(
            "❌ Сначала авторизуйтесь:\n`/login username password`",
            parse_mode='Markdown'
        )
        return

    try:
        # Получаем статистику из БД
        stats = db.get_dictionary_stats(user_id)

        total = stats.get('total', 0)
        new_count = stats.get('new', 0)
        learning_count = stats.get('learning', 0)
        learned_count = stats.get('learned', 0)

        # Вычисляем процент выученных
        progress = round((learned_count / total) * 100) if total > 0 else 0

        text = (
            "📊 *Твоя статистика*\n\n"
            f"📚 Всего слов: {total}\n\n"
            f"🆕 Новых: {new_count}\n"
            f"📖 На изучении: {learning_count}\n"
            f"✅ Выучено: {learned_count}\n\n"
            f"🎯 Прогресс: {progress}%"
        )

        await update.message.reply_text(
            text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await update.message.reply_text(
            "⚠️ Не удалось загрузить статистику.",
            reply_markup=get_main_keyboard()
        )


async def show_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать словарь пользователя"""
    telegram_id = update.effective_user.id
    user_id = get_user_id_from_telegram(telegram_id)

    if not user_id:
        await update.message.reply_text(
            "❌ Сначала авторизуйтесь:\n`/login username password`",
            parse_mode='Markdown'
        )
        return

    try:
        # Получаем последние слова из словаря
        words = db.get_user_words(user_id, limit=10)

        if not words:
            await update.message.reply_text(
                "📚 Твой словарь пока пуст.\n\n"
                "Добавляй слова через веб-интерфейс!",
                reply_markup=get_main_keyboard()
            )
            return

        # Формируем список слов
        text = "📚 *Твой словарь* (последние 10 слов)\n\n"

        for word in words:
            lemma = word.get('lemma', '?')
            status = word.get('status', 'new')
            rating = word.get('rating', 0) or 0

            # Иконка статуса
            if status == 'learned':
                icon = "✅"
            elif status == 'learning':
                icon = "📖"
            else:
                icon = "🆕"

            # Получаем перевод
            translation = db.get_translation_for_word(word.get('id'))
            translation_text = translation if translation else "—"

            text += f"{icon} *{lemma}* — {translation_text} ({rating}/10)\n"

        text += "\n_Управляй словарём через веб-интерфейс_"

        await update.message.reply_text(
            text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Ошибка получения словаря: {e}")
        await update.message.reply_text(
            "⚠️ Не удалось загрузить словарь.",
            reply_markup=get_main_keyboard()
        )


# =============================================================================
# ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
# =============================================================================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (кнопки клавиатуры)"""
    text = update.message.text
    telegram_id = update.effective_user.id

    # Проверяем авторизацию для большинства команд
    user = db.get_user_by_telegram_id(telegram_id)

    if text == "💪 Начать тренировку":
        if not user:
            await update.message.reply_text(
                "❌ Сначала авторизуйтесь:\n`/login username password`",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        return await start_training(update, context, user.get('id'))

    elif text == "📊 Моя статистика":
        return await show_statistics(update, context)

    elif text == "📚 Мой словарь":
        return await show_dictionary(update, context)

    else:
        # Неизвестная команда
        if user:
            await update.message.reply_text(
                "Используй кнопки ниже:",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "Привет! Для начала авторизуйся:\n"
                "`/login username password`",
                parse_mode='Markdown'
            )


# =============================================================================
# ОБРАБОТЧИК ОШИБОК
# =============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")


# =============================================================================
# ИНИЦИАЛИЗАЦИЯ И ЗАПУСК
# =============================================================================

async def post_init(application: Application):
    """Инициализация после запуска бота"""
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("login", "Привязать аккаунт"),
        BotCommand("train", "Начать тренировку"),
        BotCommand("cancel", "Отменить тренировку"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Команды бота зарегистрированы")


def main():
    """Запуск бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return

    # Убеждаемся, что тестовые пользователи существуют в БД
    logger.info("Проверяем тестовых пользователей в БД...")
    db.ensure_test_users_exist()

    # Создаем приложение
    app = Application.builder().token(token).post_init(post_init).build()

    # ConversationHandler для тренировки
    training_handler = ConversationHandler(
        entry_points=[
            CommandHandler("train", train_command),
            MessageHandler(
                filters.Regex("^💪 Начать тренировку$"),
                lambda u, c: start_training(u, c, get_user_id_from_telegram(u.effective_user.id))
            ),
        ],
        states={
            TRAINING: [
                CallbackQueryHandler(handle_answer, pattern=r"^ans:\d+$"),
                CallbackQueryHandler(next_test, pattern=r"^next$"),
                CallbackQueryHandler(restart_training, pattern=r"^restart$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_training),
            CallbackQueryHandler(restart_training, pattern=r"^restart$"),
        ],
        allow_reentry=True,
    )

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(training_handler)

    # Обработчики кнопок статистики и словаря (вне ConversationHandler)
    app.add_handler(MessageHandler(filters.Regex("^📊 Моя статистика$"), show_statistics))
    app.add_handler(MessageHandler(filters.Regex("^📚 Мой словарь$"), show_dictionary))

    # Обработчик всех остальных текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
