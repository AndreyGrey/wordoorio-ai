#!/usr/bin/env python3
"""
Скрипт для удаления всех слов анонимных пользователей (user_id IS NULL)
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_anonymous_words():
    """Удалить все слова анонимных пользователей"""
    db = WordoorioDatabase()

    # Получить все слова с user_id IS NULL
    get_words_query = """
    SELECT id, lemma FROM dictionary_words
    WHERE user_id IS NULL
    """

    words = db._fetch_all(get_words_query, {})
    logger.info(f"Найдено {len(words)} анонимных слов для удаления")

    if not words:
        logger.info("Анонимных слов не найдено")
        return

    # Сначала удалить все highlights, ссылающиеся на эти слова
    for word in words:
        word_id = word['id']

        # Удалить highlights для этого слова
        delete_highlights_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM highlights
        WHERE word_id = $word_id
        """
        db._execute_query(delete_highlights_query, {'$word_id': word_id})

    logger.info(f"Удалены все highlights для {len(words)} слов")

    # Удалить примеры
    for word in words:
        word_id = word['id']

        delete_examples_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM dictionary_examples
        WHERE word_id = $word_id
        """
        db._execute_query(delete_examples_query, {'$word_id': word_id})

    logger.info(f"Удалены все примеры для {len(words)} слов")

    # Удалить переводы
    for word in words:
        word_id = word['id']

        delete_translations_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM dictionary_translations
        WHERE word_id = $word_id
        """
        db._execute_query(delete_translations_query, {'$word_id': word_id})

    logger.info(f"Удалены все переводы для {len(words)} слов")

    # Теперь удалить сами слова
    deleted_count = 0
    for word in words:
        word_id = word['id']
        lemma = word['lemma']

        try:
            delete_word_query = """
            DECLARE $word_id AS Uint64?;

            DELETE FROM dictionary_words
            WHERE id = $word_id
            """
            db._execute_query(delete_word_query, {'$word_id': word_id})
            deleted_count += 1
            logger.info(f"Удалено: {lemma} (id={word_id})")
        except Exception as e:
            logger.error(f"Ошибка при удалении '{lemma}': {e}")

    logger.info(f"✅ Удалено {deleted_count} из {len(words)} анонимных слов")


if __name__ == '__main__':
    delete_anonymous_words()
