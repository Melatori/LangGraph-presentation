from typing import NotRequired

from langchain.agents import AgentState

class BackendState(AgentState):
    compile_status: NotRequired[bool]
    build_attempts: NotRequired[int]
    test_status: NotRequired[bool]
    test_attempts: NotRequired[int]
    failed_tests: NotRequired[list[str]]
    review_approved: NotRequired[bool]
    review_issues: NotRequired[list[str]]
    review_rounds: NotRequired[int]
