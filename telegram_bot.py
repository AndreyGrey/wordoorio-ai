#!/usr/bin/env python3
"""
Telegram Bot для тренировки английских слов
Polling mode, интеграция с TrainingService и TestManager
"""

import os
import asyncio
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from dotenv import load_dotenv

# Импорты из проекта
from database import WordoorioDatabase
from core.training_service import TrainingService
from core.test_manager import TestManager
from core.yandex_ai_client import YandexAIClient
from core.auth_manager import AuthManager

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
auth_manager = AuthManager(db.db_path)  # AuthManager ожидает строку, а не объект


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [[InlineKeyboardButton("НАЧАТЬ 🚀", callback_data="start_training")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Готов потренировать английские слова из твоего словаря?\n\n"
        "Нажми НАЧАТЬ для запуска теста из 8 слов.",
        reply_markup=reply_markup
    )


async def start_training_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки НАЧАТЬ - запуск тренировки"""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id

    # Получаем пользователя по telegram_id
    user = auth_manager.get_user_by_telegram_id(telegram_id)

    if not user:
        await query.edit_message_text(
            "❌ Сначала авторизуйтесь на сайте wordoorio.ru\n\n"
            "Используйте Telegram Login Widget для связи аккаунта."
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
        keyboard = [[InlineKeyboardButton("Перейти на сайт", url="https://wordoorio.ru")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📚 В твоем словаре пока нет слов.\n\n"
            "Добавь слова на wordoorio.ru и возвращайся!",
            reply_markup=reply_markup
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


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Запуск бота"""
    # Получаем токен бота
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return

    # Создаем приложение
    app = Application.builder().token(token).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(start_training_callback, pattern="^start_training$"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^answer_"))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    # Запускаем бота (polling mode)
    logger.info("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
