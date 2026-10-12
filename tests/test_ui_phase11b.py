from charts import GREEN, RED, skill_coverage_chart, skills_by_category_chart
from ui_styles import roadmap_cards_html


def fake_selected(**overrides):
    selected = {
        "role": "Test Role",
        "required_matched": ["Python", "SQL", "Git"],
        "required_missing": ["Docker", "Linux"],
        "bonus_matched": ["Flask"],
        "bonus_missing": ["Django", "FastAPI", "MongoDB"],
    }
    selected.update(overrides)
    return selected


def fake_roadmap_items():
    return [
        {
            "order": 1,
            "skill": "Git",
            "priority": "Required",
            "start_week": 1,
            "end_week": 1,
            "topics": ["Commits and history", "Branches"],
            "project": "Put a project under <Git>",
        },
        {
            "order": 2,
            "skill": "Machine Learning",
            "priority": "Bonus",
            "start_week": 2,
            "end_week": 4,
            "topics": ["Regression", "Evaluation"],
            "project": "Predict a value",
        },
    ]


# ---------- skills by category chart ----------


def test_category_chart_counts_skills_and_puts_the_largest_on_top():
    grouped = {"Databases": ["SQL"], "Programming": ["Python", "Java", "C++"], "Tools": ["Git", "GitHub"]}
    bar = skills_by_category_chart(grouped).data[0]
    assert list(bar.y)[-1] == "Programming"
    assert dict(zip(bar.y, bar.x)) == {"Databases": 1, "Programming": 3, "Tools": 2}


def test_category_chart_handles_no_skills():
    figure = skills_by_category_chart({})
    assert len(figure.data[0].x) == 0


def test_category_chart_axis_shows_whole_numbers():
    figure = skills_by_category_chart({"Tools": ["Git", "GitHub"]})
    assert figure.layout.xaxis.tickformat == "d"
    assert figure.layout.xaxis.dtick == 1


# ---------- found vs not found chart ----------


def test_coverage_chart_has_found_and_not_found_stacks():
    figure = skill_coverage_chart(fake_selected())
    found, missing = figure.data
    assert figure.layout.barmode == "stack"
    assert (found.name, missing.name) == ("Found", "Not found")
    assert found.marker.color == GREEN and missing.marker.color == RED


def test_coverage_chart_counts_match_the_analysis():
    figure = skill_coverage_chart(fake_selected())
    found, missing = figure.data
    # y order is bottom to top: Bonus, Required
    assert list(found.y) == ["Bonus skills", "Required skills"]
    assert list(found.x) == [1, 3]
    assert list(missing.x) == [3, 2]


def test_coverage_chart_hides_zero_labels():
    selected = fake_selected(required_missing=[], bonus_matched=[])
    found, missing = skill_coverage_chart(selected).data
    assert list(found.text) == ["", "3"]
    assert list(missing.text) == ["3", ""]

def test_coverage_chart_legend_lists_found_before_not_found():
    figure = skill_coverage_chart(fake_selected())
    assert figure.layout.legend.traceorder == "normal"

# ---------- roadmap cards ----------


def test_roadmap_cards_show_step_weeks_skill_and_priority():
    html = roadmap_cards_html(fake_roadmap_items())
    assert "Step 1" in html and "Week 1" in html and "Weeks 2-4" in html
    assert "Git" in html and "Machine Learning" in html
    assert "Required skill" in html and "Bonus skill" in html


def test_roadmap_cards_show_topics_and_projects_and_escape_text():
    html = roadmap_cards_html(fake_roadmap_items())
    assert "Commits and history" in html and "Predict a value" in html
    assert "<Git>" not in html and "&lt;Git&gt;" in html


def test_roadmap_cards_with_no_items_is_an_empty_grid():
    assert "rl-card" not in roadmap_cards_html([])


def test_roadmap_card_html_has_no_newlines():
    assert "\n" not in roadmap_cards_html(fake_roadmap_items())