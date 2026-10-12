import inspect
import io
from datetime import date

from pypdf import PdfReader

from report_generator import build_report_pdf, report_filename, safe_text


def make_analysis(role, score, req_found, req_missing, bonus_found=(), bonus_missing=()):
    return {
        "role": role,
        "score": score,
        "similarity": 0.2,
        "required_matched": list(req_found),
        "required_missing": list(req_missing),
        "bonus_matched": list(bonus_found),
        "bonus_missing": list(bonus_missing),
    }


def sample_analyses():
    return [
        make_analysis("Full Stack Developer", 90, ["JavaScript", "React", "SQL"], [], ["Docker"], ["MongoDB"]),
        make_analysis("Python Developer", 69, ["Python", "Git", "SQL", "REST API"], ["Linux"], ["Flask"], ["Django"]),
        make_analysis(
            "Machine Learning Engineer",
            53,
            ["Python", "Pandas", "NumPy"],
            ["Machine Learning", "scikit-learn"],
            ["CI/CD"],
            ["MLflow", "AWS"],
        ),
        make_analysis("Data Analyst", 37, ["Python"], ["Excel", "Power BI"]),
    ]


def sample_roadmap():
    return {
        "role": "Machine Learning Engineer",
        "items": [
            {
                "order": 1, "skill": "Machine Learning", "priority": "Required",
                "start_week": 1, "end_week": 3, "weeks": 3,
                "topics": ["Supervised learning", "Train test split", "Evaluation metrics"],
                "project": "Predict a value from a public dataset",
            },
            {
                "order": 2, "skill": "scikit-learn", "priority": "Required",
                "start_week": 4, "end_week": 4, "weeks": 1,
                "topics": ["Pipelines", "Cross validation"],
                "project": "Compare three models on one dataset",
            },
        ],
        "weekly_plan": [],
        "total_weeks": 4,
        "hours_per_week": 8,
        "remaining": ["Kubernetes"],
    }


def sample_groups():
    return {"Programming": ["Python", "Java", "C++"], "Databases": ["SQL"]}


def build(**overrides):
    analyses = sample_analyses()
    arguments = {
        "skills_by_category": sample_groups(),
        "analyses": analyses,
        "selected": analyses[2],
        "roadmap": sample_roadmap(),
        "generated_on": date(2026, 10, 11),
    }
    arguments.update(overrides)
    return build_report_pdf(**arguments)


def read_pdf(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = " ".join(" ".join((page.extract_text() or "").split()) for page in reader.pages)
    return reader, text


def test_report_is_a_valid_pdf():
    pdf = build()
    reader, _ = read_pdf(pdf)
    assert pdf.startswith(b"%PDF")
    assert len(reader.pages) >= 1


def test_report_contains_every_section_heading():
    _, text = read_pdf(build())
    for heading in (
        "Summary",
        "Top recommended roles",
        "Skills found in the resume",
        "Skill gap for Machine Learning Engineer",
        "Learning roadmap for Machine Learning Engineer",
        "How to read this report",
    ):
        assert heading in text, heading


def test_report_shows_target_role_score_and_date():
    _, text = read_pdf(build())
    assert "53 / 100" in text and "Moderate overlap" in text
    assert "11 October 2026" in text


def test_report_lists_top_three_roles_only():
    _, text = read_pdf(build())
    for role in ("Full Stack Developer", "Python Developer"):
        assert role in text
    assert "Data Analyst" not in text


def test_report_lists_skills_found_and_missing():
    _, text = read_pdf(build())
    assert "Python, Java, C++" in text
    assert "Machine Learning, scikit-learn" in text
    assert "CI/CD" in text and "MLflow, AWS" in text


def test_report_contains_the_roadmap_steps():
    _, text = read_pdf(build())
    assert "Machine Learning" in text and "Required skill" in text
    assert "Predict a value from a public dataset" in text
    assert "1-3" in text
    assert "Not in this plan yet: Kubernetes" in text


def test_report_handles_no_missing_skills():
    analyses = sample_analyses()
    roadmap = {**sample_roadmap(), "items": [], "remaining": [], "total_weeks": 0}
    _, text = read_pdf(build(selected=analyses[0], roadmap=roadmap))
    assert "nothing to add to a roadmap" in text
    assert "None. All required skills were found." in text


def test_report_handles_no_skills_found():
    _, text = read_pdf(build(skills_by_category={}))
    assert "No skills from the dictionary were detected" in text


def test_report_does_not_break_on_special_characters():
    analyses = sample_analyses()
    analyses[2]["required_missing"] = ["<b>Bold</b> & more", "C#", "emoji \U0001F642", "\u65e5\u672c\u8a9e"]
    pdf = build(selected=analyses[2], analyses=analyses)
    _, text = read_pdf(pdf)
    assert "<b>Bold</b> & more" in text  # shown literally, not treated as markup
    assert "C#" in text


def test_long_roadmap_spans_pages_with_page_numbers():
    items = []
    for number in range(1, 41):
        items.append(
            {
                "order": number, "skill": f"Skill {number}", "priority": "Bonus",
                "start_week": number, "end_week": number, "weeks": 1,
                "topics": ["Topic one", "Topic two", "Topic three", "Topic four"],
                "project": "A practice project with a fairly long description to wrap",
            }
        )
    roadmap = {**sample_roadmap(), "items": items, "total_weeks": 40}
    reader, text = read_pdf(build(roadmap=roadmap))
    assert len(reader.pages) >= 2
    assert "Page 1" in text and "Page 2" in text


def test_report_never_receives_the_resume_text():
    parameters = inspect.signature(build_report_pdf).parameters
    assert not any("resume" in name for name in parameters)


def test_safe_text_keeps_symbols_and_replaces_unsupported_characters():
    assert safe_text("C++ C# .NET CI/CD") == "C++ C# .NET CI/CD"
    assert safe_text("caf\u00e9") == "caf\u00e9"
    assert safe_text("go \u2192 home") == "go ? home"


def test_report_filename_is_safe_and_dated():
    name = report_filename("Machine Learning Engineer", date(2026, 10, 11))
    assert name == "resumelens-report-machine-learning-engineer-2026-10-11.pdf"
    assert report_filename("C++ / <Dev>", date(2026, 1, 2)) == "resumelens-report-c-dev-2026-01-02.pdf"
    assert report_filename("???", date(2026, 1, 2)) == "resumelens-report-role-2026-01-02.pdf"


def test_roadmap_heading_stays_on_the_same_page_as_its_table():
    """With a realistic amount of content the heading used to be left alone at
    the bottom of page 1 while its table started on page 2."""
    def analysis(role, score, found, missing, bonus_found, bonus_missing):
        return make_analysis(role, score, found, missing, bonus_found, bonus_missing)

    analyses = [
        analysis("Full Stack Developer", 90, ["JavaScript", "HTML", "CSS", "React", "Node.js", "REST API", "SQL", "Git"], [], ["Docker", "PostgreSQL", "GitHub", "CI/CD", "Python"], ["MongoDB", "AWS"]),
        analysis("Python Developer", 69, ["Python", "Git", "SQL", "REST API"], ["Linux"], ["Flask", "FastAPI", "Docker", "PostgreSQL", "CI/CD"], ["Django", "MongoDB"]),
        analysis("Machine Learning Engineer", 53, ["Python", "Pandas", "NumPy", "FastAPI", "Docker", "Git"], ["Machine Learning", "scikit-learn"], ["CI/CD"], ["MLflow", "AWS", "Statistics", "Deep Learning", "Kubernetes"]),
    ]
    groups = {
        "Programming": ["Python", "Java", "JavaScript", "C++"],
        "Databases": ["SQL", "PostgreSQL"],
        "Web Development": ["HTML", "CSS", "React", "Node.js", "REST API", "FastAPI", "Flask"],
        "Data Analytics": ["Pandas", "NumPy", "Matplotlib"],
        "Cloud & DevOps": ["Google Cloud", "Docker", "CI/CD"],
        "Tools": ["Git", "GitHub"],
    }
    pdf = build(skills_by_category=groups, analyses=analyses, selected=analyses[2])
    reader = PdfReader(io.BytesIO(pdf))
    pages = [" ".join((page.extract_text() or "").split()) for page in reader.pages]
    heading_pages = [i for i, text in enumerate(pages) if "Learning roadmap for" in text]
    table_pages = [i for i, text in enumerate(pages) if "Practice project" in text]
    assert heading_pages and heading_pages == table_pages