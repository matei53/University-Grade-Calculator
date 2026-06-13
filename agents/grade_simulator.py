"""
Grade simulator agent powered by Ollama + LangGraph ReAct.
The agent receives pre-computed context, then uses tools to verify its math
before returning the final JSON result.
"""

import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from agents.tools import _get_api_client, get_current_grades

SYSTEM_PROMPT = """You are a university grade simulator agent.
You receive pre-computed context about a student's grades and a simulation target.

AVAILABLE TOOLS:
• get_current_grades — fetch detailed assessment-level grade data from the system.
  Use this if you need extra detail about a specific subject or assessment.
• verify_simulation — validate your proposed scores.
  Call it with a JSON string mapping assessment IDs (string keys) to proposed scores.
  Example: '{"2": 8.5, "3": 7.0}'
  It returns the resulting weighted average and a per-subject breakdown.
  ALWAYS call verify_simulation before finalising your answer.

FORMULA (used internally by verify_simulation):
  subject_grade = Σ [ (score / max_score) × (weight / 100) × subject_max_grade ]
  overall_avg   = Σ(subject_grade × credits) / Σ(credits of graded subjects only)

  IMPORTANT: the denominator only includes subjects that have at least one score.
  Do NOT exploit this by leaving subjects ungraded to inflate the average.
  A realistic simulation requires ALL ungraded assessments to receive a predicted score.

WORKFLOW:
1. Read the pre-computed context supplied by the user.
2. Identify every assessment marked "Available to change: YES".
3. Assign a predicted_score to EVERY such assessment (see Rules 1 and 2 below).
4. Call verify_simulation with ALL proposed scores.
5. If the returned average does not meet the target, adjust scores and call again (up to 3 times).
6. Once satisfied, output ONLY the final JSON — nothing else.

RULES:
1. UNGRADED ASSESSMENTS (Currently failing: NO GRADE) — MANDATORY.
   The context lists a "MANDATORY IDs" set — every ID in that list MUST appear in your
   output with a predicted_score. No exceptions, no partial coverage.
   Omitting any ID from that list makes your response invalid.

2. GRADED AVAILABLE ASSESSMENTS (Currently failing: YES or NO) — CONDITIONAL.
   Include in the output only if you are raising the score.
   Never lower a score below the current grade (no downgrade).

3. PASSING FLOORS — every predicted score must satisfy ALL three:
   a. predicted_score ≥ the assessment's "Min passing score".
   b. The resulting subject grade ≥ the subject's "Passing grade".
   c. predicted_score ≥ current grade if already graded (never downgrade).

4. SCORE STRATEGY — per the "Target status:" banner:
   • "TARGET NOT MET"      → set all ungraded to at least Min passing score first,
                              then raise available scores as needed to reach the target.
   • "TARGET ALREADY MET"  → set all ungraded to at least Min passing score;
                              do NOT raise already-passing graded assessments.
   • "TARGET IMPOSSIBLE"   → maximise all available assessments; set a non-empty message.
   • "NO AVAILABLE ASSESSMENTS" → return empty grades list with a non-empty message.

5. "message" must be "" unless the target is impossible or there are no assessments.
6. Use the student note (if provided) to distribute scores — lower for harder subjects.

OUTPUT — respond with ONLY a raw JSON object, no markdown, no code fences:
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
# Verify-simulation tool (defined here so it can access the formula helpers)
# ---------------------------------------------------------------------------


@tool
def verify_simulation(proposed_scores_json: str) -> str:
    """
    Compute the weighted average resulting from a proposed set of scores.

    Args:
        proposed_scores_json: JSON string mapping assessment_id (string key) to
            proposed score (number). Example: '{"1": 8.5, "3": 7.0}'

    Returns the overall weighted average and a per-subject grade breakdown,
    or an error message if the input is invalid.
    """
    try:
        raw = json.loads(proposed_scores_json)
        proposed = {int(k): float(v) for k, v in raw.items()}
    except Exception as e:
        return f"Invalid input — expected a JSON object with string keys: {e}"

    try:
        years_data = _get_api_client().get_academic_years()
    except Exception as e:
        return f"Error fetching grades: {e}"

    total_points = 0.0
    total_credits = 0.0
    lines: list[str] = []

    for year in years_data:
        for subject in year.get("subjects", []):
            credits = float(subject.get("credit_value", 0))
            max_grade = float(subject.get("max_grade", 10.0))
            passing_grade = float(subject.get("passing_grade", 5.0))
            grade = 0.0
            has_score = False

            for a in subject.get("assessments", []):
                a_id = a.get("id")
                weight = float(a.get("weight", 0))
                max_score = float(a.get("max_score", 10.0))
                grade_obj = a.get("grade")
                score: Optional[float] = None
                if grade_obj is not None and grade_obj.get("score") is not None:
                    score = float(grade_obj["score"])
                if a_id in proposed:
                    score = proposed[a_id]
                if score is not None:
                    has_score = True
                    grade += (score / max_score) * (weight / 100.0) * max_grade

            if has_score:
                total_points += grade * credits
                total_credits += credits
                status = "PASS" if grade >= passing_grade else "FAIL"
                lines.append(f"  {subject.get('name', '?')}: {grade:.2f}/{max_grade} ({status})")

    if total_credits == 0:
        return "No graded subjects found after applying proposed scores."

    overall = total_points / total_credits
    return f"Weighted average: {overall:.2f}\n" + "\n".join(lines)


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

    # Collect every ungraded available assessment ID — these are mandatory predictions.
    mandatory_ids: list[int] = []
    for year in years_data:
        for subject in year.get("subjects", []):
            for a in subject.get("assessments", []):
                a_id = a.get("id")
                if a_id not in available_ids:
                    continue
                grade_obj = a.get("grade")
                if grade_obj is None or grade_obj.get("score") is None:
                    mandatory_ids.append(a_id)

    if mandatory_ids:
        lines.append("")
        lines.append(
            f"  MANDATORY IDs (ungraded + available — ALL must appear in your output): "
            f"{mandatory_ids}"
        )
        lines.append(
            "  Your response is INVALID if any of these IDs are absent from the grades list."
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
    Run the grade simulator ReAct agent.

    The agent receives pre-computed context, then uses get_current_grades and
    verify_simulation as tools to reason about and verify its proposed scores.

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

    # Compute mandatory IDs once so Python can enforce coverage regardless of LLM behaviour.
    available_ids = set(assessment_ids)
    mandatory_ids: set[int] = set()
    for _year in years_data:
        for _subj in _year.get("subjects", []):
            for _a in _subj.get("assessments", []):
                _aid = _a.get("id")
                if _aid not in available_ids:
                    continue
                _grade = _a.get("grade")
                if _grade is None or _grade.get("score") is None:
                    mandatory_ids.add(_aid)

    llm = ChatOllama(model="llama3.2", temperature=0)
    agent = create_react_agent(llm, [get_current_grades, verify_simulation])
    data_message = _build_data_prompt(target, year_label, user_note, assessment_ids, years_data)

    def _first_final_message(messages: list) -> Optional[str]:
        """Return the content of the last AI message that has no pending tool calls."""
        for msg in reversed(messages):
            content = getattr(msg, "content", "")
            if content and not getattr(msg, "tool_calls", []):
                return content
        return None

    def _normalize(parsed: dict) -> dict:
        """Coerce assessment_id to int and predicted_score to float."""
        for entry in parsed.get("grades", []):
            try:
                entry["assessment_id"] = int(entry["assessment_id"])
            except (TypeError, ValueError, KeyError):
                pass
            try:
                entry["predicted_score"] = float(entry["predicted_score"])
            except (TypeError, ValueError, KeyError):
                pass
        return parsed

    def _missing_mandatory(parsed: dict) -> list[int]:
        predicted = set()
        for entry in parsed.get("grades", []):
            try:
                predicted.add(int(entry.get("assessment_id")))
            except (TypeError, ValueError):
                pass
        return sorted(mandatory_ids - predicted)

    def _fill_mandatory(parsed: dict) -> dict:
        """Add placeholder entries for any still-missing mandatory IDs."""
        still_missing = _missing_mandatory(parsed)
        if not still_missing:
            return parsed
        scores = [
            e["predicted_score"]
            for e in parsed.get("grades", [])
            if isinstance(e.get("predicted_score"), (int, float))
        ]
        fill = round(sum(scores) / len(scores), 1) if scores else min(round(target, 1), 10.0)
        for aid in still_missing:
            parsed.setdefault("grades", []).append(
                {"assessment_id": aid, "predicted_score": fill}
            )
        return parsed

    try:
        result = agent.invoke({
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=data_message),
            ]
        })
        all_messages = result.get("messages", [])
        content = _first_final_message(all_messages)

        if content is not None:
            parsed = _extract_json(content)
            if parsed is not None:
                parsed = _normalize(parsed)
                missing = _missing_mandatory(parsed)
                if missing:
                    # Targeted retry naming exactly which IDs were skipped.
                    retry_result = agent.invoke({
                        "messages": all_messages + [
                            HumanMessage(content=(
                                f"Your response is missing MANDATORY assessment IDs: {missing}. "
                                f"Every ungraded assessment in that list MUST appear in the grades array. "
                                f"Output the complete JSON again with ALL missing IDs included."
                            ))
                        ]
                    })
                    retry_content = _first_final_message(retry_result.get("messages", []))
                    if retry_content is not None:
                        retry_parsed = _extract_json(retry_content)
                        if retry_parsed is not None:
                            return _fill_mandatory(_normalize(retry_parsed))
                return _fill_mandatory(parsed)

            # Retry: the agent returned text but not valid JSON
            retry_result = agent.invoke({
                "messages": all_messages + [
                    HumanMessage(content=(
                        "Your previous response was not valid JSON. "
                        "Respond with ONLY the raw JSON object and no other text."
                    ))
                ]
            })
            retry_content = _first_final_message(retry_result.get("messages", []))
            if retry_content is not None:
                retry_parsed = _extract_json(retry_content)
                if retry_parsed is not None:
                    return _fill_mandatory(_normalize(retry_parsed))

        # Complete failure — build a minimal result from mandatory IDs if possible.
        if mandatory_ids:
            fill = min(round(target, 1), 10.0)
            return {
                "grades": [
                    {"assessment_id": aid, "predicted_score": fill}
                    for aid in sorted(mandatory_ids)
                ],
                "message": "",
            }
        return fallback

    except Exception as e:
        return {"grades": [], "message": f"Error running simulation: {e}"}
