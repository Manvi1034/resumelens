import pytest

from job_matcher import get_role, load_job_roles
from skill_extractor import load_skill_dictionary

MANDATORY_ROLES = {
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "NLP Engineer",
    "Computer Vision Engineer",
}


def test_mandatory_roles_are_present():
    names = {role["name"] for role in load_job_roles()}
    assert MANDATORY_ROLES <= names


def test_role_names_are_unique():
    names = [role["name"] for role in load_job_roles()]
    assert len(names) == len(set(names))


def test_every_role_has_description_and_enough_required_skills():
    for role in load_job_roles():
        assert len(role["description"].split()) >= 10, role["name"]
        assert len(role["required_skills"]) >= 5, role["name"]


def test_skills_are_not_repeated_within_a_role():
    for role in load_job_roles():
        listed = role["required_skills"] + role["bonus_skills"]
        assert len(listed) == len(set(listed)), f"duplicate skill in {role['name']}"


def test_all_role_skills_exist_in_the_skill_dictionary():
    known = {entry["name"] for entry in load_skill_dictionary()}
    for role in load_job_roles():
        for skill in role["required_skills"] + role["bonus_skills"]:
            assert skill in known, f"{role['name']}: unknown skill {skill}"


def test_get_role_returns_the_matching_role():
    assert get_role("Data Analyst")["name"] == "Data Analyst"


def test_get_role_rejects_unknown_names():
    with pytest.raises(ValueError):
        get_role("Astronaut")