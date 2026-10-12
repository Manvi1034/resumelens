"""Report generation: build a PDF analysis report in memory with ReportLab.

The report holds analysis results only (scores, skills, gaps, roadmap). It never
receives the resume text, so no name, email or phone number can end up in it.
Nothing is written to disk: the PDF is returned as bytes.
"""

import io
import re
import unicodedata
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from job_matcher import (
    BONUS_WEIGHT,
    REQUIRED_WEIGHT,
    SIMILARITY_CAP,
    TEXT_WEIGHT,
    describe_score,
)

PRODUCT_NAME = "ResumeLens"
NOTICE = (
    "For educational career guidance only. Not a hiring or rejection tool. "
    "Scores are estimates based on skill and wording overlap, not a recruiter's decision."
)

NAVY = colors.HexColor("#1B2559")
INDIGO = colors.HexColor("#4F46E5")
SLATE = colors.HexColor("#475069")
BORDER = colors.HexColor("#E3E6EF")
TINT = colors.HexColor("#EEF0FF")
FOUND_BG = colors.HexColor("#E7F6EC")
MISSING_BG = colors.HexColor("#FDECEC")
NEUTRAL_BG = colors.HexColor("#EEF0F6")

PAGE_WIDTH, PAGE_HEIGHT = A4
PAGE_MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * PAGE_MARGIN
TOP_ROLES_SHOWN = 3
MAX_GAPS_SHOWN = 4


# ---------- text helpers ----------


def safe_text(value):
    """Make text safe for ReportLab's built-in fonts.

    The built-in fonts only cover Western European characters. Anything else
    (emoji, other scripts, arrows) becomes '?' instead of a broken glyph.
    """
    text = unicodedata.normalize("NFKC", str(value))
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _paragraph(value, style):
    """A paragraph of plain text: unsafe characters replaced and markup escaped."""
    return Paragraph(escape(safe_text(value)), style)


def _join(items, empty="None"):
    return ", ".join(items) if items else empty


def report_filename(role, generated_on=None):
    """Return a safe file name such as resumelens-report-data-analyst-2026-10-11.pdf."""
    generated_on = generated_on or date.today()
    slug = re.sub(r"[^a-z0-9]+", "-", str(role).lower()).strip("-") or "role"
    return f"resumelens-report-{slug}-{generated_on.isoformat()}.pdf"


# ---------- styles and tables ----------


def _make_styles():
    body = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=SLATE)
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=NAVY
        ),
        "subtitle": ParagraphStyle("subtitle", spaceAfter=8, **body),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=1,
        ),
        "body": ParagraphStyle("body", spaceAfter=4, **body),
        "body_keep": ParagraphStyle("body_keep", spaceAfter=4, keepWithNext=1, **body),
        "bullet": ParagraphStyle("bullet", leftIndent=12, bulletIndent=2, spaceAfter=3, **body),
        "small": ParagraphStyle(
            "small", fontName="Helvetica", fontSize=8, leading=11, textColor=SLATE
        ),
        "cell": ParagraphStyle(
            "cell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=SLATE
        ),
        "cell_bold": ParagraphStyle(
            "cell_bold", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=NAVY
        ),
        "th": ParagraphStyle(
            "th", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=SLATE
        ),
        "value": ParagraphStyle(
            "value", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY
        ),
    }


def _data_table(rows, widths, has_header=True, extra_styles=()):
    """A bordered table. The first row is a navy header row when has_header is True."""
    table = Table(rows, colWidths=widths, repeatRows=1 if has_header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if has_header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    table.setStyle(TableStyle(commands + list(extra_styles)))
    return table


# ---------- sections ----------


def _header_section(styles, product_name, generated_on):
    notice = Table([[_paragraph(NOTICE, styles["small"])]], colWidths=[CONTENT_WIDTH])
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TINT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        _paragraph(product_name, styles["title"]),
        _paragraph(
            f"Resume analysis report  |  {generated_on.strftime('%d %B %Y')}",
            styles["subtitle"],
        ),
        notice,
    ]


def _summary_section(styles, skills_by_category, selected):
    total_skills = sum(len(skills) for skills in skills_by_category.values())
    cells = [
        [
            _paragraph("TARGET ROLE", styles["label"]),
            _paragraph(selected["role"], styles["value"]),
        ],
        [
            _paragraph("MATCH SCORE", styles["label"]),
            _paragraph(f"{selected['score']} / 100", styles["value"]),
            _paragraph(describe_score(selected["score"]), styles["small"]),
        ],
        [
            _paragraph("SKILLS FOUND", styles["label"]),
            _paragraph(str(total_skills), styles["value"]),
            _paragraph(f"in {len(skills_by_category)} categories", styles["small"]),
        ],
    ]
    widths = [CONTENT_WIDTH * 0.46, CONTENT_WIDTH * 0.27, CONTENT_WIDTH * 0.27]
    table = Table([cells], colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [_paragraph("Summary", styles["h2"]), table]


def _top_roles_section(styles, analyses):
    header = [
        _paragraph(text, styles["th"])
        for text in ("#", "Role", "Score", "Overlap", "Required", "Main gaps")
    ]
    rows = [header]
    for rank, item in enumerate(analyses[:TOP_ROLES_SHOWN], start=1):
        matched = len(item["required_matched"])
        total = matched + len(item["required_missing"])
        missing = item["required_missing"]
        gaps = _join(missing[:MAX_GAPS_SHOWN])
        if len(missing) > MAX_GAPS_SHOWN:
            gaps += " and more"
        rows.append(
            [
                _paragraph(str(rank), styles["cell"]),
                _paragraph(item["role"], styles["cell_bold"]),
                _paragraph(f"{item['score']} / 100", styles["cell"]),
                _paragraph(describe_score(item["score"]), styles["cell"]),
                _paragraph(f"{matched} of {total}", styles["cell"]),
                _paragraph(gaps, styles["cell"]),
            ]
        )
    widths = [8 * mm, 44 * mm, 20 * mm, 28 * mm, 20 * mm, 54 * mm]
    return [
        _paragraph("Top recommended roles", styles["h2"]),
        _data_table(rows, widths),
        Spacer(1, 4),
        _paragraph(
            "Roles are ranked by match score. A recommendation shows the closest "
            "overlap with the resume and is not a prediction of hiring outcomes.",
            styles["small"],
        ),
    ]


def _skills_found_section(styles, skills_by_category):
    flowables = [_paragraph("Skills found in the resume", styles["h2"])]
    if not any(skills_by_category.values()):
        flowables.append(
            _paragraph(
                "No skills from the dictionary were detected in the resume text.",
                styles["body"],
            )
        )
        return flowables

    rows = [[_paragraph("Category", styles["th"]), _paragraph("Skills", styles["th"])]]
    for category, skills in skills_by_category.items():
        rows.append(
            [
                _paragraph(category, styles["cell_bold"]),
                _paragraph(_join(skills), styles["cell"]),
            ]
        )
    flowables.append(_data_table(rows, [42 * mm, 132 * mm]))
    return flowables


def _skill_gap_section(styles, selected):
    rows = [
        ("Required skills found", _join(selected["required_matched"], "None found yet")),
        (
            "Required skills not found",
            _join(selected["required_missing"], "None. All required skills were found."),
        ),
        ("Bonus skills found", _join(selected["bonus_matched"], "None found yet")),
        (
            "Bonus skills not found",
            _join(selected["bonus_missing"], "None. All bonus skills were found."),
        ),
    ]
    table_rows = [
        [_paragraph(label, styles["cell_bold"]), _paragraph(text, styles["cell"])]
        for label, text in rows
    ]
    backgrounds = [
        ("BACKGROUND", (0, 0), (-1, 0), FOUND_BG),
        ("BACKGROUND", (0, 1), (-1, 1), MISSING_BG),
        ("BACKGROUND", (0, 2), (-1, 2), TINT),
        ("BACKGROUND", (0, 3), (-1, 3), NEUTRAL_BG),
    ]
    return [
        _paragraph(f"Skill gap for {selected['role']}", styles["h2"]),
        _data_table(table_rows, [48 * mm, 126 * mm], has_header=False, extra_styles=backgrounds),
        Spacer(1, 4),
        _paragraph(
            "'Not found' means the skill was not detected in the resume text. The "
            "person may have the skill but describe it differently or not list it.",
            styles["small"],
        ),
    ]


def _roadmap_section(styles, roadmap, role):
    flowables = [_paragraph(f"Learning roadmap for {role}", styles["h2"])]
    if not roadmap["items"]:
        flowables.append(
            _paragraph(
                f"No missing skills were found for {role}, so there is nothing to "
                "add to a roadmap.",
                styles["body"],
            )
        )
        return flowables

    hours = roadmap["total_weeks"] * roadmap["hours_per_week"]
    flowables.append(
        _paragraph(
            f"{len(roadmap['items'])} skills  |  about {roadmap['total_weeks']} weeks  |  "
            f"roughly {hours} hours at {roadmap['hours_per_week']} hours per week. "
            "These are rough estimates for a beginner.",
            styles["body_keep"],
        )
    )

    rows = [
        [
            _paragraph(text, styles["th"])
            for text in ("Step", "Skill", "Weeks", "Topics", "Practice project")
        ]
    ]
    for item in roadmap["items"]:
        if item["start_week"] == item["end_week"]:
            weeks = str(item["start_week"])
        else:
            weeks = f"{item['start_week']}-{item['end_week']}"
        rows.append(
            [
                _paragraph(str(item["order"]), styles["cell"]),
                [
                    _paragraph(item["skill"], styles["cell_bold"]),
                    _paragraph(f"{item['priority']} skill", styles["small"]),
                ],
                _paragraph(weeks, styles["cell"]),
                _paragraph(_join(item["topics"]), styles["cell"]),
                _paragraph(item["project"], styles["cell"]),
            ]
        )
    flowables.append(
        _data_table(rows, [11 * mm, 32 * mm, 15 * mm, 60 * mm, 56 * mm])
    )
    if roadmap["remaining"]:
        flowables.append(Spacer(1, 4))
        flowables.append(
            _paragraph(
                "Not in this plan yet: " + _join(roadmap["remaining"]) + ".",
                styles["small"],
            )
        )
    return flowables


def _how_to_read_section(styles):
    lines = [
        f"Match score = {REQUIRED_WEIGHT:.0%} x required-skill coverage + "
        f"{BONUS_WEIGHT:.0%} x bonus-skill coverage + {TEXT_WEIGHT:.0%} x wording "
        f"similarity (scaled so {SIMILARITY_CAP} or more counts as full marks).",
        "Skills are found by keyword matching against a curated dictionary, so "
        "synonyms and context can be missed.",
        "A missing keyword does not mean a missing ability.",
        "All required skills count equally, so a role can look stronger than it is.",
        "The report contains analysis results only. It does not include the resume "
        "text or personal details such as name, email or phone number.",
    ]
    flowables = [_paragraph("How to read this report", styles["h2"])]
    flowables += [
        Paragraph(escape(safe_text(line)), styles["bullet"], bulletText="-")
        for line in lines
    ]
    return flowables


# ---------- page decoration ----------


def _first_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INDIGO)
    canvas.rect(0, PAGE_HEIGHT - 6 * mm, PAGE_WIDTH, 6 * mm, fill=1, stroke=0)
    canvas.restoreState()
    _footer(canvas, doc)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(PAGE_MARGIN, 14 * mm, PAGE_WIDTH - PAGE_MARGIN, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawString(
        PAGE_MARGIN, 9.5 * mm, f"{PRODUCT_NAME}  |  For educational guidance only"
    )
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ---------- public function ----------


def build_report_pdf(
    skills_by_category, analyses, selected, roadmap, product_name=PRODUCT_NAME, generated_on=None
):
    """Build the analysis report and return it as PDF bytes.

    skills_by_category: {category: [skill, ...]} from group_by_category().
    analyses: best-first list from analyze_roles().
    selected: the analysis of the target role (one item of `analyses`).
    roadmap: the dictionary from build_roadmap(selected).

    The resume text is deliberately not a parameter.
    """
    generated_on = generated_on or date.today()
    styles = _make_styles()

    story = []
    story += _header_section(styles, product_name, generated_on)
    story += _summary_section(styles, skills_by_category, selected)
    story += _top_roles_section(styles, analyses)
    story += _skills_found_section(styles, skills_by_category)
    story += _skill_gap_section(styles, selected)
    story += _roadmap_section(styles, roadmap, selected["role"])
    story += _how_to_read_section(styles)

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title=f"{safe_text(product_name)} analysis report",
        author=safe_text(product_name),
        subject="Resume analysis for educational career guidance",
    )
    document.build(story, onFirstPage=_first_page, onLaterPages=_footer)
    return buffer.getvalue()