from charts import INDIGO, role_scores_chart
from ui_styles import (
    badge_group_html,
    role_cards_html,
    summary_cards_html,
)


def fake_analyses():
    return [{"role": f"Role {i}", "score": 90 - 10 * i} for i in range(8)]


def test_badges_escape_html():
    html = badge_group_html("Skills", ["<script>alert(1)</script>"], "found")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_badge_group_shows_the_empty_text():
    html = badge_group_html("Required skills not found", [], "missing", "None at all")
    assert "None at all" in html
    assert "rl-badge" not in html


def test_badge_group_uses_the_requested_colour_class():
    assert "rl-found" in badge_group_html("Found", ["Python"], "found")
    assert "rl-missing" in badge_group_html("Missing", ["Docker"], "missing")


def test_summary_cards_show_labels_and_values_and_escape_text():
    html = summary_cards_html(
        [("Best match", "Data <Analyst>", "Score 72 / 100"), ("Skills found", 12, "in 4 categories")]
    )
    assert "Best match" in html and "Skills found" in html
    assert "12" in html
    assert "&lt;Analyst&gt;" in html and "<Analyst>" not in html


def test_role_cards_show_rank_role_score_and_bar_width():
    html = role_cards_html(
        [
            {
                "rank": 1,
                "role": "Data Analyst",
                "score": 72,
                "label": "Moderate overlap",
                "explanation": ["You have 3 of 5.", "Main gaps: <b>x</b>."],
            }
        ]
    )
    assert "Recommendation #1" in html
    assert "Data Analyst" in html
    assert "width:72%" in html
    assert "<b>x</b>" not in html


def test_role_scores_chart_puts_best_role_on_top():
    figure = role_scores_chart(fake_analyses())
    assert list(figure.data[0].y)[-1] == "Role 0"


def test_role_scores_chart_highlights_only_the_top_three():
    colours = list(role_scores_chart(fake_analyses()).data[0].marker.color)
    assert len(colours) == 8
    assert colours.count(INDIGO) == 3
    assert colours[-3:] == [INDIGO] * 3