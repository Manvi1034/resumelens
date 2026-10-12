"""End-to-end tests: sample resume file -> parsing -> skills -> roles -> roadmap -> report.

The expected answers live in tests/test_cases.csv. Files are built in memory by
make_sample_resumes.py, so nothing has to exist on disk.
"""

import pytest

from evaluate import analyze_resume, load_test_cases, precision_recall
from job_matcher import load_job_roles
from make_sample_resumes import (
    PROFILES,
    build_docx,
    build_docx_nested_table,
    build_docx_textbox,
    build_pdf,
)
from report_generator import build_report_pdf
from roadmap_generator import MAX_ROADMAP_ITEMS, build_roadmap
from skill_extractor import group_by_category, load_skill_dictionary

LAYOUT_BUILDERS = {
    "layout_nested_table": build_docx_nested_table,
    "layout_textbox": build_docx_textbox,
}
# Cases whose false positives are a documented limitation of keyword matching.
KNOWN_FALSE_POSITIVES = {"tricky_wording": {"Excel", "Java", "React"}}


def make_cases():
    cases = []
    for case in load_test_cases():
        name = case["resume"]
        if name in PROFILES:
            cases.append((case, name, ".docx", build_docx(PROFILES[name])))
            cases.append((case, name, ".pdf", build_pdf(PROFILES[name])))
        else:
            cases.append((case, name, ".docx", LAYOUT_BUILDERS[name]()))
    return cases


CASES = make_cases()
CASE_IDS = [f"{name}{extension}" for _, name, extension, _ in CASES]
RANKED_CASES = [c for c in CASES if c[0]["expected_top_role"] != "ANY"]
RANKED_IDS = [f"{name}{extension}" for _, name, extension, _ in RANKED_CASES]


def run(name, extension=".docx"):
    data = build_docx(PROFILES[name]) if extension == ".docx" else build_pdf(PROFILES[name])
    return analyze_resume(f"{name}{extension}", data)


def scores(result):
    return [(a["role"], a["score"], round(a["similarity"], 6)) for a in result["analyses"]]


# ---------- extraction quality, skill precision and recall, role ranking ----------


@pytest.mark.parametrize("case, name, extension, data", RANKED_CASES, ids=RANKED_IDS)
def test_top_role_is_the_expected_role(case, name, extension, data):
    result = analyze_resume(f"{name}{extension}", data)
    assert result["analyses"][0]["role"] == case["expected_top_role"]


@pytest.mark.parametrize("case, name, extension, data", CASES, ids=CASE_IDS)
def test_skill_precision_and_recall(case, name, extension, data):
    result = analyze_resume(f"{name}{extension}", data)
    precision, recall = precision_recall(result["skills"], case["true_skills"])
    assert recall == 1.0, set(case["true_skills"]) - set(result["skills"])
    expected_false = KNOWN_FALSE_POSITIVES.get(name, set())
    assert set(result["skills"]) - set(case["true_skills"]) == expected_false


# ---------- consistency, fairness, sparse resumes, gaming ----------


@pytest.mark.parametrize("name", [n for n in PROFILES])
def test_docx_and_pdf_versions_give_the_same_result(name):
    docx_result, pdf_result = run(name, ".docx"), run(name, ".pdf")
    assert docx_result["skills"] == pdf_result["skills"]
    assert scores(docx_result) == scores(pdf_result)


def test_personal_details_do_not_change_any_score():
    plain, personal = run("ml_engineer"), run("ml_engineer_personal")
    assert "Hindu" in personal["text"]  # the details really are in the file
    assert personal["skills"] == plain["skills"]
    assert scores(personal) == scores(plain)


def test_removing_skills_lowers_the_score():
    full = PROFILES["data_analyst"]
    reduced = "\n".join(
        line for line in full.splitlines()
        if not line.startswith(("Tools:", "Libraries:", "Concepts:"))
    )
    before = run("data_analyst")
    after = analyze_resume("reduced.docx", build_docx(reduced))

    def data_analyst_score(result):
        return next(a["score"] for a in result["analyses"] if a["role"] == "Data Analyst")

    assert data_analyst_score(after) < data_analyst_score(before)


def test_very_sparse_resume_scores_low_everywhere():
    result = run("fresher_sparse")
    assert result["analyses"][0]["score"] < 30


def test_keyword_pile_does_not_beat_a_real_resume_with_the_same_skills():
    stuffed = next(a for a in run("keyword_stuffed")["analyses"] if a["role"] == "Machine Learning Engineer")
    honest = next(a for a in run("ml_engineer")["analyses"] if a["role"] == "Machine Learning Engineer")
    assert honest["score"] > stuffed["score"]


# ---------- every target role works from end to end ----------


def test_every_target_role_gives_a_valid_roadmap_and_report():
    result = run("data_analyst")
    dictionary = load_skill_dictionary()
    groups = group_by_category(result["skills"], dictionary)
    found = set(result["skills"])

    assert len(result["analyses"]) == len(load_job_roles())   
    for analysis in result["analyses"]:
        roadmap = build_roadmap(analysis)
        skills = [item["skill"] for item in roadmap["items"]]

        assert len(skills) <= MAX_ROADMAP_ITEMS
        assert len(skills) == len(set(skills))
        assert not (set(skills) & found)  # never teaches a skill already found
        priorities = [item["priority"] for item in roadmap["items"]]
        assert priorities == sorted(priorities, key=lambda p: p != "Required")
        for previous, current in zip(roadmap["items"], roadmap["items"][1:]):
            assert current["start_week"] == previous["end_week"] + 1

        pdf = build_report_pdf(groups, result["analyses"], analysis, roadmap)
        assert pdf.startswith(b"%PDF")