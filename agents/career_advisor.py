"""
Career guidance agent — runs locally via ChatOllama, mirroring grade_simulator.py.
Field-agnostic: works for any university programme, not just computer science.
"""

from typing import Any, Dict

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None
    SystemMessage = None
    HumanMessage = None


SYSTEM_PROMPT = (
    "You are an expert Academic and Career Advisor for university students. "
    "You will receive a student's academic history — their subjects, grades, and field of study. "
    "Analyse their strengths and areas of interest based solely on what is shown. "
    "Do NOT assume a specific field (e.g. do not default to computer science). "
    "Tailor every recommendation — career paths, electives, and advice — to the actual "
    "subjects and performance visible in the data. "
    "Provide: 1) Top 3 career paths suited to this student's profile, "
    "2) Elective or optional course types to consider next semester, "
    "3) A short motivational paragraph. "
    "Format your response in Markdown with clear headings."
)


def _format_student_data(student_data: Dict[str, Any]) -> str:
    import json

    try:
        return json.dumps(student_data, indent=2)
    except Exception:
        return str(student_data)


def generate_career_guidance(student_data: Dict[str, Any]) -> str:
    """Generate Markdown career guidance from a student_data dict.

    student_data should have a 'years' key containing the academic years list
    as returned by the API (subjects, assessments, grades).
    """
    if ChatOllama is not None:
        try:
            model = ChatOllama(model="llama3.2", temperature=0)
            user_content = (
                "Student academic history (JSON):\n```json\n"
                + _format_student_data(student_data)
                + "\n```\n\n"
                "Produce the advice in Markdown with exactly these sections:\n"
                "- **Strengths:** bullet list derived from the actual subjects and grades\n"
                "- **Top 3 Career Paths:** numbered list, 1-2 sentences each\n"
                "- **Recommended Electives:** bullet list of course types or topics\n"
                "- **Motivational Advice:** one short paragraph\n"
            )
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]
            result = model.generate([messages])
            try:
                text = result.generations[0][0].text
                if text:
                    return text
            except Exception:
                out = model(messages)
                if hasattr(out, "content"):
                    return out.content
        except Exception as e:
            return (
                "**Career Advisor unavailable**\n\n"
                f"The career guidance model could not be reached: {e}\n\n"
                "Please try again later."
            )

    # Fallback: field-agnostic rule-based guidance when LLM is unavailable
    try:
        subjects = []
        for y in student_data.get("years", []):
            for s in y.get("subjects", []):
                subjects.append(s)

        strong_subjects = []
        for s in subjects:
            assessments = s.get("assessments", [])
            if assessments:
                scores = [
                    float(a["grade_score"]) for a in assessments if a.get("grade_score") is not None
                ]
                if scores and (sum(scores) / len(scores)) >= 7.0:
                    strong_subjects.append(s.get("name", "Unknown"))

        strengths = [f"Strong performance in {n}" for n in strong_subjects[:3]]
        if not strengths:
            strengths = ["Consistent academic effort across subjects"]

        md = "# AI Career & Electives Guidance\n\n"
        md += "## Strengths\n\n" + "".join(f"- {s}\n" for s in strengths)
        md += "\n## Top 3 Career Paths\n\n"
        md += (
            "1. **Specialist in your strongest area** — deepen expertise and pursue "
            "industry roles or postgraduate study in the subjects where you excel.\n"
            "2. **Applied / Interdisciplinary role** — combine multiple subject areas "
            "in a consulting, project-management, or applied research capacity.\n"
            "3. **Research & Academia** — if you enjoy the theoretical side, consider "
            "graduate studies or a research career in your field.\n"
        )
        md += "\n## Recommended Electives\n\n"
        md += (
            "- Advanced courses in your highest-scoring subjects\n"
            "- Practical skills: project management, technical communication, data analysis\n"
            "- Cross-disciplinary electives to broaden your perspective\n"
        )
        md += "\n## Motivational Advice\n\n"
        md += (
            "Stay curious and apply your knowledge through real projects and internships. "
            "Build on the areas where you excel, seek mentorship, and keep practising consistently."
        )
        return md
    except Exception as e:
        return f"Career advisor experienced an unexpected error: {e}"


def run_career_guidance(api_client) -> str:
    """Fetch the student's academic data via the API client and return guidance Markdown."""
    years_data = api_client.get_academic_years()
    student_data = {"years": years_data}
    return generate_career_guidance(student_data)
