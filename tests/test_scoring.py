import pytest

from job_matcher import (
    BONUS_WEIGHT,
    REQUIRED_WEIGHT,
    TEXT_WEIGHT,
    analyze_roles,
    calculate_match_score,
    describe_score,
    load_job_roles,
    scale_similarity,
)
from skill_extractor import extract_skills
from text_cleaner import clean_text


def score_of(role_name, text, skills):
    analyses = analyze_roles(clean_text(text), skills)
    return next(item["score"] for item in analyses if item["role"] == role_name)


def test_weights_add_up_to_one():
    assert REQUIRED_WEIGHT + BONUS_WEIGHT + TEXT_WEIGHT == pytest.approx(1.0)


def test_worked_example_from_the_lesson():
    assert calculate_match_score(0.8, 0.25, 0.30) == 67


def test_perfect_resume_scores_100():
    assert calculate_match_score(1.0, 1.0, 0.9) == 100


def test_empty_resume_scores_zero():
    assert calculate_match_score(0.0, 0.0, 0.0) == 0


def test_similarity_is_scaled_and_capped():
    assert scale_similarity(0.25) == pytest.approx(0.5)
    assert scale_similarity(0.9) == 1.0
    assert scale_similarity(-0.1) == 0.0


def test_score_always_stays_between_0_and_100():
    for required in (0, 0.5, 1):
        for bonus in (0, 0.5, 1):
            for similarity in (0, 0.2, 0.5, 1):
                assert 0 <= calculate_match_score(required, bonus, similarity) <= 100


def test_score_labels():
    assert describe_score(80) == "Strong overlap"
    assert describe_score(60) == "Moderate overlap"
    assert describe_score(40) == "Limited overlap"
    assert describe_score(10) == "Little overlap so far"


def test_adding_a_required_skill_raises_the_score():
    text = "python sql"
    before = score_of("Data Analyst", text, ["Python"])
    after = score_of("Data Analyst", text, ["Python", "SQL"])
    assert after > before


def test_related_role_ranks_first():
    text = "Python OpenCV CNN YOLO PyTorch deep learning image processing NumPy"
    cleaned = clean_text(text)
    analyses = analyze_roles(cleaned, extract_skills(cleaned))
    assert analyses[0]["role"] == "Computer Vision Engineer"
    assert analyses[0]["score"] > analyses[1]["score"]


def test_matched_and_missing_skills_cover_every_listed_skill():
    cleaned = clean_text("python sql pandas docker")
    roles = {role["name"]: role for role in load_job_roles()}
    for item in analyze_roles(cleaned, extract_skills(cleaned)):
        role = roles[item["role"]]
        assert set(item["required_matched"]) | set(item["required_missing"]) == set(
            role["required_skills"]
        )
        assert set(item["bonus_matched"]) | set(item["bonus_missing"]) == set(
            role["bonus_skills"]
        )


def test_protected_attributes_do_not_change_the_score():
    base = "Python SQL Pandas Excel Power BI statistics"
    extra = (
        " Gender: female. Age: 25. Nationality: Indian. "
        "Marital status: married. Religion: Hindu."
    )
    skills = extract_skills(clean_text(base))
    assert score_of("Data Analyst", base, skills) == score_of(
        "Data Analyst", base + extra, skills
    )