from typing import Dict, Any
import json

# LangChain/ChatOllama integration
try:
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - fallback when langchain not available
    ChatOllama = None
    SystemMessage = None
    HumanMessage = None


SYSTEM_PROMPT = (
    "You are an expert Academic and Career Advisor for Computer Science students. "
    "Analyze the provided list of subjects and grades. Identify the student's strengths "
    "(e.g., strong math, great at software engineering, backend vs frontend flair) and provide: "
    "1) Top 3 recommended career paths, 2) Types of elective/optional courses they should select next semester, "
    "and 3) A short motivational advice. Answer concisely and format the output in Markdown with headings."
)


def _format_student_data(student_data: Dict[str, Any]) -> str:
    try:
        return json.dumps(student_data, indent=2)
    except Exception:
        return str(student_data)


def generate_career_guidance(student_data: Dict[str, Any]) -> str:
    """Generate career guidance markdown for a student_data dict.

    student_data should contain a structured representation of years, subjects, assessments and grades.
    Returns a Markdown-formatted string.
    """
    # If langchain + ChatOllama available, use it
    if ChatOllama is not None:
        try:
            model_name = "llama3"
            model = ChatOllama(model=model_name)

            user_content = (
                "Student academic history (JSON):\n```" + _format_student_data(student_data) + "\n```\n"
                "Please produce the advice in Markdown with these sections:\n"
                "- **Strengths:** short bullet list\n"
                "- **Top 3 Career Paths:** numbered list with 1-2 sentences each\n"
                "- **Recommended Electives:** bullet list of course types or topics\n"
                "- **Motivational Advice:** one short paragraph\n"
            )

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_content),
            ]

            result = model.generate([messages])
            # Extract text from result safely
            try:
                text = result.generations[0][0].text
                if text:
                    return text
            except Exception:
                # fallback to calling the model directly
                out = model(messages)
                if isinstance(out, dict) and out.get("content"):
                    return out["content"]
                if hasattr(out, "content"):
                    return out.content
        except Exception as e:  # pragma: no cover - runtime issues with LLM
            return (
                "**Career Advisor unavailable**\n\n"
                "The career guidance model could not be reached. "
                f"Error: {e}\n\n"
                "Please try again later."
            )

    # Fallback: simple rule-based guidance when LLM not available
    try:
        subjects = []
        for y in student_data.get("years", []):
            for s in y.get("subjects", []):
                subjects.append(s)

        # crude heuristics
        math_like = sum(1 for s in subjects if "math" in s.get("name", "").lower())
        prog_like = sum(1 for s in subjects if any(k in s.get("name", "").lower() for k in ("program", "software", "algor", "data")))
        systems_like = sum(1 for s in subjects if any(k in s.get("name", "").lower() for k in ("os", "network", "system", "architecture")))

        strengths = []
        if math_like >= 2:
            strengths.append("Strong mathematical foundations")
        if prog_like >= 2:
            strengths.append("Good programming / software development skills")
        if systems_like >= 2:
            strengths.append("Interest in systems / low-level or infrastructure topics")
        if not strengths:
            strengths.append("Well-rounded CS foundation")

        career_suggestions = [
            "Software Engineer (Backend/Full-stack)",
            "Data Scientist / ML Engineer",
            "Systems Engineer / DevOps",
        ]

        electives = [
            "Advanced Programming / Data Structures",
            "Databases and Distributed Systems",
            "Machine Learning Fundamentals",
        ]

        advice = (
            "Keep exploring project-based courses and internships; build small projects that showcase your strengths. "
            "Seek mentorship and practice problem-solving regularly."
        )

        md = "# AI Career & Electives Guidance\n\n"
        md += "## Strengths\n\n"
        for s in strengths:
            md += f"- {s}\n"
        md += "\n## Top 3 Career Paths\n\n"
        for i, c in enumerate(career_suggestions, start=1):
            md += f"{i}. **{c}** — Briefly explore coursework and internships related to this path.\n"
        md += "\n## Recommended Electives\n\n"
        for e in electives:
            md += f"- {e}\n"
        md += "\n## Motivational Advice\n\n"
        md += advice
        return md
    except Exception as e:
        return f"Career advisor experienced an unexpected error: {e}"
