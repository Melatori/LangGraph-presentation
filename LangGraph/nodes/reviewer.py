from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from backend_state import BackendState
from nodes.backend_agent import MODEL, PROMPTS_DIR, build_system_prompt
from tools import list_files, read_file


REVIEWER_ROLE_FILE = PROMPTS_DIR / "reviewer.md"


class Review(BaseModel):
    """Code review result."""

    approved: bool = Field(description="true if the code can be accepted without changes")
    issues: list[str] = Field(
        default_factory=list,
        description="Issues under the review rules: source, file, what is wrong, how to fix it. Empty if approved=true.",
    )


reviewer_agent = create_agent(
    model=init_chat_model(MODEL, max_tokens=8000),
    tools=[list_files, read_file],
    system_prompt=build_system_prompt(REVIEWER_ROLE_FILE),
    response_format=Review,
    name="reviewer",
)


def _human_answers(state: BackendState) -> str:
    # The developer's ask_human calls hold the questions; the matching tool results hold the answers.
    questions = {
        call["id"]: call["args"]["question"]
        for message in state["messages"]
        if isinstance(message, AIMessage)
        for call in message.tool_calls
        if call["name"] == "ask_human"
    }
    return "\n\n".join(
        f"Q: {questions[message.tool_call_id]}\nA: {message.text}"
        for message in state["messages"]
        if isinstance(message, ToolMessage) and message.tool_call_id in questions
    )


def reviewer(state: BackendState) -> dict[str, Any]:
    task = state["messages"][0].text
    request = f"Review the project. The task the developer was solving:\n\n{task}"
    answers = _human_answers(state)
    if answers:
        request += f"\n\nThe human's answers to the developer's questions (same weight as the task):\n\n{answers}"
    result = reviewer_agent.invoke({"messages": [HumanMessage(request)]})
    review: Review = result["structured_response"]
    rounds = state.get("review_rounds", 0) + 1

    if review.approved or not review.issues:
        return {"review_approved": True, "review_issues": [], "review_rounds": rounds}

    remarks = "\n".join(f"- {issue}" for issue in review.issues)
    message = HumanMessage(f"The reviewer found problems. Fix them:\n\n{remarks}")
    return {
        "review_approved": False,
        "review_issues": review.issues,
        "review_rounds": rounds,
        "build_attempts": 0,
        "test_attempts": 0,
        "messages": [message],
    }
