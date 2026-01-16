#!/usr/bin/env python3
"""
Скрипт для удаления всех слов пользователя user_id=1
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_user_words(user_id: int):
    """Удалить все слова пользователя по user_id"""
    db = WordoorioDatabase()

    # Получить все слова пользователя
    get_words_query = """
    DECLARE $user_id AS Uint64?;

    SELECT id, lemma FROM dictionary_words
    WHERE user_id = $user_id
    """

    words = db._fetch_all(get_words_query, {'$user_id': user_id})
    logger.info(f"Найдено {len(words)} слов для user_id={user_id}")

    if not words:
        logger.info("Слов не найдено")
        return

    # Удаляем в правильном порядке: highlights -> examples -> translations -> words

    # 1. Удалить highlights
    deleted_highlights = 0
    for word in words:
        word_id = word['id']
        delete_highlights_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM highlights
        WHERE word_id = $word_id
        """
        db._execute_query(delete_highlights_query, {'$word_id': word_id})
        deleted_highlights += 1

    logger.info(f"✓ Удалены highlights для {deleted_highlights} слов")

    # 2. Удалить examples
    deleted_examples = 0
    for word in words:
        word_id = word['id']
        delete_examples_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM dictionary_examples
        WHERE word_id = $word_id
        """
        db._execute_query(delete_examples_query, {'$word_id': word_id})
        deleted_examples += 1

    logger.info(f"✓ Удалены examples для {deleted_examples} слов")

    # 3. Удалить translations
    deleted_translations = 0
    for word in words:
        word_id = word['id']
        delete_translations_query = """
        DECLARE $word_id AS Uint64?;

        DELETE FROM dictionary_translations
        WHERE word_id = $word_id
        """
        db._execute_query(delete_translations_query, {'$word_id': word_id})
        deleted_translations += 1

    logger.info(f"✓ Удалены translations для {deleted_translations} слов")

    # 4. Удалить сами слова
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
            if deleted_count % 10 == 0 or deleted_count == len(words):
                logger.info(f"Удалено {deleted_count}/{len(words)} слов...")
        except Exception as e:
            logger.error(f"Ошибка при удалении '{lemma}' (id={word_id}): {e}")

    logger.info(f"✅ Удалено {deleted_count} из {len(words)} слов пользователя user_id={user_id}")


if __name__ == '__main__':
    import sys
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    delete_user_words(user_id)
