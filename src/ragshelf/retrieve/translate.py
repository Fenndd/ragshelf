"""Translate a query to English before retrieval, keeping the original.

Language detection and translation are one `ChatClient` call that answers in a
strict two-line format (see `ragshelf.prompts.query_translation`). Any reply that
does not fit the format, or fails the sanity checks below, raises
`TranslationError`; the original query is never used as a silent fallback.

One deliberate exception: a short query (at most 3 words) without Cyrillic that
the model "translates" to itself (a place name, `Python`) is a legitimate no-op.
It is returned with `translated=False` and the model's language label. Longer
queries and any query with Cyrillic that come back unchanged still raise.

Limitations: a Latin-script non-English query (Slovak without diacritics,
transliterated Russian) that the model labels `en` passes through untranslated;
only a mostly Cyrillic query is caught by a sanity check.
"""

import re
from dataclasses import dataclass

from ragshelf.llm.base import ChatClient, LLMError, Route
from ragshelf.prompts.query_translation import PROMPT_VERSION, build_messages

# Deterministic decoding; the reply is two short lines.
TEMPERATURE = 0.0
MAX_TOKENS = 512

# A translation far longer than its query is commentary, not a translation.
MAX_LENGTH_FACTOR = 4
MAX_LENGTH_SLACK = 100

# Exactly a two-letter ISO 639-1 code. A region suffix (`en-US`, `ru-RU`) is
# tolerated and dropped; three-letter codes (`rus`) and words are rejected.
_LANGUAGE_LINE = re.compile(r"language:\s*([A-Za-z]{2})(?:-[A-Za-z0-9]{2,8})?", re.IGNORECASE)
_TRANSLATION_PREFIX = re.compile(r"translation:\s*", re.IGNORECASE)
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")

# Wrapper pairs models put around a translation despite the prompt; longest first.
_WRAPPERS = (
    ("**", "**"),
    ("__", "__"),
    ('"', '"'),
    ("'", "'"),
    ("\u201C", "\u201D"),
    ("\u00AB", "\u00BB"),
    ("`", "`"),
    ("*", "*"),
    ("_", "_"),
)
# Quote characters form one family: translating guillemets or typographic quotes
# to straight quotes (or the reverse) is correct, so a quote at the edge of a
# translation is stray only when the query contains no quote character at all.
_QUOTES = frozenset("\"\u201C\u201D\u201E\u00AB\u00BB")
# Other markup must not start or end a translation unless the query has it too.
_MARKUP_CHARS = frozenset("`*_")

# A translation identical to the query is accepted as a no-op only for a short query.
NOOP_MAX_WORDS = 3


class TranslationError(LLMError):
    """The query could not be translated. Also an `LLMError`, so callers may catch either."""


@dataclass(frozen=True)
class TranslatedQuery:
    """A query in both forms. Retrieval uses `english`; the answer language and the trace use `original`."""

    original: str
    english: str
    # Lowercase two-letter ISO 639-1 code reported by the model ("ru", "sk", "en", ...).
    # A region suffix in the reply ("ru-RU") is dropped; other forms raise `TranslationError`.
    language: str
    # False when the query was English and `english` is the original, unchanged.
    translated: bool
    prompt_version: str
    # Which model and route answered, for the trace.
    model: str
    route: Route


def translate_query(query: str, client: ChatClient) -> TranslatedQuery:
    """Detect the language of `query` and return it with its English form.

    English queries come back unchanged. Raises `TranslationError` for a blank
    query, a failed request, a cut-off or malformed reply, or a reply that is
    not plausibly a translation.
    """
    if not query.strip():
        raise TranslationError("the query is empty")

    try:
        completion = client.complete(
            build_messages(query), max_tokens=MAX_TOKENS, temperature=TEMPERATURE
        )
    except LLMError as error:
        raise TranslationError(f"the translation request failed: {error}") from error

    # Real clients pass the provider's value through: "stop" (or none) is a normal end.
    if completion.finish_reason == "length":
        raise TranslationError("the translation reply was cut off at max_tokens")
    if completion.finish_reason not in (None, "stop"):
        raise TranslationError(
            f"the translation reply ended abnormally (finish_reason {completion.finish_reason!r})"
        )

    language, translation = _parse_reply(completion.text)

    if language == "en":
        if _mostly_cyrillic(query):
            raise TranslationError("the model reported English for a mostly Cyrillic query")
        return TranslatedQuery(
            query, query.strip(), "en", False, PROMPT_VERSION, completion.model, completion.route
        )

    if translation is None:
        raise TranslationError(f"no translation for a {language!r} query")
    translation = _unwrap(query, translation)
    if _check_translation(query, translation):
        # A short Latin-script query that needs no translation (a place name).
        return TranslatedQuery(
            query, query.strip(), language, False, PROMPT_VERSION, completion.model, completion.route
        )
    return TranslatedQuery(
        query, translation, language, True, PROMPT_VERSION, completion.model, completion.route
    )


def _parse_reply(text: str) -> tuple[str, str | None]:
    """Return (language, translation or None) from the strict reply format."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or len(lines) > 2:
        raise TranslationError(f"the reply is not in the two-line format: {_preview(text)}")

    match = _LANGUAGE_LINE.fullmatch(lines[0])
    if match is None:
        raise TranslationError(f"the reply has no language line: {_preview(text)}")
    language = match.group(1).lower()

    translation: str | None = None
    if len(lines) == 2:
        prefix = _TRANSLATION_PREFIX.match(lines[1])
        if prefix is None:
            raise TranslationError(f"the reply has no translation line: {_preview(text)}")
        translation = lines[1][prefix.end():].strip()
    if language != "en" and not translation:
        raise TranslationError(f"the translation is empty: {_preview(text)}")
    return language, translation


def _unwrap(query: str, translation: str) -> str:
    """Strip symmetric quote or emphasis wrappers the model added around the translation.

    A wrapper the query itself starts with is kept (any quote character counts
    for any quote wrapper, see `_QUOTES`). A wrapper is stripped only
    when it encloses the whole text: if the inner text contains the opener or
    closer again (two separately quoted phrases, `_x and _y_`), the text is left
    alone so the caller's stray-edge check rejects it instead of mangling it.
    Wrappers that are not symmetric, or a repeated `translation:` label, are
    rejected by the caller.
    """
    stripped = translation
    changed = True
    while changed:
        changed = False
        for opener, closer in _WRAPPERS:
            if (
                len(stripped) > len(opener) + len(closer)
                and stripped.startswith(opener)
                and stripped.endswith(closer)
                and not _query_starts_with(query, opener)
            ):
                inner = stripped[len(opener) : len(stripped) - len(closer)]
                if opener in inner or closer in inner:
                    continue
                stripped = inner.strip()
                changed = True
    return stripped


def _query_starts_with(query: str, opener: str) -> bool:
    start = query.lstrip()
    if opener[0] in _QUOTES:
        return start[:1] in _QUOTES
    return start.startswith(opener)


def _mostly_cyrillic(text: str) -> bool:
    """True when Cyrillic letters are the majority of the letters in `text`."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    return sum(1 for char in letters if _CYRILLIC.match(char)) / len(letters) > 0.5


def _comparable(text: str) -> str:
    """Case, spacing and punctuation-insensitive form, to detect an echoed query."""
    return "".join(char for char in text.casefold() if char.isalnum())


def _check_translation(query: str, translation: str) -> bool:
    """Raise `TranslationError` unless `translation` is plausible.

    Returns True for the accepted no-op (see the module docstring), else False.
    """
    if not translation:
        raise TranslationError("the translation is empty after removing quotes")
    if _TRANSLATION_PREFIX.match(translation):
        raise TranslationError("the translation repeats the 'translation:' label")
    query_has_quotes = any(char in _QUOTES for char in query)
    for edge in (translation[0], translation[-1]):
        if (edge in _QUOTES and not query_has_quotes) or (
            edge in _MARKUP_CHARS and edge not in query
        ):
            raise TranslationError("the translation has stray quote or markup characters")
    if _comparable(translation) == _comparable(query):
        if len(query.split()) <= NOOP_MAX_WORDS and _CYRILLIC.search(query) is None:
            return True
        raise TranslationError("the translation is the query unchanged, so it was not translated")
    if len(translation) > len(query) * MAX_LENGTH_FACTOR + MAX_LENGTH_SLACK:
        raise TranslationError("the translation is far longer than the query")
    if not any(char.isalpha() for char in translation):
        raise TranslationError("the translation has no letters")
    if _mostly_cyrillic(translation):
        raise TranslationError("the translation is mostly Cyrillic, so it was not translated")
    return False


def _preview(text: str, limit: int = 80) -> str:
    flat = " ".join(text.split())
    return repr(flat if len(flat) <= limit else flat[:limit] + "...")
