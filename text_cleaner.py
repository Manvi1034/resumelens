"""Text cleaning: turn raw resume text into normalized text for matching.

Punctuation is removed only from the edges of words, so technical terms such
as C++, C#, .NET, Node.js, CI/CD and scikit-learn survive cleaning.
"""

import re
import unicodedata

EMAIL_PATTERN = re.compile(r"\S+@\S+\.\S+")
URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")

# Symbols removed only from the START or END of a word, never from inside it.
# Note that "+" and "#" are NOT in this list, so C++ and C# keep their symbols.
EDGE_PUNCTUATION = ",;:()[]{}\"'!?*|<>=~`^\\_&/@-"
TRAILING_PUNCTUATION = EDGE_PUNCTUATION + "."

# Replace fancy characters with plain ones. Bullets become spaces.
CHARACTER_REPLACEMENTS = str.maketrans(
    {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u2018": "'",  # curly quotes
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": " ",  # bullet
        "\u2023": " ",
        "\u25cf": " ",
        "\u25aa": " ",
        "\u25a0": " ",
        "\u25e6": " ",
        "\uf0b7": " ",  # bullet used by Word-generated PDFs
    }
)


def _remove_phone_number(match):
    """Remove a match only if it has at least 10 digits.

    The digit check stops date ranges like '2021 - 2025' from being removed.
    """
    digits = re.sub(r"\D", "", match.group())
    return " " if len(digits) >= 10 else match.group()


def _clean_token(token):
    """Strip punctuation from the edges of one word, keeping inner symbols."""
    token = token.rstrip(TRAILING_PUNCTUATION)
    token = token.lstrip(EDGE_PUNCTUATION)
    # Keep a leading dot only when a letter follows it (".net").
    if token.startswith(".") and not re.match(r"\.[a-z]", token):
        token = token.lstrip(".")
    return token


def clean_text(text):
    """Return lowercase, single-spaced text with technical terms preserved."""
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.translate(CHARACTER_REPLACEMENTS)

    # Personal details are not job-related, so remove them before analysis.
    text = EMAIL_PATTERN.sub(" ", text)
    text = URL_PATTERN.sub(" ", text)
    text = PHONE_PATTERN.sub(_remove_phone_number, text)

    text = text.lower()
    tokens = (_clean_token(token) for token in text.split())

    # Drop tokens with no letters or digits (stray symbols like "-" or "|").
    return " ".join(
        token for token in tokens if any(char.isalnum() for char in token)
    )