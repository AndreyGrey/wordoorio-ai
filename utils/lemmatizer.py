#!/usr/bin/env python3
"""
Лемматизатор для английского языка (spaCy)
"""

import spacy

# Загружаем модель один раз при импорте
_nlp = None


def _get_nlp():
    """Ленивая загрузка английской модели"""
    global _nlp
    if _nlp is None:
        print("📚 Загружаем spaCy модель для английского...", flush=True)
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        print("✅ Модель загружена", flush=True)
    return _nlp


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


# Тесты для проверки
if __name__ == "__main__":
    print("🧪 Тестируем лемматизатор...\n")

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
        "amplifying",
    ]

    for test in english_tests:
        result = lemmatize(test)
        print(f"  '{test}' → '{result}'")

    print("\n✅ Тесты завершены")
