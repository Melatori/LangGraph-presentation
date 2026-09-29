from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from nodes.backend_agent import agent
from nodes.gradle_build import gradle_build
from nodes.gradle_test import gradle_test
from nodes.reviewer import reviewer
from backend_state import BackendState


MAX_BUILD_ATTEMPTS = 3
MAX_TEST_ATTEMPTS = 3
MAX_REVIEW_ROUNDS = 5

Graph = CompiledStateGraph[BackendState, None, BackendState, BackendState]


def route_after_build(state: BackendState) -> str:
    if state.get("compile_status"):
        return "gradle_test"
    if state.get("build_attempts", 0) >= MAX_BUILD_ATTEMPTS:
        return END
    return "agent"


def route_after_tests(state: BackendState) -> str:
    if state.get("test_status"):
        return "reviewer"
    if state.get("test_attempts", 0) >= MAX_TEST_ATTEMPTS:
        return END
    return "agent"


def route_after_review(state: BackendState) -> str:
    if state.get("review_approved") or state.get("review_rounds", 0) >= MAX_REVIEW_ROUNDS:
        return END
    return "agent"


def build_graph(checkpointer: BaseCheckpointSaver[Any] | None = None) -> Graph:
    builder = StateGraph(BackendState)
    builder.add_node("agent", agent)
    builder.add_node("gradle_build", gradle_build)
    builder.add_node("gradle_test", gradle_test)
    builder.add_node("reviewer", reviewer)

    builder.add_edge(START, "agent")
    builder.add_edge("agent", "gradle_build")
    builder.add_conditional_edges("gradle_build", route_after_build, ["agent", "gradle_test", END])
    builder.add_conditional_edges("gradle_test", route_after_tests, ["agent", "reviewer", END])
    builder.add_conditional_edges("reviewer", route_after_review, ["agent", END])

    return builder.compile(checkpointer=checkpointer)
