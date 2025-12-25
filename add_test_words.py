#!/usr/bin/env python3
"""
Скрипт для добавления тестовых слов для тренировки
"""

from database import WordoorioDatabase
from datetime import datetime
import sqlite3

db = WordoorioDatabase()

# ID пользователя (Andrew_KW)
user_id = 1

# Тестовые слова
test_words = [
    ("incentives", "noun", "стимулы, поощрения"),
    ("quirky", "adjective", "своеобразный, причудливый"),
    ("vast", "adjective", "обширный, огромный"),
    ("optimise", "verb", "оптимизировать"),
    ("compelling", "adjective", "убедительный, неотразимый"),
    ("sophisticated", "adjective", "утончённый, изысканный"),
    ("scrutinize", "verb", "внимательно изучать"),
    ("ambiguous", "adjective", "двусмысленный"),
    ("eloquent", "adjective", "красноречивый"),
    ("meticulous", "adjective", "дотошный, скрупулезный"),
    ("resilient", "adjective", "устойчивый, жизнестойкий"),
    ("profound", "adjective", "глубокий, основательный"),
]

print("🔧 Добавление тестовых слов...")

with sqlite3.connect(db.db_path) as conn:
    cursor = conn.cursor()

    added = 0
    for lemma, word_type, translation in test_words:
        # Проверяем, есть ли уже слово
        cursor.execute("""
            SELECT id FROM dictionary_words
            WHERE user_id = ? AND lemma = ?
        """, (user_id, lemma))

        existing = cursor.fetchone()

        if not existing:
            now = datetime.now().isoformat()

            # Добавляем слово
            cursor.execute("""
                INSERT INTO dictionary_words (user_id, lemma, type, status, added_at, rating)
                VALUES (?, ?, ?, 'new', ?, 0)
            """, (user_id, lemma, word_type, now))
            word_id = cursor.lastrowid

            # Добавляем перевод
            cursor.execute("""
                INSERT INTO dictionary_translations (word_id, translation, added_at)
                VALUES (?, ?, ?)
            """, (word_id, translation, now))

            added += 1
            print(f"  ✅ {lemma}")

    conn.commit()

    # Проверяем итог
    cursor.execute("SELECT COUNT(*) FROM dictionary_words WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]

    print(f"\n✅ Добавлено слов: {added}")
    print(f"📊 Всего слов в словаре: {total}")
    print(f"\n🚀 Готово! Можно тестировать тренировки на http://localhost:8081/training")
