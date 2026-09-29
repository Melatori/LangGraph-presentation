import argparse
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

load_dotenv()

from backend_state import BackendState
from graph import MAX_BUILD_ATTEMPTS, MAX_REVIEW_ROUNDS, MAX_TEST_ATTEMPTS, Graph, build_graph
from tools import WORKSPACE


# The longest possible run: in every review round each test attempt comes after the maximum of agent + build pairs.
RECURSION_LIMIT = MAX_REVIEW_ROUNDS * (MAX_TEST_ATTEMPTS * (2 * MAX_BUILD_ATTEMPTS + 1) + 1) + 10
MAX_LINE_LENGTH = 150
MAX_ARG_LENGTH = 60
# Next to main.py, so --resume finds the same database whatever the current directory is.
DB_FILE = Path(__file__).resolve().parent / "demo.db"
GRAPH_FILE = Path(__file__).resolve().parent / "graph.mmd"


@dataclass
class NodeStats:
    runs: int = 0
    seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


def _one_line(text: str) -> str:
    line = " ".join(text.split())
    return line if len(line) <= MAX_LINE_LENGTH else line[:MAX_LINE_LENGTH] + "..."


def _format_args(args: dict[str, Any]) -> str:
    # Short arguments (path, name) are shown, long ones (file contents) are hidden.
    parts: list[str] = []
    for key, value in args.items():
        text = str(value)
        short = len(text) <= MAX_ARG_LENGTH and "\n" not in text
        parts.append(f"{key}={text}" if short else f"{key}=...")
    return ", ".join(parts)


def _build_error(log: str) -> str:
    lines = [line.strip() for line in log.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if "error:" in line:
            return line.replace(f"{WORKSPACE}\\", "")
        if "What went wrong" in line and i + 1 < len(lines):
            # The first line often says only where it failed ("Execution failed for task ':x'."), the next one says why.
            return " ".join(text for text in lines[i + 1 : i + 3] if not text.startswith("*"))
        if "timed out" in line:
            return line
    return "see the build log for details"


def _config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}


def print_message(who: str, message: BaseMessage) -> None:
    if isinstance(message, AIMessage):
        # The reviewer's final answer is JSON with the issues; print_review prints it.
        final_review = who == "reviewer" and not message.tool_calls
        if message.text.strip() and not final_review:
            print(f"{who}: {_one_line(message.text)}")
        for call in message.tool_calls:
            print(f"{who} -> {call['name']}({_format_args(call['args'])})")
    elif isinstance(message, ToolMessage):
        # File contents and listings are not printed: only errors and short one-line responses.
        text = message.text.strip()
        if message.status == "error":
            print(f"{message.name} -> {who}: error: {_one_line(text)}")
        elif "\n" not in text and len(text) <= MAX_LINE_LENGTH:
            print(f"{message.name} -> {who}: {text}")


def print_build(update: dict[str, Any]) -> None:
    attempt = update.get("build_attempts", 0)
    if update.get("compile_status"):
        print(f"gradle_build -> gradle_test: build passed (attempt {attempt})")
        return

    target = "agent" if attempt < MAX_BUILD_ATTEMPTS else "END"
    messages = update.get("messages", [])
    log = messages[-1].text if messages else ""
    print(f"gradle_build -> {target}: build failed (attempt {attempt}): {_one_line(_build_error(log))}")


def print_tests(update: dict[str, Any]) -> None:
    attempt = update.get("test_attempts", 0)
    if update.get("test_status"):
        print(f"gradle_test -> reviewer: tests passed (attempt {attempt})")
        return

    target = "agent" if attempt < MAX_TEST_ATTEMPTS else "END"
    failed: list[str] = update.get("failed_tests", [])
    if not failed:
        messages = update.get("messages", [])
        log = messages[-1].text if messages else ""
        print(f"gradle_test -> {target}: tests failed (attempt {attempt}): {_one_line(_build_error(log))}")
        return

    print(f"gradle_test -> {target}: tests failed: {len(failed)} (attempt {attempt})")
    for name in failed:
        print(f"  - {_one_line(name)}")


def print_review(update: dict[str, Any]) -> None:
    review_round = update.get("review_rounds", 0)
    if update.get("review_approved"):
        print(f"reviewer -> END: code approved (round {review_round})")
        return

    target = "agent" if review_round < MAX_REVIEW_ROUNDS else "END"
    issues: list[str] = update.get("review_issues", [])
    print(f"reviewer -> {target}: issues: {len(issues)} (round {review_round})")
    for issue in issues:
        print(f"  - {_one_line(issue)}")


def print_summary(stats: dict[str, NodeStats]) -> None:
    if not stats:
        return
    print(f"\n{'node':<16}{'runs':>6}{'time, s':>10}{'input tok':>12}{'output tok':>12}")
    for node, node_stats in stats.items():
        print(
            f"{node:<16}{node_stats.runs:>6}{node_stats.seconds:>10.1f}"
            f"{node_stats.input_tokens:>12}{node_stats.output_tokens:>12}"
        )
    print(
        f"{'total':<16}{sum(s.runs for s in stats.values()):>6}{sum(s.seconds for s in stats.values()):>10.1f}"
        f"{sum(s.input_tokens for s in stats.values()):>12}{sum(s.output_tokens for s in stats.values()):>12}"
    )


def ask(question: Any, thread_id: str) -> str | None:
    print(f"\nagent asks: {question}")
    # Without a terminal (e.g. output redirected to a file) nobody can answer, so the run stays paused.
    answer = input("answer> ").strip() if sys.stdin.isatty() else ""
    if not answer:
        print(f'waiting for an answer — resume with: python main.py --resume {thread_id} --answer "<text>"')
        return None
    return answer


def stream_steps(
    graph: Graph, graph_input: BackendState | Command[Any] | None, config: RunnableConfig, stats: dict[str, NodeStats]
) -> float:
    last_update = time.perf_counter()
    for part in graph.stream(graph_input, config, stream_mode="updates", subgraphs=True, version="v2"):
        if part["type"] != "updates":
            continue
        for node, node_update in part["data"].items():
            if not node_update or node.startswith("__"):
                continue
            if not part["ns"]:
                # Nodes run one at a time, so the time since the previous outer update is this node's run time.
                now = time.perf_counter()
                stats[node].runs += 1
                stats[node].seconds += now - last_update
                last_update = now
                # Outer graph: "agent" repeats the subgraph steps that were already printed.
                if node == "gradle_build":
                    print_build(node_update)
                elif node == "gradle_test":
                    print_tests(node_update)
                elif node == "reviewer":
                    print_review(node_update)
                continue
            # ns[0] looks like "agent:<id>" or "reviewer:<id>": take the node name.
            who = part["ns"][0].split(":")[0]
            for message in node_update.get("messages", []):
                if isinstance(message, AIMessage) and message.usage_metadata:
                    stats[who].input_tokens += message.usage_metadata["input_tokens"]
                    stats[who].output_tokens += message.usage_metadata["output_tokens"]
                print_message(who, message)
    return last_update


def run(graph: Graph, graph_input: BackendState | Command[Any] | None, thread_id: str) -> None:
    config = _config(thread_id)
    stats: dict[str, NodeStats] = defaultdict(NodeStats)

    try:
        while True:
            last_update = stream_steps(graph, graph_input, config, stats)
            snapshot = graph.get_state(config)
            if not snapshot.interrupts:
                if "build_attempts" not in snapshot.values:
                    print("Result: the build was not run.")
                break
            # The paused node hasn't finished, so its time so far is added without counting a run.
            stats[snapshot.next[0]].seconds += time.perf_counter() - last_update
            answer = ask(snapshot.interrupts[0].value, thread_id)
            if answer is None:
                break
            graph_input = Command(resume=answer)
    except BaseException:
        print(f"\nrun stopped — continue with: python main.py --resume {thread_id}")
        print_summary(stats)
        raise
    print_summary(stats)


def resume(graph: Graph, thread_id: str, answer: str | None) -> None:
    snapshot = graph.get_state(_config(thread_id))
    if not snapshot.values:
        print(f"Thread {thread_id} not found in {DB_FILE.name}.")
    elif snapshot.interrupts:
        answer = answer or ask(snapshot.interrupts[0].value, thread_id)
        if answer:
            run(graph, Command(resume=answer), thread_id)
    elif snapshot.next:
        # The previous process stopped mid-run: continue from the last checkpoint.
        run(graph, None, thread_id)
    else:
        print(f"Thread {thread_id} has already finished, nothing to resume.")


def print_history(graph: Graph, thread_id: str) -> None:
    snapshots = list(graph.get_state_history(_config(thread_id)))
    if not snapshots:
        print(f"Thread {thread_id} not found in {DB_FILE.name}.")
        return
    # get_state_history returns the newest checkpoint first.
    for snapshot in reversed(snapshots):
        values = snapshot.values
        step = snapshot.metadata.get("step", "?") if snapshot.metadata else "?"
        next_nodes = ", ".join(snapshot.next) or "END"
        print(
            f"step {step:>3} | next: {next_nodes:<16}"
            f" | build_attempts={values.get('build_attempts', '-')}"
            f" test_attempts={values.get('test_attempts', '-')}"
            f" review_rounds={values.get('review_rounds', '-')}"
            f" compile_status={values.get('compile_status', '-')}"
            f" test_status={values.get('test_status', '-')}"
            f" review_approved={values.get('review_approved', '-')}"
        )


def draw() -> None:
    GRAPH_FILE.write_text(build_graph().get_graph().draw_mermaid(), encoding="utf-8")
    print(f"Saved {GRAPH_FILE}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Java/Spring Boot agent pipeline.")
    parser.add_argument("task", nargs="?", help="task for a new run")
    parser.add_argument("--thread", help="thread id for a new run (generated if omitted)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resume", metavar="ID", help="answer the agent's question or continue a stopped run")
    mode.add_argument("--history", metavar="ID", help="print the checkpoint history of a thread")
    mode.add_argument("--draw", action="store_true", help=f"save the graph as Mermaid to {GRAPH_FILE.name}")
    parser.add_argument("--answer", help="answer to the agent's question for --resume (asked in the terminal if omitted)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.draw:
        draw()
        return

    with closing(sqlite3.connect(DB_FILE, check_same_thread=False)) as connection:
        graph = build_graph(SqliteSaver(connection))
        if args.history:
            print_history(graph, args.history)
        elif args.resume:
            resume(graph, args.resume, args.answer)
        else:
            thread_id = args.thread or uuid.uuid4().hex[:8]
            print(f"thread: {thread_id}")
            task = args.task or input("Task: ")
            run(graph, {"messages": [HumanMessage(task)]}, thread_id)


if __name__ == "__main__":
    main()
