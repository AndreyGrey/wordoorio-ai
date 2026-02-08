#!/usr/bin/env python3
"""
Лемматизатор для английского и русского языков

- Английский: spaCy (en_core_web_sm)
- Русский: pymorphy2
"""

import spacy

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


def lemmatize_with_pos(text: str) -> tuple:
    """
    Преобразует слово или фразу в словарную форму + возвращает флаг причастия.

    Используется для согласования EN ↔ RU: если EN = причастие,
    то RU перевод тоже не нужно лемматизировать.

    Args:
        text: Слово или фраза для лемматизации

    Returns:
        tuple: (лемматизированный текст, is_participle)
            - is_participle = True если первое слово — причастие (VBN/VBG)
    """
    if not text or not text.strip():
        return text, False

    nlp = _get_nlp()
    doc = nlp(text.strip())

    lemmas = []
    is_participle = False

    for i, token in enumerate(doc):
        if token.tag_ in ('VBN', 'VBG'):
            # VBN = past participle (embroiled, broken, written)
            # VBG = gerund/present participle (amplifying, running)
            lemmas.append(token.text.lower())
            if i == 0:  # Первое слово — определяет тип всего highlight
                is_participle = True
        else:
            lemmas.append(token.lemma_)

    return " ".join(lemmas), is_participle


def lemmatize(text: str) -> str:
    """
    Преобразует слово или фразу в словарную форму

    Примеры:
        - "incentives" → "incentive"
        - "went" → "go"
        - "gave up" → "give up"
        - "embroiled" → "embroiled" (причастие — не трогаем)
        - "amplifying" → "amplifying" (герундий — не трогаем)

    Args:
        text: Слово или фраза для лемматизации

    Returns:
        Лемматизированный текст
    """
    lemma, _ = lemmatize_with_pos(text)
    return lemma


def _get_morph():
    """Ленивая загрузка pymorphy2 для русского языка"""
    global _morph
    if _morph is None:
        import pymorphy2
        print("📚 Загружаем pymorphy2 для русского...", flush=True)
        _morph = pymorphy2.MorphAnalyzer()
        print("✅ pymorphy2 загружен", flush=True)
    return _morph


def lemmatize_russian(text: str) -> str:
    """
    Нормализует русский текст в словарную форму.

    Для одиночных слов:
    - Глаголы → инфинитив (normal_form)
    - Прилагательные/причастия → м.р. ед.ч. им.п. (inflect, НЕ normal_form!)
    - Существительные → ед.ч. им.п.

    Для фраз:
    - НЕ трогаем — оставляем как есть от AI-агента
    - Промпт v2.0 уже просит словарную форму
    - AI лучше справляется с согласованием внутри фразы

    Примеры:
    - "захватывающие" → "захватывающий" (причастие → м.р. ед.ч.)
    - "нарушающая" → "нарушающий" (причастие → м.р. ед.ч., НЕ "нарушать"!)
    - "адаптировались" → "адаптироваться" (глагол → инфинитив)
    - "закрытая экосистема" → "закрытая экосистема" (фраза — не трогаем)

    Args:
        text: Слово или фраза на русском

    Returns:
        Нормализованный текст
    """
    if not text or not text.strip():
        return text

    morph = _get_morph()
    words = text.strip().split()

    if len(words) == 1:
        # Одиночное слово — нормализация с учётом части речи
        parsed = morph.parse(words[0])[0]
        pos = parsed.tag.POS

        if pos == 'VERB' or pos == 'INFN':
            # Глагол → инфинитив
            return parsed.normal_form
        elif pos in ('ADJF', 'ADJS', 'PRTF', 'PRTS'):
            # Прилагательное или причастие → м.р. ед.ч. им.п.
            # ВАЖНО: НЕ normal_form, иначе причастие станет глаголом!
            inflected = parsed.inflect({'masc', 'sing', 'nomn'})
            if inflected:
                return inflected.word
            # Fallback если inflect не сработал
            return parsed.normal_form
        elif pos == 'NOUN':
            # Существительное → ед.ч. им.п.
            inflected = parsed.inflect({'sing', 'nomn'})
            if inflected:
                return inflected.word
            return parsed.normal_form
        else:
            # Остальные части речи — normal_form
            return parsed.normal_form
    else:
        # Фраза (2+ слов) — НЕ трогаем, оставляем как есть
        # AI-агент с промптом v2.0 уже возвращает словарную форму
        # и лучше справляется с согласованием внутри фразы
        return text.strip()


# Тесты для проверки
if __name__ == "__main__":
    print("🧪 Тестируем лемматизатор...\n")

    print("=== Английский (spaCy) — lemmatize_with_pos() ===")
    english_tests = [
        # (вход, ожидаемая_лемма, ожидаемый_is_participle)
        # Обычные слова → лемматизируются, is_participle=False
        ("incentives", "incentive", False),
        ("went", "go", False),
        ("bigger", "big", False),
        ("stories", "story", False),
        # Причастия (VBN, VBG) → НЕ лемматизируются, is_participle=True
        ("embroiled", "embroiled", True),   # VBN
        ("amplifying", "amplifying", True),  # VBG
        ("running", "running", True),        # VBG
        ("broken", "broken", True),          # VBN
        ("peppered", "peppered", True),      # VBN
        # Фразы — is_participle по первому слову
        ("gave up", "give up", False),       # gave=VBD, не причастие
        ("came across", "come across", False),
        ("peppered with", "peppered with", True),  # peppered=VBN
    ]

    for test, expected_lemma, expected_participle in english_tests:
        lemma, is_part = lemmatize_with_pos(test)
        lemma_ok = lemma == expected_lemma
        part_ok = is_part == expected_participle
        if lemma_ok and part_ok:
            status = "✓"
        else:
            status = f"✗ (лемма: '{lemma}', participle: {is_part})"
        print(f"  '{test}' → '{lemma}' [participle={is_part}] {status}")

    print("\n=== Русский (pymorphy2) ===")
    russian_tests = [
        # Причастия/прилагательные → м.р. ед.ч. (НЕ инфинитив!)
        ("захватывающие", "захватывающий"),
        ("нарушающая", "нарушающий"),  # НЕ "нарушать"!
        ("поддельные", "поддельный"),
        ("поддельная", "поддельный"),
        ("сосредоточённое", "сосредоточённый"),
        # Глаголы → инфинитив
        ("адаптировались", "адаптироваться"),
        ("касается", "касаться"),
        ("появился", "появиться"),
        # Фразы → не трогаем (AI уже вернул правильную форму)
        ("закрытая экосистема", "закрытая экосистема"),
        ("засыпали вопросами", "засыпали вопросами"),
        ("втянут в конфликт", "втянут в конфликт"),
    ]

    for test, expected in russian_tests:
        result = lemmatize_russian(test)
        status = "✓" if result == expected else f"✗ (ожидалось '{expected}')"
        print(f"  '{test}' → '{result}' {status}")

    print("\n✅ Тесты завершены")
