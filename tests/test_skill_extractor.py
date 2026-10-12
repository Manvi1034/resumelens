from skill_extractor import extract_skills, group_by_category, load_skill_dictionary
from text_cleaner import clean_text


def skills_in(raw_text):
    """Clean the text the same way the app does, then extract skills."""
    return extract_skills(clean_text(raw_text))


def test_basic_skills_are_found():
    skills = skills_in("Python, SQL and Pandas projects")
    assert {"Python", "SQL", "Pandas"} <= set(skills)


def test_symbol_skills_are_found():
    skills = skills_in("Skills: C++, C#, .NET, Node.js.")
    assert {"C++", "C#", "Node.js"} <= set(skills)


def test_slash_separated_skills_are_found():
    skills = skills_in("Experienced in C/C++ and Java/JavaScript.")
    assert {"C++", "Java", "JavaScript"} <= set(skills)


def test_partial_word_matches_are_rejected():
    skills = skills_in("JavaScript developer using MySQL and GitHub")
    assert {"JavaScript", "MySQL", "GitHub"} <= set(skills)
    assert "Java" not in skills
    assert "SQL" not in skills
    assert "Git" not in skills


def test_aliases_map_to_official_names():
    skills = skills_in("sklearn, postgres, k8s, natural language processing, powerbi")
    assert {"scikit-learn", "PostgreSQL", "Kubernetes", "NLP", "Power BI"} <= set(skills)


def test_multi_word_skills_are_found():
    skills = skills_in("Experience with machine learning and REST APIs")
    assert {"Machine Learning", "REST API"} <= set(skills)


def test_each_skill_is_reported_once():
    skills = skills_in("python Python PYTHON python3")
    assert skills.count("Python") == 1


def test_link_without_http_still_counts():
    assert "GitHub" in skills_in("Portfolio: github.com/janedoe")


def test_empty_text_returns_no_skills():
    assert extract_skills("") == []


def test_skills_are_grouped_by_category():
    grouped = group_by_category(["Python", "SQL", "Pandas"], load_skill_dictionary())
    assert grouped == {
        "Programming": ["Python"],
        "Databases": ["SQL"],
        "Data Analytics": ["Pandas"],
    }