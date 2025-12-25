#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных для системы тренировки
"""

from database import WordoorioDatabase
from datetime import datetime

db = WordoorioDatabase()

# Создаем тестового пользователя
# ВАЖНО: Замените telegram_id на ваш настоящий!
# Узнать свой telegram_id можно через бота @userinfobot
TELEGRAM_ID = 123456789  # <-- ЗАМЕНИТЕ НА ВАШ telegram_id

print("🔧 Создание тестовых данных...")

# Добавляем пользователя
import sqlite3
with sqlite3.connect(db.db_path) as conn:
    cursor = conn.cursor()

    # Проверяем, есть ли уже пользователь
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (TELEGRAM_ID,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        print(f"✅ Пользователь уже существует (ID: {user_id})")
    else:
        # Создаем пользователя
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (telegram_id, first_name, username, auth_date, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (TELEGRAM_ID, "Test User", "testuser", int(datetime.now().timestamp()), now, now))
        user_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Создан пользователь (ID: {user_id}, telegram_id: {TELEGRAM_ID})")

# Добавляем тестовые слова
test_words = [
    ("sophisticated", "adjective", "утончённый, изысканный"),
    ("compelling", "adjective", "убедительный, неотразимый"),
    ("scrutinize", "verb", "внимательно изучать, рассматривать"),
    ("ambiguous", "adjective", "двусмысленный, неопределенный"),
    ("eloquent", "adjective", "красноречивый"),
    ("meticulous", "adjective", "дотошный, скрупулезный"),
    ("resilient", "adjective", "устойчивый, жизнестойкий"),
    ("profound", "adjective", "глубокий, основательный"),
    ("trivial", "adjective", "тривиальный, незначительный"),
    ("intricate", "adjective", "сложный, запутанный"),
    ("abundant", "adjective", "обильный, изобильный"),
    ("diligent", "adjective", "прилежный, старательный"),
]

with sqlite3.connect(db.db_path) as conn:
    cursor = conn.cursor()

    added_count = 0
    for lemma, word_type, translation in test_words:
        # Проверяем, есть ли уже слово
        cursor.execute("""
            SELECT id FROM dictionary_words
            WHERE user_id = ? AND lemma = ?
        """, (user_id, lemma))

        existing = cursor.fetchone()

        if existing:
            word_id = existing[0]
        else:
            # Добавляем слово
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO dictionary_words (user_id, lemma, type, status, added_at)
                VALUES (?, ?, ?, 'new', ?)
            """, (user_id, lemma, word_type, now))
            word_id = cursor.lastrowid

            # Добавляем перевод
            cursor.execute("""
                INSERT INTO dictionary_translations (word_id, translation, added_at)
                VALUES (?, ?, ?)
            """, (word_id, translation, now))

            added_count += 1

    conn.commit()

    if added_count > 0:
        print(f"✅ Добавлено слов: {added_count}")
    else:
        print(f"✅ Слова уже были в словаре")

# Проверяем итоговое состояние
cursor.execute("""
    SELECT COUNT(*) FROM dictionary_words WHERE user_id = ?
""", (user_id,))
total_words = cursor.fetchone()[0]

print(f"\n📊 Статистика:")
print(f"   User ID: {user_id}")
print(f"   Telegram ID: {TELEGRAM_ID}")
print(f"   Всего слов в словаре: {total_words}")
print(f"\n✅ Готово! Теперь можно запускать бота и тестировать.")
print(f"\n💡 ВАЖНО: Если telegram_id в скрипте не совпадает с вашим настоящим,")
print(f"   обновите переменную TELEGRAM_ID в начале скрипта и запустите снова!")
