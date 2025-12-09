#!/usr/bin/env python3
"""
🔤 Лемматизатор
Преобразует слова и фразы в словарную форму (английский и русский)
"""

import spacy
import pymorphy2

# Загружаем модели один раз при импорте
_nlp = None
_morph = None

def _get_nlp():
    """Ленивая загрузка английской модели"""
    global _nlp
    if _nlp is None:
        print("📚 Загружаем spaCy модель для английского...", flush=True)
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        print("✅ Модель загружена", flush=True)
    return _nlp

def _get_morph():
    """Ленивая загрузка русского морфоанализатора"""
    global _morph
    if _morph is None:
        print("📚 Загружаем pymorphy2 для русского...", flush=True)
        _morph = pymorphy2.MorphAnalyzer()
        print("✅ Морфоанализатор загружен", flush=True)
    return _morph


def lemmatize(text: str) -> str:
    """
    Преобразует слово или фразу в словарную форму

    Примеры:
        - "incentives" → "incentive"
        - "running" → "run"
        - "went" → "go"
        - "gave up" → "give up"
        - "making sense" → "make sense"

    Args:
        text: Слово или фраза для лемматизации

    Returns:
        Лемматизированный текст
    """
    if not text or not text.strip():
        return text

    nlp = _get_nlp()
    doc = nlp(text.strip())

    # Лемматизируем каждое слово
    lemmas = [token.lemma_ for token in doc]

    return " ".join(lemmas)


def lemmatize_batch(texts: list[str]) -> list[str]:
    """
    Лемматизирует список текстов (более эффективно чем по одному)

    Args:
        texts: Список слов или фраз

    Returns:
        Список лемматизированных текстов
    """
    if not texts:
        return []

    nlp = _get_nlp()

    # Обрабатываем все тексты за один проход
    results = []
    for doc in nlp.pipe(texts):
        lemmas = [token.lemma_ for token in doc]
        results.append(" ".join(lemmas))

    return results


def lemmatize_russian(text: str) -> str:
    """
    Лемматизирует русский текст (слово или фразу)

    Примеры:
        - "стимулы" → "стимул"
        - "бегущий" → "бежать"
        - "управление бизнесом" → "управление бизнес"

    Args:
        text: Русское слово или фраза

    Returns:
        Лемматизированный текст
    """
    if not text or not text.strip():
        return text

    morph = _get_morph()

    # Разбиваем на слова
    words = text.strip().split()
    lemmas = []

    for word in words:
        # Парсим слово и берем первый (наиболее вероятный) вариант
        parsed = morph.parse(word)
        if parsed:
            lemma = parsed[0].normal_form
            lemmas.append(lemma)
        else:
            # Если не удалось распарсить, оставляем как есть
            lemmas.append(word)

    return " ".join(lemmas)


# Тесты для проверки
if __name__ == "__main__":
    print("🧪 Тестируем лемматизатор...\n")

    print("📝 Английский:")
    english_tests = [
        "incentives",
        "running",
        "went",
        "bigger",
        "stories",
        "gave up",
        "making sense",
        "came across",
        "compelling arguments",
    ]

    for test in english_tests:
        result = lemmatize(test)
        print(f"  '{test}' → '{result}'")

    print("\n📝 Русский:")
    russian_tests = [
        "стимулы",
        "стимулирующий",
        "управление бизнесом",
        "бегущий",
        "сдались",
    ]

    for test in russian_tests:
        result = lemmatize_russian(test)
        print(f"  '{test}' → '{result}'")

    print("\n✅ Тесты завершены")
