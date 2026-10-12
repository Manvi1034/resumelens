"""Job matching: load job roles, compare a resume with them using TF-IDF and
cosine similarity, and measure how many required skills were found.
"""

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skill_extractor import split_pipe
from text_cleaner import clean_text

JOB_ROLES_PATH = Path(__file__).resolve().parent / "data" / "job_roles.csv"

# A "word" starts with a letter or digit and may contain + # . - inside it,
# so c++, c#, node.js and scikit-learn stay in one piece. "/" separates words.
TOKEN_PATTERN = r"[a-z0-9][a-z0-9+#.\-]*"


def load_job_roles(csv_path=JOB_ROLES_PATH):
    """Read job_roles.csv and return a list of role dictionaries.

    Each role has: name, description, required_skills (list), bonus_skills (list).
    """
    table = pd.read_csv(csv_path)
    roles = []
    for _, row in table.iterrows():
        roles.append(
            {
                "name": row["role"].strip(),
                "description": row["description"].strip(),
                "required_skills": split_pipe(row["required_skills"]),
                "bonus_skills": split_pipe(row["bonus_skills"]),
            }
        )
    return roles


def get_role(role_name, roles=None):
    """Return one role by name. Raises ValueError if the name is unknown."""
    if roles is None:
        roles = load_job_roles()
    for role in roles:
        if role["name"] == role_name:
            return role
    raise ValueError(f"Unknown job role: {role_name}")


def build_role_document(role):
    """Combine a role's description and skills into one cleaned text."""
    parts = [role["description"]] + role["required_skills"] + role["bonus_skills"]
    return clean_text(" ".join(parts))


def create_vectorizer():
    """Create the TF-IDF vectorizer used for matching."""
    return TfidfVectorizer(
        token_pattern=TOKEN_PATTERN,
        ngram_range=(1, 2),  # single words and two-word phrases
        stop_words="english",  # ignore words like "the" and "and"
        sublinear_tf=True,  # repeating a word 20 times does not count 20x
    )


def rank_roles_by_text_similarity(cleaned_resume_text, roles=None):
    """Return every role with its text similarity (0 to 1), highest first."""
    if roles is None:
        roles = load_job_roles()
    if not cleaned_resume_text:
        return [{"role": role["name"], "similarity": 0.0} for role in roles]

    role_documents = [build_role_document(role) for role in roles]

    vectorizer = create_vectorizer()
    role_vectors = vectorizer.fit_transform(role_documents)  # learn vocabulary + IDF
    resume_vector = vectorizer.transform([cleaned_resume_text])  # reuse the vocabulary
    similarities = cosine_similarity(resume_vector, role_vectors)[0]

    results = [
        {"role": role["name"], "similarity": float(score)}
        for role, score in zip(roles, similarities)
    ]
    return sorted(results, key=lambda item: item["similarity"], reverse=True)


def calculate_skill_coverage(found_skills, role):
    """Compare found skills with a role's REQUIRED skills.

    coverage = matched required skills / total required skills.
    """
    found = set(found_skills)
    required = role["required_skills"]
    matched = [skill for skill in required if skill in found]
    missing = [skill for skill in required if skill not in found]
    coverage = len(matched) / len(required) if required else 0.0
    return {"matched": matched, "missing": missing, "coverage": coverage}


def compare_resume_to_roles(cleaned_resume_text, found_skills, roles=None):
    """Return one result per role with both measures, ranked by text similarity."""
    if roles is None:
        roles = load_job_roles()
    ranking = rank_roles_by_text_similarity(cleaned_resume_text, roles)
    role_by_name = {role["name"]: role for role in roles}

    results = []
    for item in ranking:
        coverage = calculate_skill_coverage(found_skills, role_by_name[item["role"]])
        results.append({**item, **coverage})
    return results




# ---------------------------------------------------------------------------
# Phase 8: transparent match score
#
# score = 100 x (REQUIRED_WEIGHT x required coverage
#              + BONUS_WEIGHT    x bonus coverage
#              + TEXT_WEIGHT     x scaled similarity)
# ---------------------------------------------------------------------------

REQUIRED_WEIGHT = 0.60  # core skills matter most
BONUS_WEIGHT = 0.15  # extra skills help a little
TEXT_WEIGHT = 0.25  # how closely the wording matches the role
SIMILARITY_CAP = 0.50  # a similarity of 0.50 or more counts as full marks


def scale_similarity(similarity):
    """Turn a raw similarity (0 to 1) into a 0 to 1 value, capped at SIMILARITY_CAP."""
    return min(max(similarity, 0.0), SIMILARITY_CAP) / SIMILARITY_CAP


def calculate_match_score(required_coverage, bonus_coverage, similarity):
    """Combine the three parts into a whole-number score from 0 to 100."""
    score = (
        REQUIRED_WEIGHT * required_coverage
        + BONUS_WEIGHT * bonus_coverage
        + TEXT_WEIGHT * scale_similarity(similarity)
    )
    return round(score * 100)


def describe_score(score):
    """Turn a score into a short, neutral label."""
    if score >= 75:
        return "Strong overlap"
    if score >= 50:
        return "Moderate overlap"
    if score >= 30:
        return "Limited overlap"
    return "Little overlap so far"


def split_found_and_missing(skills, found_skills):
    """Split a list of skills into (found, missing), keeping the original order."""
    found = set(found_skills)
    return (
        [skill for skill in skills if skill in found],
        [skill for skill in skills if skill not in found],
    )


def analyze_roles(cleaned_resume_text, found_skills, roles=None):
    """Return a full analysis for every role, ranked by match score (highest first)."""
    if roles is None:
        roles = load_job_roles()

    ranking = rank_roles_by_text_similarity(cleaned_resume_text, roles)
    similarity_by_role = {item["role"]: item["similarity"] for item in ranking}

    analyses = []
    for role in roles:
        required_matched, required_missing = split_found_and_missing(
            role["required_skills"], found_skills
        )
        bonus_matched, bonus_missing = split_found_and_missing(
            role["bonus_skills"], found_skills
        )

        required_total = len(role["required_skills"])
        bonus_total = len(role["bonus_skills"])
        required_coverage = len(required_matched) / required_total if required_total else 0.0
        bonus_coverage = len(bonus_matched) / bonus_total if bonus_total else 0.0
        similarity = similarity_by_role[role["name"]]

        analyses.append(
            {
                "role": role["name"],
                "score": calculate_match_score(
                    required_coverage, bonus_coverage, similarity
                ),
                "similarity": similarity,
                "required_coverage": required_coverage,
                "bonus_coverage": bonus_coverage,
                "required_matched": required_matched,
                "required_missing": required_missing,
                "bonus_matched": bonus_matched,
                "bonus_missing": bonus_missing,
            }
        )

    return sorted(
        analyses, key=lambda item: (item["score"], item["similarity"]), reverse=True
    )



# ---------------------------------------------------------------------------
# Phase 9: top-role recommendations with plain-language explanations
# ---------------------------------------------------------------------------

TOP_N_RECOMMENDATIONS = 3
MAX_GAPS_SHOWN = 4


def describe_wording_match(similarity):
    """Describe how closely the resume wording matches a role description."""
    scaled = scale_similarity(similarity)
    if scaled >= 0.6:
        return "Your resume wording closely matches this role's description."
    if scaled >= 0.3:
        return "Your resume wording partly overlaps with this role's description."
    return "Your resume wording is not very similar to this role's description."


def build_explanation(analysis):
    """Return a list of short sentences explaining one role's score."""
    matched = analysis["required_matched"]
    missing = analysis["required_missing"]
    total = len(matched) + len(missing)

    lines = []
    if matched:
        lines.append(
            f"You have {len(matched)} of {total} required skills: "
            f"{', '.join(matched)}."
        )
    else:
        lines.append(f"None of the {total} required skills were found yet.")

    if missing:
        shown = ", ".join(missing[:MAX_GAPS_SHOWN])
        more = " and more" if len(missing) > MAX_GAPS_SHOWN else ""
        lines.append(f"Main gaps: {shown}{more}.")
    else:
        lines.append("No required skills are missing.")

    lines.append(describe_wording_match(analysis["similarity"]))

    if analysis["bonus_matched"]:
        lines.append(
            "Bonus skills you already have: "
            f"{', '.join(analysis['bonus_matched'])}."
        )
    return lines


def recommend_roles(analyses, top_n=TOP_N_RECOMMENDATIONS):
    """Return the top roles from analyze_roles() with explanations."""
    recommendations = []
    for rank, analysis in enumerate(analyses[:top_n], start=1):
        recommendations.append(
            {
                "rank": rank,
                "role": analysis["role"],
                "score": analysis["score"],
                "label": describe_score(analysis["score"]),
                "explanation": build_explanation(analysis),
            }
        )
    return recommendations