#!/usr/bin/env python3
"""
Отладочный скрипт для проверки хайлайтов
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_highlights():
    """Проверить состояние хайлайтов в БД"""
    db = WordoorioDatabase()

    # 1. Проверяем analyses
    print("\n" + "="*80)
    print("ANALYSES")
    print("="*80)
    analyses_query = """
    SELECT id, user_id, session_id, analysis_date, total_highlights, total_words
    FROM analyses
    ORDER BY analysis_date DESC
    LIMIT 10
    """
    analyses = db._fetch_all(analyses_query, {})
    for analysis in analyses:
        print(f"Analysis ID: {analysis['id']}, User: {analysis.get('user_id')}, Session: {analysis.get('session_id')}, Highlights: {analysis.get('total_highlights', 0)}")

    # 2. Проверяем highlights
    print("\n" + "="*80)
    print("HIGHLIGHTS")
    print("="*80)
    highlights_query = """
    SELECT id, analysis_id, word_id, position
    FROM highlights
    LIMIT 20
    """
    highlights = db._fetch_all(highlights_query, {})
    print(f"Всего highlights: {len(highlights)}")
    for highlight in highlights:
        print(f"  ID: {highlight['id']}, Analysis: {highlight['analysis_id']}, Word ID: {highlight['word_id']}, Position: {highlight['position']}")

    # 3. Проверяем dictionary_words
    print("\n" + "="*80)
    print("DICTIONARY_WORDS")
    print("="*80)
    words_query = """
    SELECT id, lemma, user_id, added_at
    FROM dictionary_words
    LIMIT 20
    """
    words = db._fetch_all(words_query, {})
    print(f"Всего слов: {len(words)}")
    for word in words:
        print(f"  ID: {word['id']}, Lemma: {word['lemma']}, User: {word.get('user_id')}")

    # 4. Проверяем связь highlights -> words
    print("\n" + "="*80)
    print("HIGHLIGHTS -> WORDS JOIN")
    print("="*80)
    join_query = """
    SELECT
        h.id AS highlight_id,
        h.analysis_id,
        h.word_id,
        w.lemma,
        w.user_id
    FROM highlights AS h
    INNER JOIN dictionary_words AS w ON h.word_id = w.id
    LIMIT 20
    """
    joined = db._fetch_all(join_query, {})
    print(f"Найдено связанных записей: {len(joined)}")
    for row in joined:
        print(f"  Highlight {row['highlight_id']}: Analysis {row['analysis_id']} -> Word '{row['lemma']}' (id={row['word_id']})")

    # 5. Пробуем вызвать get_user_highlights для user_id=1
    print("\n" + "="*80)
    print("GET_USER_HIGHLIGHTS(user_id=1)")
    print("="*80)
    try:
        highlights = db.get_user_highlights(user_id=1, limit=10)
        print(f"Результат: {len(highlights)} analyses")
        for i, analysis in enumerate(highlights):
            print(f"\n  Analysis #{i+1}:")
            print(f"    ID: {analysis.get('id')}")
            print(f"    Date: {analysis.get('analysis_date')}")
            print(f"    Highlights: {len(analysis.get('highlights', []))}")
            for h in analysis.get('highlights', []):
                print(f"      - {h.get('highlight')}: {h.get('highlight_translation')}")
    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_highlights()
