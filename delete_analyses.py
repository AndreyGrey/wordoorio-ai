#!/usr/bin/env python3
"""
Скрипт для удаления всех analyses
"""

from database import WordoorioDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_all_analyses():
    """Удалить все analyses"""
    db = WordoorioDatabase()

    # Получить все analyses
    get_analyses_query = """
    SELECT id FROM analyses
    """

    analyses = db._fetch_all(get_analyses_query, {})
    logger.info(f"Найдено {len(analyses)} analyses для удаления")

    if not analyses:
        logger.info("Analyses не найдены")
        return

    # Удалить каждый analysis
    deleted_count = 0
    for analysis in analyses:
        analysis_id = analysis['id']

        try:
            delete_query = """
            DECLARE $analysis_id AS Uint64?;

            DELETE FROM analyses
            WHERE id = $analysis_id
            """
            db._execute_query(delete_query, {'$analysis_id': analysis_id})
            deleted_count += 1
            logger.info(f"Удален analysis id={analysis_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении analysis {analysis_id}: {e}")

    logger.info(f"✅ Удалено {deleted_count} из {len(analyses)} analyses")


if __name__ == '__main__':
    delete_all_analyses()
