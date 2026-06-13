"""
Career guidance agent — powered by Ollama + LangGraph ReAct.
The agent must call get_academic_profile to fetch the student's data before advising.
Field-agnostic: works for any university programme, not just computer science.
"""

from typing import Any, Dict

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_ollama import ChatOllama
    from langgraph.prebuilt import create_react_agent
except Exception:
    ChatOllama = None
    SystemMessage = None
    HumanMessage = None
    create_react_agent = None


SYSTEM_PROMPT = (
    "You are an expert Academic and Career Advisor for university students. "
    "The student's academic profile will be provided to you. "
    "Analyse their strengths and performance based solely on what is shown — "
    "do NOT assume a specific field (e.g. do not default to computer science). "
    "Tailor every recommendation — career paths, electives, and advice — to the actual "
    "subjects and grades visible in the profile. "
    "If you need to re-fetch or verify the profile data, use the get_academic_profile tool. "
    "Provide: 1) Top 3 career paths suited to this student's profile, "
    "2) Elective or optional course types to consider next semester, "
    "3) A short motivational paragraph. "
    "Format your response in Markdown with clear headings."
)


def generate_career_guidance(student_data: Dict[str, Any]) -> str:
    """
    Rule-based career guidance — used as fallback when the LLM is unavailable.

    student_data must have a 'years' key with the academic years list as returned
    by the API (subjects → assessments → grade: {score: ...}).
    """
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
                    float(a["grade"]["score"])
                    for a in assessments
                    if a.get("grade") and a["grade"].get("score") is not None
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
    """
    Run the career advisor ReAct agent.

    The agent receives the system prompt and a request to fetch the student's
    profile via the get_academic_profile tool. Falls back to rule-based guidance
    when the LLM is unavailable.
    """
    from agents.tools import get_academic_profile, set_api_client

    set_api_client(api_client)

    if ChatOllama is None or create_react_agent is None:
        try:
            years_data = api_client.get_academic_years()
        except Exception as e:
            return f"Error fetching academic data: {e}"
        return generate_career_guidance({"years": years_data})

    try:
        # Pre-fetch the profile so it is available in the initial context.
        # llama3.2 may not reliably emit structured tool-call tokens when the model
        # has no data to work from, so we prime the conversation with the fetched
        # profile and keep get_academic_profile available for the agent to re-call
        # if it wants to verify or expand on any detail.
        profile = get_academic_profile.invoke({})

        llm = ChatOllama(model="llama3.2", temperature=0)
        agent = create_react_agent(llm, [get_academic_profile])

        human_message = (
            f"Student Academic Profile:\n\n{profile}\n\n"
            "Based on the above profile, provide comprehensive career guidance. "
            "Call get_academic_profile if you need to re-fetch or verify the data."
        )

        result = agent.invoke({
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_message),
            ]
        })

        messages = result.get("messages", [])
        for msg in reversed(messages):
            content = getattr(msg, "content", "")
            if content and not getattr(msg, "tool_calls", []):
                return content

        # Agent produced no usable final message — fall back
        years_data = api_client.get_academic_years()
        return generate_career_guidance({"years": years_data})

    except Exception as e:
        return (
            "**Career Advisor unavailable**\n\n"
            f"The career guidance model could not be reached: {e}\n\n"
            "Please try again later."
        )
