"""Design system for the dashboard: colours, CSS and small HTML helpers.

Every piece of text that goes into HTML is escaped, so a skill name or role
name can never inject markup into the page.
"""

from html import escape

import streamlit as st

APP_NAME = "ResumeLens"
TAGLINE = "AI resume analysis and role recommendations for students"
SIDEBAR_TAGLINE = "Resume analysis for students"

CSS = """
<style>
:root {--navy: #1B2559; --slate: #475069; --indigo: #4F46E5; --indigo-dark: #4338CA; --tint: #EEF0FF; --border: #E3E6EF; --track: #E9ECF5;}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container, [data-testid="stMainBlockContainer"] {padding: 4rem 2.25rem 3rem 2.25rem; max-width: 1320px;}
section[data-testid="stSidebar"] {border-right: 1px solid var(--border);}
[data-testid="stSidebarUserContent"] {padding-top: 0.5rem;}
div[data-testid="stHeading"] h2, div[data-testid="stHeading"] h3 {font-size: 1.3rem; font-weight: 700; color: var(--navy); letter-spacing: -0.01em; padding-top: 0.5rem;}
[data-testid="stMetric"] {background: #FFFFFF; border: 1px solid var(--border); border-radius: 12px; padding: 0.75rem 1rem; box-shadow: 0 1px 2px rgba(27, 37, 89, 0.06);}
[data-testid="stFileUploaderDropzone"] {background: #F8F9FF; border: 2px dashed #B8BEF5; border-radius: 12px; padding: 1rem;}
[data-testid="stFileUploaderDropzone"]:hover {background: var(--tint); border-color: var(--indigo);}
[data-testid="stFileUploaderDropzone"] button {background: var(--indigo); border: 1px solid var(--indigo); border-radius: 8px; font-weight: 600;}
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] button * {color: #FFFFFF;}
[data-testid="stFileUploaderDropzone"] button:hover {background: var(--indigo-dark); border-color: var(--indigo-dark);}
.rl-hero {display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem 1.5rem; background: var(--tint); border: 1px solid #D9DEFA; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem;}
.rl-hero .rl-title {font-size: 1.9rem; font-weight: 800; color: var(--navy); margin: 0; line-height: 1.15; letter-spacing: -0.02em;}
.rl-hero .rl-subtitle {color: var(--slate); margin: 0.3rem 0 0 0; font-size: 1rem;}
.rl-pill {display: inline-block; background: #FFFFFF; color: var(--indigo-dark); border: 1px solid #C7CDF7; border-radius: 999px; padding: 0.3rem 0.85rem; font-size: 0.82rem; font-weight: 600;}
.rl-brand {display: flex; align-items: center; gap: 0.7rem; margin: 0 0 1.25rem 0;}
.rl-brand .rl-logo {display: flex; align-items: center; justify-content: center; flex: 0 0 2.4rem; width: 2.4rem; height: 2.4rem; border-radius: 10px; background: var(--indigo); color: #FFFFFF; font-weight: 800; font-size: 1.2rem;}
.rl-brand .rl-brand-name {font-size: 1.15rem; font-weight: 700; color: var(--navy); margin: 0; line-height: 1.2;}
.rl-brand .rl-brand-sub {font-size: 0.8rem; color: var(--slate); margin: 0;}
.rl-sidebar-step {display: flex; align-items: center; gap: 0.55rem; font-weight: 600; color: var(--navy); margin: 0.5rem 0 0.4rem 0;}
.rl-sidebar-step .rl-step-num {display: inline-flex; align-items: center; justify-content: center; flex: 0 0 1.5rem; width: 1.5rem; height: 1.5rem; border-radius: 999px; background: var(--indigo); color: #FFFFFF; font-size: 0.8rem; font-weight: 700;}
.rl-section-title {font-size: 1.1rem; font-weight: 700; color: var(--navy); margin: 0.25rem 0 0 0;}
.rl-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin: 0.9rem 0 1.25rem 0;}
.rl-grid.rl-grid-wide {grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));}
.rl-card {background: #FFFFFF; border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.15rem; box-shadow: 0 1px 2px rgba(27, 37, 89, 0.06);}
.rl-card .rl-label {font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--slate); margin: 0;}
.rl-card .rl-value {font-size: 1.45rem; font-weight: 700; color: var(--navy); line-height: 1.25; margin: 0.2rem 0 0 0; overflow-wrap: anywhere;}
.rl-card .rl-note {font-size: 0.88rem; color: var(--slate); margin: 0.3rem 0 0 0;}
.rl-card .rl-role-name {font-size: 1.2rem; font-weight: 700; color: var(--navy); margin: 0.35rem 0 0 0;}
.rl-card .rl-score {font-size: 2.2rem; font-weight: 700; color: var(--indigo); line-height: 1.1; margin: 0.4rem 0 0 0;}
.rl-card .rl-score span {font-size: 1rem; font-weight: 500; color: var(--slate);}
.rl-card .rl-step-badge {display: flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; border-radius: 999px; background: var(--tint); color: var(--indigo-dark); font-weight: 700; margin: 0 0 0.6rem 0;}
.rl-card .rl-step-title {font-size: 1.05rem; font-weight: 700; color: var(--navy); margin: 0;}
.rl-bar {height: 8px; background: var(--track); border-radius: 999px; overflow: hidden; margin-top: 0.5rem;}
.rl-bar div {height: 100%; background: var(--indigo); border-radius: 999px;}
.rl-card .rl-list {margin: 0.7rem 0 0 0; padding-left: 1.1rem; color: var(--slate); font-size: 0.9rem;}
.rl-card .rl-list li {margin-bottom: 0.4rem;}
.rl-group {margin-bottom: 0.9rem;}
.rl-group .rl-group-title {font-weight: 600; color: var(--navy); margin: 0 0 0.35rem 0;}
.rl-badge {display: inline-block; padding: 0.15rem 0.65rem; margin: 0 0.35rem 0.35rem 0; border-radius: 999px; border: 1px solid transparent; font-size: 0.82rem; font-weight: 500;}
.rl-found {background: #E7F6EC; color: #14532D; border-color: #BFE5CC;}
.rl-missing {background: #FDECEC; color: #7F1D1D; border-color: #F5C2C2;}
.rl-info {background: #E8EEFF; color: #1E3A8A; border-color: #C7D4FB;}
.rl-neutral {background: #EEF0F6; color: #334155; border-color: #D8DCE8;}
.rl-muted {color: var(--slate); font-size: 0.9rem;}
.rl-card .rl-subhead {font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--slate); margin: 0.9rem 0 0.4rem 0;}
.rl-card .rl-project {font-size: 0.9rem; color: var(--slate); margin: 0.9rem 0 0 0;}
.rl-card .rl-project strong {color: var(--navy);}
@media (max-width: 640px) {.block-container, [data-testid="stMainBlockContainer"] {padding: 3.5rem 1rem 2rem 1rem;} .rl-hero {padding: 1rem;} .rl-hero .rl-title {font-size: 1.5rem;}}
</style>
"""

KIND_CLASSES = {
    "found": "rl-found",
    "missing": "rl-missing",
    "info": "rl-info",
    "neutral": "rl-neutral",
}

EMPTY_STATE_STEPS = (
    (
        "1",
        "Upload",
        "Add a PDF or DOCX in the sidebar (the arrow at the top left opens it on "
        "small screens). Your file is read in memory and is not saved.",
    ),
    (
        "2",
        "Review",
        "See which skills were found, how your resume compares with each role, "
        "and where the gaps are.",
    ),
    (
        "3",
        "Plan",
        "Choose a target role and follow a week-by-week learning roadmap.",
    ),
)


# ---------- pure HTML builders (easy to test) ----------


def badges_html(skills, kind):
    """Return one coloured label per skill."""
    css_class = KIND_CLASSES.get(kind, "rl-neutral")
    return "".join(
        f'<span class="rl-badge {css_class}">{escape(str(skill))}</span>'
        for skill in skills
    )


def badge_group_html(title, skills, kind, empty_text="None"):
    """Return a titled group of skill labels, or a muted message if empty."""
    if skills:
        body = badges_html(skills, kind)
    else:
        body = f'<span class="rl-muted">{escape(empty_text)}</span>'
    return (
        f'<div class="rl-group"><p class="rl-group-title">{escape(title)}</p>'
        f"{body}</div>"
    )


def summary_cards_html(cards):
    """Return a responsive grid of summary cards from (label, value, note) tuples."""
    items = "".join(
        '<div class="rl-card">'
        f'<p class="rl-label">{escape(str(label))}</p>'
        f'<p class="rl-value">{escape(str(value))}</p>'
        f'<p class="rl-note">{escape(str(note))}</p>'
        "</div>"
        for label, value, note in cards
    )
    return f'<div class="rl-grid">{items}</div>'


def role_cards_html(recommendations):
    """Return the recommendation cards from recommend_roles() output."""
    cards = []
    for recommendation in recommendations:
        score = int(recommendation["score"])
        bullets = "".join(
            f"<li>{escape(line)}</li>" for line in recommendation["explanation"]
        )
        cards.append(
            '<div class="rl-card">'
            f'<p class="rl-label">Recommendation #{int(recommendation["rank"])}</p>'
            f'<p class="rl-role-name">{escape(recommendation["role"])}</p>'
            f'<p class="rl-score">{score}<span> / 100</span></p>'
            '<div class="rl-bar" role="progressbar" aria-label="Match score" '
            f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score}">'
            f'<div style="width:{score}%"></div></div>'
            f'<p class="rl-note">{escape(recommendation["label"])}</p>'
            f'<ul class="rl-list">{bullets}</ul>'
            "</div>"
        )
    return f'<div class="rl-grid rl-grid-wide">{"".join(cards)}</div>'


def page_header_html(title, subtitle, note=None):
    """Return the page header card. `note` appears as a small pill on the right."""
    pill = f'<span class="rl-pill">{escape(note)}</span>' if note else ""
    return (
        '<div class="rl-hero"><div>'
        f'<p class="rl-title">{escape(title)}</p>'
        f'<p class="rl-subtitle">{escape(subtitle)}</p>'
        f"</div>{pill}</div>"
    )


def sidebar_brand_html():
    """Return the logo mark, product name and tagline for the top of the sidebar."""
    return (
        '<div class="rl-brand">'
        f'<div class="rl-logo">{escape(APP_NAME[:1])}</div>'
        "<div>"
        f'<p class="rl-brand-name">{escape(APP_NAME)}</p>'
        f'<p class="rl-brand-sub">{escape(SIDEBAR_TAGLINE)}</p>'
        "</div></div>"
    )


def sidebar_step_html(number, text):
    """Return a numbered step heading for the sidebar."""
    return (
        '<div class="rl-sidebar-step">'
        f'<span class="rl-step-num">{escape(str(number))}</span>'
        f"<span>{escape(text)}</span></div>"
    )


def empty_state_html():
    """Return the welcome content shown before a resume is uploaded."""
    cards = "".join(
        '<div class="rl-card">'
        f'<div class="rl-step-badge">{escape(number)}</div>'
        f'<p class="rl-step-title">{escape(title)}</p>'
        f'<p class="rl-note">{escape(text)}</p>'
        "</div>"
        for number, title, text in EMPTY_STATE_STEPS
    )
    return (
        '<p class="rl-section-title">Get started in three steps</p>'
        f'<div class="rl-grid">{cards}</div>'
    )

def roadmap_cards_html(items):
    """Return one card per roadmap step, from build_roadmap()["items"]."""
    cards = []
    for item in items:
        if item["start_week"] == item["end_week"]:
            when = f"Week {int(item['start_week'])}"
        else:
            when = f"Weeks {int(item['start_week'])}-{int(item['end_week'])}"
        kind = "info" if item["priority"] == "Required" else "neutral"
        cards.append(
            '<div class="rl-card">'
            f'<p class="rl-label">Step {int(item["order"])} &middot; {escape(when)}</p>'
            f'<p class="rl-role-name">{escape(item["skill"])}</p>'
            f'<div>{badges_html([item["priority"] + " skill"], kind)}</div>'
            '<p class="rl-subhead">Topics</p>'
            f'<div>{badges_html(item["topics"], "neutral")}</div>'
            f'<p class="rl-project"><strong>Practice project:</strong> {escape(item["project"])}</p>'
            "</div>"
        )
    return f'<div class="rl-grid rl-grid-wide">{"".join(cards)}</div>'

# ---------- functions that draw on the page ----------


def apply_theme():
    """Inject the dashboard CSS. Call once, near the top of the app."""
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, subtitle, note=None):
    st.markdown(page_header_html(title, subtitle, note), unsafe_allow_html=True)


def sidebar_brand():
    st.markdown(sidebar_brand_html(), unsafe_allow_html=True)


def sidebar_step(number, text):
    st.markdown(sidebar_step_html(number, text), unsafe_allow_html=True)


def summary_cards(cards):
    st.markdown(summary_cards_html(cards), unsafe_allow_html=True)


def role_cards(recommendations):
    st.markdown(role_cards_html(recommendations), unsafe_allow_html=True)


def badge_group(title, skills, kind, empty_text="None"):
    st.markdown(
        badge_group_html(title, skills, kind, empty_text), unsafe_allow_html=True
    )


def empty_state():
    st.markdown(empty_state_html(), unsafe_allow_html=True)



def roadmap_cards(items):
    st.markdown(roadmap_cards_html(items), unsafe_allow_html=True)
