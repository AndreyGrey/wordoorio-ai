#!/usr/bin/env python3
"""
Scraper Service
Извлечение текста из веб-страниц

@version 1.0.0
"""

import logging
from typing import Optional
from dataclasses import dataclass

import trafilatura

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Результат скрейпинга"""
    text: str
    title: str
    url: str


class ScraperService:
    """Сервис для извлечения текста из веб-страниц"""

    MAX_TEXT_LENGTH = 15000

    def scrape_url(self, url: str) -> ScrapedContent:
        """
        Извлечь текст статьи по URL

        Args:
            url: URL страницы

        Returns:
            ScrapedContent с текстом и заголовком

        Raises:
            ValueError: Если URL пустой или не удалось извлечь контент
        """
        url = url.strip()

        if not url:
            raise ValueError('URL не указан')

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Загружаем страницу
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError('Не удалось загрузить страницу')

        # Извлекаем текст
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError('Не удалось извлечь текст из страницы')

        # Извлекаем метаданные (заголовок)
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else ''

        # Ограничиваем длину текста
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]

        logger.info(f"[Scrape] URL: {url}, title: {title}, длина текста: {len(text)}")

        return ScrapedContent(text=text, title=title, url=url)
