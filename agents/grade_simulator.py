"""
Grade simulator agent powered by Ollama and LangGraph ReAct.
Pre-computes feasibility in Python; the agent distributes scores intelligently.
"""

import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from agents.tools import _get_api_client, get_current_grades

SYSTEM_PROMPT = """You are a university grade simulator. \
Assign predicted scores to assessments marked "Available to change: YES".

EXACT FORMULA (must match the application):
  Step 1 — subject grade:
    subject_grade = Σ [ (score / max_score) × (weight / 100) × subject_max_grade ]
    Count ONLY assessments that have a score (existing grade OR your predicted score).

  Step 2 — a subject is "graded" if it has at least one scored assessment.

  Step 3 — overall weighted average:
    overall_avg = Σ(subject_grade × credits) / Σ(credits)
    Both sums are over GRADED subjects ONLY (subjects with ≥1 scored assessment).

RULES — apply ALL of the following in order:

1. SCOPE — only assign predicted_score to assessments marked "Available to change: YES".

2. PASSING FLOORS — every predicted score must satisfy ALL three:
   a. predicted_score ≥ the assessment's "Min passing score".
   b. The resulting subject grade ≥ the subject's "Passing grade".
   c. predicted_score ≥ current grade if the assessment already has one \
(never suggest a retake score below what the student already has).

3. WHAT TO CHANGE — determined by the "Target status:" line in the data:
   • "TARGET ALREADY MET" → ONLY assign predicted scores to assessments where \
"Currently failing: YES" or "Currently failing: NO GRADE (ungraded)", \
or whose subject has "Subject passing: FAILING" or "Subject passing: NO GRADES YET". \
Do NOT touch assessments that are passing.
   • "TARGET NOT MET" → treat assessments marked "Currently failing: YES" OR \
"Currently failing: NO GRADE (ungraded)" as the first priority (raise to at \
least their Min passing score), then raise further available assessments as \
needed to reach the target. Prioritise lowest-weight assessments first.

4. SPECIAL CASES (see data prompt banner):
   • IMPOSSIBLE target → use the stated maximum as effective target; \
set a non-empty "message" explaining the adjustment.
   • NO AVAILABLE ASSESSMENTS → return empty grades list with a non-empty "message".
   • Otherwise "message" must be an empty string "".

5. Use the student's note (if provided) to distribute scores — lower for difficult \
subjects, higher for expected strengths.

OUTPUT — respond with ONLY a raw JSON object. No markdown, no code fences, no extra text.
{"grades": [{"assessment_id": <int>, "predicted_score": <float>}, ...], "message": ""}"""


# ---------------------------------------------------------------------------
# Formula helpers — mirror DashboardService exactly
# ---------------------------------------------------------------------------


def _compute_subject_grade(
    subject: dict,
    available_ids: set,
    available_score: Optional[float],
) -> tuple[float, bool]:
    """
    Compute a subject's grade value and whether it has any scored assessment.

    available_ids: set of assessment IDs that are "available to change".
    available_score: score to assign to available assessments, or None to skip them.
    """
    max_grade = float(subject.get("max_grade", 10.0))
    grade = 0.0
    has_score = False

    for a in subject.get("assessments", []):
        a_id = a.get("id")
        weight = float(a.get("weight", 0))
        max_score_a = float(a.get("max_score", 10.0))
        grade_obj = a.get("grade")

        score: Optional[float] = None
        if grade_obj is not None and grade_obj.get("score") is not None:
            score = float(grade_obj["score"])

        if a_id in available_ids:
            score = available_score  # None → skip; float → override

        if score is not None:
            has_score = True
            normalized = score / max_score_a if max_score_a > 0 else 0.0
            grade += normalized * (weight / 100.0) * max_grade

    return grade, has_score


def _compute_weighted_average(
    years_data: list[dict],
    available_ids: set,
    available_score: Optional[float],
) -> Optional[float]:
    """
    Compute the overall weighted average using the app's exact formula.

    available_score=None  → available assessments are skipped (fixed grades only).
    available_score=float → all available assessments are assigned that score.

    Returns None when no subject ends up with any scored assessment.
    """
    total_points = 0.0
    total_credits = 0.0

    for year in years_data:
        for subject in year.get("subjects", []):
            credits = float(subject.get("credit_value", 0))
            grade, has_score = _compute_subject_grade(subject, available_ids, available_score)
            if has_score:
                total_points += grade * credits
                total_credits += credits

    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_data_prompt(  # noqa: C901
    target: float,
    year_label: str,
    user_note: str,
    assessment_ids: list[int],
    years_data: list[dict],
) -> str:
    """Build the structured plain-text data message for the agent."""
    available_ids = set(assessment_ids)

    # actual_avg counts all existing scores (including retakeable ones)
    actual_avg = _compute_weighted_average(years_data, set(), None)
    # current_avg skips available assessments (fixed grades only)
    current_avg = _compute_weighted_average(years_data, available_ids, None)
    max_avg = _compute_weighted_average(years_data, available_ids, 10.0)
    min_avg = _compute_weighted_average(years_data, available_ids, 1.0)

    target_already_met = actual_avg is not None and actual_avg >= target

    lines: list[str] = [
        f"Target average: {target}/10",
        f"Scope: {year_label}",
    ]
    if user_note.strip():
        lines.append(f"Student note: {user_note.strip()}")

    lines.append("")
    lines.append("Pre-computed averages (Python-verified — use these for math):")
    lines.append(
        f"  Actual current average (all existing grades): "
        f"{f'{actual_avg:.2f}' if actual_avg is not None else 'N/A (no grades yet)'}"
    )
    lines.append(
        f"  Baseline average (fixed grades only, excl. available): "
        f"{f'{current_avg:.2f}' if current_avg is not None else 'N/A'}"
    )
    lines.append(
        f"  Maximum achievable (all available = 10.0): "
        f"{f'{max_avg:.2f}' if max_avg is not None else 'N/A'}"
    )
    lines.append(
        f"  Minimum achievable (all available =  1.0): "
        f"{f'{min_avg:.2f}' if min_avg is not None else 'N/A'}"
    )

    if not available_ids:
        lines.append(
            "  Target status: NO AVAILABLE ASSESSMENTS — "
            "return empty grades list with a non-empty message."
        )
    elif target_already_met:
        lines.append(
            f"  Target status: TARGET ALREADY MET "
            f"(actual {actual_avg:.2f} ≥ target {target:.2f}). "
            f"Only fix FAILING or ungraded assessments/subjects. "
            f"Do NOT change passing assessments."
        )
    elif max_avg is not None and target > max_avg:
        lines.append(
            f"  Target status: TARGET IMPOSSIBLE "
            f"(max achievable {max_avg:.2f} < target {target:.2f}). "
            f"Use {max_avg:.2f} as effective target and set a non-empty message."
        )
    else:
        lines.append(
            f"  Target status: TARGET NOT MET "
            f"(current {f'{actual_avg:.2f}' if actual_avg is not None else 'N/A (no grades yet)'} "
            f"< target {target:.2f}). "
            f"Assign predicted scores to available assessments to reach the target."
        )

    lines.append("")
    lines.append("Academic data:")

    for year in years_data:
        year_lbl = year.get("label") or f"Year {year.get('order_index', '?')}"
        lines.append(f"\n  [{year_lbl}]")
        subjects = year.get("subjects", [])
        if not subjects:
            lines.append("    (no subjects)")
            continue

        for subject in subjects:
            credits = subject.get("credit_value", 0)
            max_grade = float(subject.get("max_grade", 10.0))
            passing_grade = float(subject.get("passing_grade", 5.0))

            # Current subject grade from all existing scores (regardless of available_ids)
            subj_grade, subj_has_score = _compute_subject_grade(subject, set(), None)
            if not subj_has_score:
                subj_passing_str = "NO GRADES YET"
            elif subj_grade >= passing_grade:
                subj_passing_str = "YES"
            else:
                subj_passing_str = "FAILING"

            lines.append(
                f"  Subject: {subject.get('name', 'Unknown')} | "
                f"Credits: {credits} | Max grade: {max_grade} | "
                f"Passing grade: {passing_grade} | "
                f"Current subject grade: {f'{subj_grade:.2f}' if subj_has_score else 'N/A'} | "
                f"Subject passing: {subj_passing_str}"
            )

            assessments = subject.get("assessments", [])
            if not assessments:
                lines.append("    (no assessments)")
                continue

            for a in assessments:
                a_id = a.get("id")
                weight = a.get("weight", 0)
                max_score = float(a.get("max_score", 10.0))
                grade_obj = a.get("grade")
                score: Optional[float] = None
                if grade_obj is not None and grade_obj.get("score") is not None:
                    score = float(grade_obj["score"])

                available = "YES" if a_id in available_ids else "NO"
                grade_str = str(score) if score is not None else "no grade"
                min_passing = round((passing_grade / max_grade) * max_score, 2)

                if score is None:
                    failing_str = "NO GRADE (ungraded)"
                elif score < min_passing:
                    failing_str = "YES"
                else:
                    failing_str = "NO"

                lines.append(
                    f"    - Assessment ID {a_id}: {a.get('name', 'Assessment')} | "
                    f"Weight: {weight}% | Max score: {max_score} | "
                    f"Min passing score: {min_passing} | "
                    f"Current grade: {grade_str} | "
                    f"Currently failing: {failing_str} | "
                    f"Available to change: {available}"
                )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> Optional[dict]:
    """Extract and parse the first valid JSON object from agent output."""
    text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    # Strip markdown fences
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            pass
    # Find any {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _last_content(messages: list) -> str:
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, tuple):
        return last[1]
    if hasattr(last, "content"):
        return last.content
    return str(last)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_simulation(
    target: float,
    user_note: str = "",
    assessment_ids: Optional[list[int]] = None,
    year_id: Optional[int] = None,
    years_data: Optional[list[dict]] = None,
    year_label: str = "All Years",
) -> dict:
    """
    Run the grade simulator agent.

    Returns:
        {"grades": [{"assessment_id": int, "predicted_score": float}, ...],
         "message": str}
    """
    fallback: dict = {
        "grades": [],
        "message": "The agent failed to return a valid response.",
    }

    if assessment_ids is None:
        assessment_ids = []

    if years_data is None:
        try:
            client = _get_api_client()
            years_data = client.get_academic_years()
            if year_id is not None:
                years_data = [y for y in years_data if y.get("id") == year_id]
        except Exception as e:
            return {"grades": [], "message": f"Error fetching data: {e}"}

    llm = ChatOllama(model="llama3.2", temperature=0)
    tools = [get_current_grades]
    agent = create_react_agent(llm, tools, prompt=SystemMessage(content=SYSTEM_PROMPT))

    data_message = _build_data_prompt(target, year_label, user_note, assessment_ids, years_data)

    try:
        result = agent.invoke({"messages": [HumanMessage(content=data_message)]})
        all_messages = result.get("messages", [])
        parsed = _extract_json(_last_content(all_messages))
        if parsed is not None:
            return parsed

        # Retry: include full conversation so the agent has context
        retry_result = agent.invoke(
            {
                "messages": all_messages
                + [
                    HumanMessage(
                        content=(
                            "Your previous response was not valid JSON. "
                            "Respond with ONLY the raw JSON object and no other text."
                        )
                    )
                ]
            }
        )
        retry_parsed = _extract_json(_last_content(retry_result.get("messages", [])))
        if retry_parsed is not None:
            return retry_parsed

        return fallback

    except Exception as e:
        return {"grades": [], "message": f"Error running simulation: {e}"}
