import streamlit as st

from charts import role_scores_chart, skill_coverage_chart, skills_by_category_chart
from job_matcher import (
    BONUS_WEIGHT,
    REQUIRED_WEIGHT,
    SIMILARITY_CAP,
    TEXT_WEIGHT,
    analyze_roles,
    describe_score,
    load_job_roles,
    recommend_roles,
)
from resume_parser import MAX_FILE_SIZE_MB, ResumeParseError, extract_resume_text
from report_generator import build_report_pdf, report_filename
from roadmap_generator import build_roadmap
from skill_extractor import extract_skills, group_by_category, load_skill_dictionary
from text_cleaner import clean_text
from ui_styles import (
    APP_NAME,
    TAGLINE,
    apply_theme,
    badge_group,
    empty_state,
    page_header,
    role_cards,
    roadmap_cards,
    sidebar_brand,
    sidebar_step,
    summary_cards,
)

st.set_page_config(
    page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded"
)

DISCLAIMER = "For educational career guidance only. Not a hiring or rejection tool."
CHART_CONFIG = {"displayModeBar": False}  # hide Plotly's zoom/camera toolbar


def render_sidebar_footer():
    with st.sidebar:
        st.divider()
        st.caption(
            "Your resume is processed in memory and is not saved by this app. "
            "Results are estimates for learning and guidance, not hiring decisions."
        )


def render_how_it_works():
    st.markdown(
        f"**Match score = {REQUIRED_WEIGHT:.0%} x required-skill coverage "
        f"+ {BONUS_WEIGHT:.0%} x bonus-skill coverage "
        f"+ {TEXT_WEIGHT:.0%} x wording similarity**"
    )
    st.markdown(
        "- **Required-skill coverage:** the share of the role's core skills found "
        "in your resume.\n"
        "- **Bonus-skill coverage:** the share of the role's extra skills found.\n"
        "- **Wording similarity:** TF-IDF cosine similarity between your resume and "
        f"the role description, scaled so {SIMILARITY_CAP} or more counts as full marks."
    )
    st.markdown("**Limitations**")
    st.markdown(
        "- Skills are found by keyword matching, so synonyms and context are missed.\n"
        "- All required skills count equally, so a role can look stronger than it is.\n"
        "- Only skills in our dictionary are detected.\n"
        "- A missing keyword does not mean a missing ability.\n"
        "- Scores are estimates, not a recruiter's decision or a hiring probability."
    )
    st.markdown("**Privacy and fairness**")
    st.markdown(
        "- Your resume is processed in memory and is not saved by this app.\n"
        "- Emails, phone numbers and links are removed before analysis.\n"
        "- Only job-related skills and wording are scored. Age, gender, religion, "
        "nationality, marital status, disability and photographs are not used."
    )
    st.markdown("**Job roles used for comparison**")
    st.caption(
        "Required skills are the core skills usually expected for an entry-level "
        "role. Bonus skills are helpful extras. These lists are a curated starting "
        "point and real job postings vary."
    )
    st.dataframe(
        [
            {
                "Role": role["name"],
                "Required skills": ", ".join(role["required_skills"]),
                "Bonus skills": ", ".join(role["bonus_skills"]),
            }
            for role in load_job_roles()
        ],
        hide_index=True,
    )


def render_overview(found_skills, skills_by_category, dictionary_size, resume_text, cleaned_text):
    st.subheader("Skills found in your resume")
    if not found_skills:
        st.warning(
            "None of the skills in our dictionary were found. Check that your "
            "resume text was extracted correctly in the preview below."
        )
    else:
        badges_column, chart_column = st.columns([3, 2])
        with badges_column:
            for category, skills in skills_by_category.items():
                badge_group(category, skills, "info")
        with chart_column:
            with st.container(border=True):
                st.caption("Skills found per category")
                st.plotly_chart(
                    skills_by_category_chart(skills_by_category),
                    width="stretch",
                    config=CHART_CONFIG,
                )
    st.caption(
        f"Skills are detected by keyword matching against a curated dictionary of "
        f"{dictionary_size} skills. A skill that is not listed here may still be "
        f"part of your experience. {len(cleaned_text.split()):,} words were read "
        "from your resume."
    )
    with st.expander("See the text the app extracted"):
        tab_original, tab_cleaned = st.tabs(["Original text", "Cleaned text"])
        with tab_original:
            st.text_area(
                "Original text",
                resume_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
                key="original_preview",
            )
        with tab_cleaned:
            st.text_area(
                "Cleaned text",
                cleaned_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
                key="cleaned_preview",
            )


def render_roles(recommendations, analyses):
    st.subheader("Top recommended roles")
    if recommendations[0]["score"] < 30:
        st.warning(
            "None of the roles show strong overlap with this resume yet. The cards "
            "below are simply the closest matches. Adding relevant skills and "
            "projects to your resume will change them."
        )
    role_cards(recommendations)
    st.caption(
        "Recommendations rank roles by match score. They show the closest overlap "
        "with your resume text and are not a prediction of your suitability or of "
        "hiring outcomes."
    )

    st.subheader("All role scores")
    with st.container(border=True):
        st.plotly_chart(
            role_scores_chart(analyses), width="stretch", config=CHART_CONFIG
        )

    with st.expander("See the full score table"):
        st.dataframe(
            [
                {
                    "Role": item["role"],
                    "Match score": item["score"],
                    "Overlap": describe_score(item["score"]),
                    "Required skills": (
                        f"{len(item['required_matched'])}/"
                        f"{len(item['required_matched']) + len(item['required_missing'])}"
                    ),
                    "Bonus skills": (
                        f"{len(item['bonus_matched'])}/"
                        f"{len(item['bonus_matched']) + len(item['bonus_missing'])}"
                    ),
                    "Text similarity": round(item["similarity"], 2),
                }
                for item in analyses
            ],
            hide_index=True,
            column_config={
                "Match score": st.column_config.ProgressColumn(
                    "Match score (/100)", min_value=0, max_value=100, format="%d"
                )
            },
        )


def render_skill_gap(selected):
    st.subheader(f"Skill gap for {selected['role']}")
    score_column, chart_column = st.columns([1, 3])
    score_column.metric("Match score", f"{selected['score']} / 100")
    score_column.caption(describe_score(selected["score"]))
    with chart_column:
        with st.container(border=True):
            st.caption("Skills found and not found for this role")
            st.plotly_chart(
                skill_coverage_chart(selected), width="stretch", config=CHART_CONFIG
            )

    badge_group(
        "Required skills found", selected["required_matched"], "found", "None found yet"
    )
    badge_group(
        "Required skills not found",
        selected["required_missing"],
        "missing",
        "None. All required skills were found.",
    )
    badge_group("Bonus skills found", selected["bonus_matched"], "info", "None found yet")
    badge_group(
        "Bonus skills not found",
        selected["bonus_missing"],
        "neutral",
        "None. All bonus skills were found.",
    )
    st.caption(
        "'Not found' means the skill was not detected in your resume text. You may "
        "have the skill but describe it differently or not have listed it."
    )


def render_roadmap(roadmap, target_role):
    st.subheader(f"Learning roadmap for {target_role}")
    if not roadmap["items"]:
        st.success(
            f"No missing skills were found for {target_role}, so there is nothing "
            "to add to a roadmap."
        )
        return

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Skills in this plan", len(roadmap["items"]))
    metric_b.metric("Estimated duration", f"{roadmap['total_weeks']} weeks")
    metric_c.metric(
        "Study time", f"~{roadmap['total_weeks'] * roadmap['hours_per_week']} hours"
    )
    st.caption(
        "A suggested order for learning the skills that were not found, planned at "
        f"about {roadmap['hours_per_week']} hours per week. These are rough "
        "estimates for a beginner, so adjust them to your own pace and background."
    )

    roadmap_cards(roadmap["items"])

    st.markdown("**Week-by-week plan**")
    st.dataframe(
        [
            {"Week": row["week"], "Skill": row["skill"], "Focus": row["focus"]}
            for row in roadmap["weekly_plan"]
        ],
        hide_index=True,
    )
    if roadmap["remaining"]:
        st.caption(
            "Not in this plan yet: "
            + ", ".join(roadmap["remaining"])
            + ". Revisit them after you finish the steps above."
        )


def render_report(skills_by_category, analyses, selected, roadmap):
    st.subheader("Downloadable report")
    st.caption(
        "A PDF summary of this analysis for the selected target role. It contains "
        "your scores, skills, gaps and roadmap. It does not include your resume "
        "text or personal details, and this app does not save it."
    )
    try:
        pdf_bytes = build_report_pdf(
            skills_by_category, analyses, selected, roadmap, product_name=APP_NAME
        )
    except Exception:  # a report problem must never break the dashboard
        st.error(
            "The report could not be created. Please try again or choose a "
            "different target role."
        )
        return

    st.download_button(
        "Download PDF report",
        data=pdf_bytes,
        file_name=report_filename(selected["role"]),
        mime="application/pdf",
        type="primary",
    )
    st.markdown("**What is inside the report**")
    st.markdown(
        "- A summary of your target role and match score\n"
        "- Your top three recommended roles\n"
        "- Skills found, grouped by category\n"
        "- The skill gap for your target role\n"
        "- A learning roadmap with practice projects\n"
        "- How to read the scores and what their limits are"
    )
    st.caption(f"The report follows the target role chosen in the sidebar ({selected['role']}).")


def main():
    apply_theme()

    with st.sidebar:
        sidebar_brand()
        sidebar_step(1, "Upload your resume")
        uploaded_file = st.file_uploader(
            "Resume (PDF or DOCX)",
            type=["pdf", "docx"],
            label_visibility="collapsed",
            help=f"Maximum size: {MAX_FILE_SIZE_MB} MB. Your file is processed in memory and is not stored.",
        )

    page_header(APP_NAME, TAGLINE, DISCLAIMER)

    if uploaded_file is None:
        empty_state()
        with st.expander("How scoring works and which roles are compared"):
            render_how_it_works()
        render_sidebar_footer()
        st.stop()

    try:
        with st.spinner("Reading your resume..."):
            resume_text = extract_resume_text(
                uploaded_file.name, uploaded_file.getvalue()
            )
    except ResumeParseError as error:
        st.error(str(error))
        render_sidebar_footer()
        st.stop()

    cleaned_text = clean_text(resume_text)
    skill_dictionary = load_skill_dictionary()
    found_skills = extract_skills(cleaned_text, skill_dictionary)
    skills_by_category = group_by_category(found_skills, skill_dictionary)
    analyses = analyze_roles(cleaned_text, found_skills)
    recommendations = recommend_roles(analyses)

    with st.sidebar:
        sidebar_step(2, "Choose a target role")
        target_role = st.selectbox(
            "Target role",
            [item["role"] for item in analyses],
            label_visibility="collapsed",
            help="Starts on your highest-scoring role. Choose any role to see its skill gap and roadmap.",
        )
    render_sidebar_footer()

    selected = next(item for item in analyses if item["role"] == target_role)
    roadmap = build_roadmap(selected)
    best = analyses[0]

    summary_cards(
        [
            ("Best match", best["role"], f"Score {best['score']} / 100, {describe_score(best['score']).lower()}"),
            ("Skills found", len(found_skills), f"in {len(skills_by_category)} categories"),
            ("Target role score", f"{selected['score']} / 100", target_role),
            ("Required gaps", len(selected["required_missing"]), f"required skills not found for {target_role}"),
        ]
    )

    tab_overview, tab_roles, tab_gap, tab_roadmap, tab_report, tab_how = st.tabs(
        ["Overview", "Roles", "Skill gap", "Roadmap", "Report", "How it works"]
    )
    with tab_overview:
        render_overview(
            found_skills, skills_by_category, len(skill_dictionary), resume_text, cleaned_text
        )
    with tab_roles:
        render_roles(recommendations, analyses)
    with tab_gap:
        render_skill_gap(selected)
    with tab_roadmap:
        render_roadmap(roadmap, target_role)
    with tab_report:
        render_report(skills_by_category, analyses, selected, roadmap)
    with tab_how:
        render_how_it_works()


main()