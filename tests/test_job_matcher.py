from job_matcher import (
    build_role_document,
    calculate_skill_coverage,
    compare_resume_to_roles,
    create_vectorizer,
    get_role,
    load_job_roles,
    rank_roles_by_text_similarity,
)
from text_cleaner import clean_text


def top_role(raw_resume_text):
    ranking = rank_roles_by_text_similarity(clean_text(raw_resume_text))
    return ranking[0]["role"]


def test_ranking_covers_every_role_and_is_sorted():
    ranking = rank_roles_by_text_similarity(clean_text("python sql pandas"))
    scores = [item["similarity"] for item in ranking]
    assert len(ranking) == len(load_job_roles())
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0001 for score in scores)


def test_computer_vision_resume_ranks_computer_vision_first():
    text = "Python OpenCV CNN YOLO PyTorch deep learning image processing NumPy"
    assert top_role(text) == "Computer Vision Engineer"


def test_data_analyst_resume_ranks_data_analyst_first():
    text = "Python SQL Excel Pandas Power BI data visualization statistics Tableau"
    assert top_role(text) == "Data Analyst"


def test_nlp_resume_ranks_nlp_first():
    text = "Python NLP transformers Hugging Face spaCy NLTK deep learning PyTorch"
    assert top_role(text) == "NLP Engineer"


def test_empty_resume_gets_zero_similarity():
    ranking = rank_roles_by_text_similarity("")
    assert all(item["similarity"] == 0.0 for item in ranking)


def test_vectorizer_keeps_symbol_skills_in_one_piece():
    analyzer = create_vectorizer().build_analyzer()
    tokens = set(analyzer("c++ c# node.js scikit-learn"))
    assert {"c++", "c#", "node.js", "scikit-learn"} <= tokens


def test_role_document_contains_cleaned_skill_words():
    tokens = build_role_document(get_role("Computer Vision Engineer")).split()
    assert "opencv" in tokens


def test_skill_coverage_lists_matched_and_missing_skills():
    role = {"required_skills": ["Python", "SQL", "Docker", "Git"]}
    result = calculate_skill_coverage(["Python", "Git"], role)
    assert result["matched"] == ["Python", "Git"]
    assert result["missing"] == ["SQL", "Docker"]
    assert result["coverage"] == 0.5


def test_skill_coverage_with_no_required_skills_is_zero():
    assert calculate_skill_coverage(["Python"], {"required_skills": []})["coverage"] == 0.0


def test_compare_resume_to_roles_returns_all_fields():
    results = compare_resume_to_roles(clean_text("python sql"), ["Python", "SQL"])
    assert len(results) == len(load_job_roles())
    for item in results:
        assert {"role", "similarity", "coverage", "matched", "missing"} <= set(item)