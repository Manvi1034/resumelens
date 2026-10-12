from ui_styles import (
    APP_NAME,
    CSS,
    EMPTY_STATE_STEPS,
    empty_state_html,
    page_header_html,
    sidebar_brand_html,
    sidebar_step_html,
)


def test_page_header_shows_title_subtitle_and_note():
    html = page_header_html("ResumeLens", "A tagline", "Guidance only")
    assert "ResumeLens" in html and "A tagline" in html
    assert "rl-pill" in html and "Guidance only" in html


def test_page_header_without_note_has_no_pill():
    assert "rl-pill" not in page_header_html("ResumeLens", "A tagline")


def test_page_header_escapes_html():
    html = page_header_html("<b>Title</b>", "<i>Sub</i>", "<u>Note</u>")
    assert "<b>" not in html and "<i>" not in html and "<u>" not in html


def test_sidebar_brand_shows_name_and_first_letter_logo():
    html = sidebar_brand_html()
    assert APP_NAME in html
    assert f'<div class="rl-logo">{APP_NAME[0]}</div>' in html


def test_sidebar_step_shows_number_and_text_and_escapes():
    html = sidebar_step_html(2, "Choose <a role>")
    assert ">2<" in html
    assert "Choose &lt;a role&gt;" in html and "<a role>" not in html


def test_empty_state_has_three_step_cards():
    html = empty_state_html()
    assert html.count("rl-step-badge") == len(EMPTY_STATE_STEPS) == 3
    for title in ("Upload", "Review", "Plan"):
        assert title in html


def test_html_builders_have_no_blank_lines_or_indented_lines():
    # Markdown would treat blank lines or 4-space indents as code, not HTML.
    for html in (
        page_header_html("T", "S", "N"),
        sidebar_brand_html(),
        sidebar_step_html(1, "Upload"),
        empty_state_html(),
    ):
        assert "\n" not in html


def test_css_is_a_single_style_block_with_the_uploader_rules():
    assert CSS.count("<style>") == 1 and CSS.count("</style>") == 1
    assert "stFileUploaderDropzone" in CSS
    assert "@media" in CSS