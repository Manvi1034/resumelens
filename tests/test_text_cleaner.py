from text_cleaner import clean_text


def test_text_is_lowercased():
    assert clean_text("Python AND SQL") == "python and sql"


def test_protected_technical_terms_survive():
    text = clean_text(
        "Skills: C++, C#, .NET, Node.js, ASP.NET, CI/CD and scikit-learn."
    )
    tokens = text.split()
    for term in ["c++", "c#", ".net", "node.js", "asp.net", "ci/cd", "scikit-learn"]:
        assert term in tokens


def test_surrounding_punctuation_is_removed():
    assert clean_text("(Python), 'SQL'; \"Pandas\"!") == "python sql pandas"


def test_extra_whitespace_is_collapsed():
    assert clean_text("python\n\n  sql\t\tpandas   ") == "python sql pandas"


def test_bullet_symbols_are_removed():
    assert clean_text("\u2022 Python\n\uf0b7 SQL\n\u25cf Pandas") == "python sql pandas"


def test_email_phone_and_url_are_removed():
    text = clean_text(
        "jane.doe@example.com +91 98765 43210 https://github.com/janedoe Python"
    )
    assert text == "python"


def test_date_ranges_are_not_mistaken_for_phone_numbers():
    tokens = clean_text("B.Tech 2021 - 2025, CGPA 8.5").split()
    assert "2021" in tokens and "2025" in tokens and "8.5" in tokens


def test_unicode_ligatures_and_dashes_are_normalized():
    assert clean_text("\ufb01ne\u2013tuned NLP \u2014 Python") == "fine-tuned nlp python"


def test_empty_input_returns_empty_string():
    assert clean_text("") == ""
    assert clean_text(None) == ""