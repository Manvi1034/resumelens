"""Roadmap generation: turn a role's missing skills into a rule-based learning plan.

Rules:
1. Required skills come before bonus skills.
2. Within a group, skills are sorted by stage (1 foundations ... 5 applied).
3. The plan is capped at MAX_ROADMAP_ITEMS skills and padded with bonus skills
   up to MIN_ROADMAP_ITEMS so a short list of gaps still gives a useful plan.
4. Skills are scheduled one after another, using each skill's `weeks` value.
"""

import math
from pathlib import Path

import pandas as pd

from skill_extractor import split_pipe

LEARNING_RESOURCES_PATH = (
    Path(__file__).resolve().parent / "data" / "learning_resources.csv"
)

MIN_ROADMAP_ITEMS = 3
MAX_ROADMAP_ITEMS = 6
HOURS_PER_WEEK = 8  # planning assumption, shown to the student in the app


def load_learning_resources(csv_path=LEARNING_RESOURCES_PATH):
    """Read learning_resources.csv into {skill: {stage, weeks, topics, project}}."""
    table = pd.read_csv(csv_path)
    resources = {}
    for _, row in table.iterrows():
        resources[row["skill"].strip()] = {
            "stage": int(row["stage"]),
            "weeks": int(row["weeks"]),
            "topics": split_pipe(row["topics"]),
            "project": row["practice_project"].strip(),
        }
    return resources


def get_learning_info(skill, resources):
    """Return the learning info for a skill, or a generic plan if it has none."""
    if skill in resources:
        return resources[skill]
    return {
        "stage": 3,
        "weeks": 1,
        "topics": [
            "Core concepts and vocabulary",
            "A beginner tutorial from the official documentation",
        ],
        "project": f"Build a small project that uses {skill}",
    }


def order_for_learning(skills, resources):
    """Sort skills by stage. Skills in the same stage keep their original order."""
    positions = {skill: index for index, skill in enumerate(skills)}
    return sorted(
        skills,
        key=lambda skill: (get_learning_info(skill, resources)["stage"], positions[skill]),
    )


def select_roadmap_skills(required_missing, bonus_missing, resources, max_items, min_items):
    """Choose which skills go into the plan and label each Required or Bonus."""
    required = order_for_learning(required_missing, resources)[:max_items]
    bonus = order_for_learning(bonus_missing, resources)

    chosen = [(skill, "Required") for skill in required]
    room = max(min_items - len(chosen), 0)
    chosen += [(skill, "Bonus") for skill in bonus[:room]]
    return chosen


def weekly_focus(topics, weeks, project):
    """Split a skill's topics across its weeks. The last week adds the project."""
    size = max(1, math.ceil(len(topics) / weeks))
    entries = []
    for index in range(weeks):
        chunk = topics[index * size:(index + 1) * size]
        text = ", ".join(chunk) if chunk else "Revise and practise"
        if index == weeks - 1:
            text += f". Practice project: {project}"
        entries.append(text)
    return entries


def build_roadmap(
    analysis,
    resources=None,
    max_items=MAX_ROADMAP_ITEMS,
    min_items=MIN_ROADMAP_ITEMS,
    hours_per_week=HOURS_PER_WEEK,
):
    """Build a learning roadmap from one role's analysis (from analyze_roles)."""
    if resources is None:
        resources = load_learning_resources()

    chosen = select_roadmap_skills(
        analysis["required_missing"],
        analysis["bonus_missing"],
        resources,
        max_items,
        min_items,
    )

    items = []
    weekly_plan = []
    weeks_used = 0
    for order, (skill, priority) in enumerate(chosen, start=1):
        info = get_learning_info(skill, resources)
        start_week = weeks_used + 1
        end_week = weeks_used + info["weeks"]

        focus_per_week = weekly_focus(info["topics"], info["weeks"], info["project"])
        for offset, focus in enumerate(focus_per_week):
            weekly_plan.append(
                {"week": start_week + offset, "skill": skill, "focus": focus}
            )

        items.append(
            {
                "order": order,
                "skill": skill,
                "priority": priority,
                "stage": info["stage"],
                "weeks": info["weeks"],
                "start_week": start_week,
                "end_week": end_week,
                "topics": info["topics"],
                "project": info["project"],
            }
        )
        weeks_used = end_week

    chosen_skills = {skill for skill, _ in chosen}
    remaining = [
        skill
        for skill in analysis["required_missing"] + analysis["bonus_missing"]
        if skill not in chosen_skills
    ]

    return {
        "role": analysis["role"],
        "items": items,
        "weekly_plan": weekly_plan,
        "total_weeks": weeks_used,
        "hours_per_week": hours_per_week,
        "remaining": remaining,
    }