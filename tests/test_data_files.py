from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data():
    """Load both CSV files and return them as two DataFrames."""
    skills = pd.read_csv(DATA_DIR / "skill_dictionary.csv")
    roles = pd.read_csv(DATA_DIR / "job_roles.csv")
    return skills, roles


def split_pipe(value):
    """Turn 'Python|SQL' into ['Python', 'SQL']. Blank cells give an empty list."""
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def test_required_columns_exist():
    skills, roles = load_data()
    assert {"skill", "category", "aliases"} <= set(skills.columns)
    assert {"role", "description", "required_skills", "bonus_skills"} <= set(roles.columns)


def test_skill_dictionary_has_enough_skills():
    skills, _ = load_data()
    assert len(skills) >= 30


def test_skill_names_are_unique():
    skills, _ = load_data()
    assert skills["skill"].is_unique


def test_at_least_five_roles():
    _, roles = load_data()
    assert len(roles) >= 5


def test_role_skills_exist_in_dictionary():
    skills, roles = load_data()
    known_skills = set(skills["skill"])
    for _, row in roles.iterrows():
        listed = split_pipe(row["required_skills"]) + split_pipe(row["bonus_skills"])
        unknown = [skill for skill in listed if skill not in known_skills]
        assert not unknown, f"{row['role']} has unknown skills: {unknown}"