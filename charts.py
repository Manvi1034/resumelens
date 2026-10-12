"""Plotly charts for the dashboard."""

import plotly.graph_objects as go

INDIGO = "#4F46E5"
MUTED = "#C9CEE0"
NAVY = "#1B2559"
GRID = "#E9ECF5"
GREEN = "#1F8A5B"
RED = "#C94444"


def role_scores_chart(analyses, highlight=3):
    """Horizontal bars of every role's match score, with the top roles in indigo.

    `analyses` is the best-first list from analyze_roles().
    """
    ordered = list(reversed(analyses))  # horizontal bars draw bottom-up
    roles = [item["role"] for item in ordered]
    scores = [item["score"] for item in ordered]
    colours = [
        INDIGO if index >= len(ordered) - highlight else MUTED
        for index in range(len(ordered))
    ]

    figure = go.Figure(
        go.Bar(
            x=scores,
            y=roles,
            orientation="h",
            marker=dict(color=colours),
            text=scores,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x} / 100<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=44 * len(roles) + 90,
        margin=dict(l=0, r=30, t=10, b=0),
        font=dict(color=NAVY),
        showlegend=False,
        xaxis=dict(
            range=[0, 100],
            title="Match score (out of 100)",
            gridcolor=GRID,
            zeroline=False,
        ),
        yaxis=dict(title=None),
    )
    return figure


def _count_axis(largest):
    """Whole-number x-axis that leaves room for labels at the end of the bars."""
    axis = dict(
        range=[0, largest + 1],
        tickformat="d",
        gridcolor=GRID,
        zeroline=False,
    )
    if largest <= 10:
        axis["dtick"] = 1
    return axis


def skills_by_category_chart(skills_by_category):
    """Horizontal bars: how many skills were found in each category.

    `skills_by_category` is {category: [skill, ...]} from group_by_category().
    The category with the most skills is drawn at the top.
    """
    items = sorted(skills_by_category.items(), key=lambda item: len(item[1]))
    categories = [name for name, _ in items]
    counts = [len(skills) for _, skills in items]

    figure = go.Figure(
        go.Bar(
            x=counts,
            y=categories,
            orientation="h",
            marker=dict(color=INDIGO),
            text=counts,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x} skills<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=40 * max(len(categories), 1) + 70,
        margin=dict(l=0, r=30, t=10, b=0),
        font=dict(color=NAVY),
        showlegend=False,
        xaxis=dict(title="Skills found", **_count_axis(max(counts, default=0))),
        yaxis=dict(title=None),
    )
    return figure


def skill_coverage_chart(selected):
    """Stacked bars: skills found vs not found, for required and bonus skills.

    `selected` is one role's analysis from analyze_roles().
    """
    groups = ["Bonus skills", "Required skills"]  # drawn bottom to top
    found = [len(selected["bonus_matched"]), len(selected["required_matched"])]
    missing = [len(selected["bonus_missing"]), len(selected["required_missing"])]

    figure = go.Figure()
    for name, values, colour in (("Found", found, GREEN), ("Not found", missing, RED)):
        figure.add_bar(
            name=name,
            x=values,
            y=groups,
            orientation="h",
            marker=dict(color=colour),
            text=[str(value) if value else "" for value in values],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#FFFFFF", size=14),
            hovertemplate="%{y}: %{x} " + name.lower() + "<extra></extra>",
        )
    largest = max(
        found[0] + missing[0], found[1] + missing[1], 1
    )
    figure.update_layout(
        template="plotly_white",
        barmode="stack",
        height=220,
        margin=dict(l=0, r=10, t=10, b=0),
        font=dict(color=NAVY),
        legend=dict(orientation="h", x=0, y=1.25, traceorder="normal"),        xaxis=dict(title="Number of skills", **_count_axis(largest)),
        yaxis=dict(title=None),
    )
    return figure