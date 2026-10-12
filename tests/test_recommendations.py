from job_matcher import (
    analyze_roles,
    build_explanation,
    describe_wording_match,
    recommend_roles,
)
from skill_extractor import extract_skills
from text_cleaner import clean_text


def make_analysis(**overrides):
    """Build a small fake analysis for testing explanations."""
    analysis = {
        "role": "Test Role",
        "score": 50,
        "similarity": 0.40,
        "required_matched": ["Python"],
        "required_missing": ["SQL", "Docker"],
        "bonus_matched": [],
        "bonus_missing": ["Git"],
    }
    analysis.update(overrides)
    return analysis


def vision_analyses():
    text = clean_text(
        "Python OpenCV CNN YOLO PyTorch deep learning image processing NumPy"
    )
    return analyze_roles(text, extract_skills(text))


def test_default_returns_three_ranked_recommendations():
    recommendations = recommend_roles(vision_analyses())
    scores = [item["score"] for item in recommendations]
    assert [item["rank"] for item in recommendations] == [1, 2, 3]
    assert scores == sorted(scores, reverse=True)


def test_top_n_is_respected_and_safe_with_few_roles():
    assert len(recommend_roles(vision_analyses(), top_n=5)) == 5
    two_roles = [make_analysis(), make_analysis(role="Second Role")]
    assert len(recommend_roles(two_roles)) == 2


def test_explanation_lists_matched_and_missing_skills():
    lines = build_explanation(make_analysis())
    assert "1 of 3" in lines[0] and "Python" in lines[0]
    assert "SQL" in lines[1] and "Docker" in lines[1]


def test_explanation_when_nothing_matched():
    lines = build_explanation(make_analysis(required_matched=[]))
    assert "None of the 2 required" in lines[0]


def test_explanation_when_nothing_is_missing():
    lines = build_explanation(make_analysis(required_missing=[]))
    assert "No required skills are missing" in lines[1]


def test_long_gap_lists_are_shortened():
    missing = ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5", "Skill6"]
    lines = build_explanation(make_analysis(required_missing=missing))
    assert "Skill4" in lines[1]
    assert "Skill5" not in lines[1]
    assert "and more" in lines[1]


def test_wording_descriptions_follow_the_thresholds():
    assert "closely" in describe_wording_match(0.40)
    assert "partly" in describe_wording_match(0.20)
    assert "not very similar" in describe_wording_match(0.05)


def test_vision_resume_recommends_computer_vision_first():
    recommendations = recommend_roles(vision_analyses())
    assert recommendations[0]["role"] == "Computer Vision Engineer"
    assert any("OpenCV" in line for line in recommendations[0]["explanation"])


def test_recommendations_keep_the_scores_from_the_analysis():
    analyses = vision_analyses()
    for recommendation, analysis in zip(recommend_roles(analyses), analyses):
        assert recommendation["role"] == analysis["role"]
        assert recommendation["score"] == analysis["score"]