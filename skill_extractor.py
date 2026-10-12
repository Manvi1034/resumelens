"""Skill extraction: find dictionary skills in cleaned resume text.

Skills are matched with boundary-aware regular expressions, so "java" is not
found inside "javascript" and "c++" is found even in "c/c++".
"""

import re
from pathlib import Path

import pandas as pd

SKILL_DICTIONARY_PATH = (
    Path(__file__).resolve().parent / "data" / "skill_dictionary.csv"
)


def split_pipe(value):
    """Turn 'a|b|c' into ['a', 'b', 'c']. Blank cells give an empty list."""
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def _term_regex(term):
    """Regex for one skill name. A space or a hyphen between its words both match,
    so "machine learning" is also found as "machine-learning"."""
    words = [word for word in re.split(r"[ \-]+", term) if word]
    return r"[ \-]".join(re.escape(word) for word in words)


def build_pattern(terms):
    """Build one regex that matches any of the given names or aliases.

    A match must not touch a letter, digit, '+' or '#' on either side.
    """
    cleaned_terms = sorted(
        {term.lower().strip() for term in terms if term.strip()},
        key=len,
        reverse=True,
    )
    alternatives = "|".join(_term_regex(term) for term in cleaned_terms)
    return re.compile(rf"(?<![a-z0-9+#])(?:{alternatives})(?![a-z0-9+#])")


def load_skill_dictionary(csv_path=SKILL_DICTIONARY_PATH):
    """Read the CSV and return a list of skills, each with a compiled pattern."""
    table = pd.read_csv(csv_path)
    dictionary = []
    for _, row in table.iterrows():
        names = [row["skill"]] + split_pipe(row["aliases"])
        dictionary.append(
            {
                "name": row["skill"],
                "category": row["category"],
                "pattern": build_pattern(names),
            }
        )
    return dictionary


def extract_skills(cleaned_text, dictionary=None):
    """Return the official names of all skills found, in dictionary order.

    Expects text that has already been through clean_text().
    """
    if not cleaned_text:
        return []
    if dictionary is None:
        dictionary = load_skill_dictionary()
    return [
        entry["name"] for entry in dictionary if entry["pattern"].search(cleaned_text)
    ]


def group_by_category(skill_names, dictionary=None):
    """Group skill names by category, e.g. {'Programming': ['Python', 'C++']}."""
    if dictionary is None:
        dictionary = load_skill_dictionary()
    category_of = {entry["name"]: entry["category"] for entry in dictionary}

    grouped = {}
    for name in skill_names:
        grouped.setdefault(category_of[name], []).append(name)
    return grouped