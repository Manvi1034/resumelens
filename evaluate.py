"""Run every sample resume through the real pipeline and write the testing sheet.

    python evaluate.py

Reads the expected answers from tests/test_cases.csv and writes the results to
tests/evaluation_results.csv.
"""

import csv
from pathlib import Path

from job_matcher import analyze_roles
from resume_parser import ResumeParseError, extract_resume_text
from skill_extractor import extract_skills, load_skill_dictionary
from text_cleaner import clean_text

ROOT = Path(__file__).resolve().parent
SAMPLE_FOLDER = ROOT / "sample_resumes"
TEST_CASES_PATH = ROOT / "tests" / "test_cases.csv"
RESULTS_PATH = ROOT / "tests" / "evaluation_results.csv"
FORMATS = (".docx", ".pdf")


def analyze_resume(filename, data, dictionary=None):
    """Run the whole pipeline on one file and return every intermediate result."""
    text = extract_resume_text(filename, data)
    cleaned = clean_text(text)
    if dictionary is None:
        dictionary = load_skill_dictionary()
    skills = extract_skills(cleaned, dictionary)
    return {
        "text": text,
        "cleaned": cleaned,
        "skills": skills,
        "analyses": analyze_roles(cleaned, skills),
    }


def precision_recall(found, truth):
    """Skill precision (listed skills that are real) and recall (real skills found)."""
    found, truth = set(found), set(truth)
    correct = found & truth
    precision = len(correct) / len(found) if found else 1.0
    recall = len(correct) / len(truth) if truth else 1.0
    return precision, recall


def load_test_cases(path=TEST_CASES_PATH):
    with open(path, newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    for case in cases:
        case["true_skills"] = [s for s in case["true_skills"].split("|") if s]
    return cases


def evaluate_file(case, path, dictionary):
    row = {
        "Test Resume": path.stem,
        "Format": path.suffix.lstrip(".").upper(),
        "Expected Top Role": case["expected_top_role"],
        "Comments": case["notes"],
    }
    try:
        result = analyze_resume(path.name, path.read_bytes(), dictionary)
    except ResumeParseError as error:
        row.update(
            {"Actual Top Role": "ERROR", "Top Score": "", "Role Check": "FAIL",
             "Skill Precision": "", "Skill Recall": "", "False Positives": "",
             "Missed Skills": "", "Comments": f"{case['notes']} | {error}"}
        )
        return row

    best = result["analyses"][0]
    precision, recall = precision_recall(result["skills"], case["true_skills"])
    expected = case["expected_top_role"]
    if expected == "ANY":
        role_check = "n/a"
    else:
        role_check = "PASS" if best["role"] == expected else "FAIL"
    row.update(
        {
            "Actual Top Role": best["role"],
            "Top Score": best["score"],
            "Role Check": role_check,
            "Skill Precision": round(precision, 2),
            "Skill Recall": round(recall, 2),
            "False Positives": ", ".join(sorted(set(result["skills"]) - set(case["true_skills"]))),
            "Missed Skills": ", ".join(sorted(set(case["true_skills"]) - set(result["skills"]))),
        }
    )
    return row


def main():
    dictionary = load_skill_dictionary()
    rows = []
    for case in load_test_cases():
        for extension in FORMATS:
            path = SAMPLE_FOLDER / f"{case['resume']}{extension}"
            if path.exists():
                rows.append(evaluate_file(case, path, dictionary))

    columns = [
        "Test Resume", "Format", "Expected Top Role", "Actual Top Role", "Top Score",
        "Role Check", "Skill Precision", "Skill Recall", "False Positives",
        "Missed Skills", "Comments",
    ]
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'Resume':<24}{'Fmt':<6}{'Expected':<27}{'Actual':<27}{'Score':<7}{'Role':<6}{'Prec':<6}{'Rec':<6}")
    for row in rows:
        print(
            f"{row['Test Resume']:<24}{row['Format']:<6}{row['Expected Top Role']:<27}"
            f"{str(row['Actual Top Role']):<27}{str(row['Top Score']):<7}{row['Role Check']:<6}"
            f"{str(row['Skill Precision']):<6}{str(row['Skill Recall']):<6}"
        )
        if row["False Positives"]:
            print(f"    false positives: {row['False Positives']}")
        if row["Missed Skills"]:
            print(f"    missed skills:   {row['Missed Skills']}")

    checked = [r for r in rows if r["Role Check"] in ("PASS", "FAIL")]
    scored = [r for r in rows if r["Skill Precision"] != ""]
    if checked:
        passed = sum(r["Role Check"] == "PASS" for r in checked)
        print(f"\nRole check: {passed}/{len(checked)} passed")
    if scored:
        print(f"Average skill precision: {sum(r['Skill Precision'] for r in scored) / len(scored):.2f}")
        print(f"Average skill recall:    {sum(r['Skill Recall'] for r in scored) / len(scored):.2f}")
    print(f"\nWrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()