from job_matcher import analyze_roles, load_job_roles
from roadmap_generator import (
    MAX_ROADMAP_ITEMS,
    build_roadmap,
    load_learning_resources,
)
from skill_extractor import extract_skills, load_skill_dictionary
from text_cleaner import clean_text


def make_analysis(required_missing=(), bonus_missing=()):
    """A small fake role analysis containing only the fields the roadmap uses."""
    return {
        "role": "Test Role",
        "required_missing": list(required_missing),
        "bonus_missing": list(bonus_missing),
    }


def test_every_role_skill_has_learning_resources():
    resources = load_learning_resources()
    for role in load_job_roles():
        for skill in role["required_skills"] + role["bonus_skills"]:
            assert skill in resources, f"No learning info for {skill} ({role['name']})"


def test_learning_skills_exist_in_the_skill_dictionary():
    known = {entry["name"] for entry in load_skill_dictionary()}
    for skill in load_learning_resources():
        assert skill in known, f"{skill} is not in skill_dictionary.csv"


def test_resource_values_are_sensible():
    for skill, info in load_learning_resources().items():
        assert 1 <= info["stage"] <= 5, skill
        assert 1 <= info["weeks"] <= 3, skill
        assert len(info["topics"]) >= 3, skill
        assert info["project"], skill


def test_skills_are_ordered_by_stage():
    roadmap = build_roadmap(make_analysis(["Docker", "Python", "SQL"]))
    assert [item["skill"] for item in roadmap["items"]] == ["Python", "SQL", "Docker"]


def test_required_skills_come_before_bonus_skills():
    roadmap = build_roadmap(make_analysis(["Docker"], ["Python", "SQL"]))
    assert [item["priority"] for item in roadmap["items"]] == [
        "Required",
        "Bonus",
        "Bonus",
    ]
    assert roadmap["items"][0]["skill"] == "Docker"


def test_weeks_are_consecutive_and_total_is_correct():
    roadmap = build_roadmap(make_analysis(["Git", "Machine Learning", "scikit-learn"]))
    items = roadmap["items"]
    assert items[0]["start_week"] == 1
    for previous, current in zip(items, items[1:]):
        assert current["start_week"] == previous["end_week"] + 1
    assert roadmap["total_weeks"] == items[-1]["end_week"] == 6


def test_roadmap_is_capped_and_reports_remaining_skills():
    required = [
        "Python", "SQL", "Excel", "Pandas",
        "Power BI", "Data Visualization", "Statistics", "Tableau",
    ]
    roadmap = build_roadmap(make_analysis(required))
    assert len(roadmap["items"]) == MAX_ROADMAP_ITEMS
    assert set(roadmap["remaining"]) == {"Data Visualization", "Tableau"}


def test_bonus_skills_fill_a_short_roadmap():
    bonus = ["MongoDB", "AWS", "Kubernetes", "MLflow", "Tableau"]
    roadmap = build_roadmap(make_analysis(["Docker"], bonus))
    assert len(roadmap["items"]) == 3
    assert len(roadmap["remaining"]) == 3


def test_no_missing_skills_gives_an_empty_roadmap():
    roadmap = build_roadmap(make_analysis())
    assert roadmap["items"] == []
    assert roadmap["weekly_plan"] == []
    assert roadmap["total_weeks"] == 0
    assert roadmap["remaining"] == []


def test_unknown_skill_gets_a_generic_plan():
    roadmap = build_roadmap(make_analysis(["Cobol"]))
    item = roadmap["items"][0]
    assert item["weeks"] == 1
    assert "Cobol" in item["project"]


def test_weekly_plan_has_one_row_per_week_and_ends_with_the_project():
    roadmap = build_roadmap(make_analysis(["Git", "Machine Learning"]))
    weekly = roadmap["weekly_plan"]
    assert [row["week"] for row in weekly] == list(range(1, roadmap["total_weeks"] + 1))
    for item in roadmap["items"]:
        last_week_row = weekly[item["end_week"] - 1]
        assert "Practice project" in last_week_row["focus"]
        assert last_week_row["skill"] == item["skill"]


def test_roadmap_from_a_real_analysis():
    text = clean_text("python pandas numpy")
    analyses = analyze_roles(text, extract_skills(text))
    ml_engineer = next(a for a in analyses if a["role"] == "Machine Learning Engineer")
    roadmap = build_roadmap(ml_engineer)
    assert [item["skill"] for item in roadmap["items"]] == [
        "Git",
        "Machine Learning",
        "scikit-learn",
        "FastAPI",
        "Docker",
    ]
    assert roadmap["total_weeks"] == 8