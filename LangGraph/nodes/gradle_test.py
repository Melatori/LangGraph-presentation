import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any

from langchain_core.messages import HumanMessage

from backend_state import BackendState
from nodes.gradle_build import BUILD_TIMEOUT_SECONDS, MAX_LOG_LINES, NO_INTEGRATION_TESTS
from tools import WORKSPACE


TEST_TASKS = ["test", "testIntegration"]
# --continue runs testIntegration even if test fails, so the agent gets all failures at once.
TEST_COMMAND = [str(WORKSPACE / "gradlew.bat"), *TEST_TASKS, "--continue"]
TEST_RESULTS_DIR = WORKSPACE / "build" / "test-results"
MAX_FAILURES = 10
MAX_MESSAGE_LENGTH = 500


def _failed_tests(started: float) -> tuple[list[str], list[str]]:
    # The JUnit XML reports hold the assertion messages and causes that the Gradle console output leaves out.
    names: list[str] = []
    details: list[str] = []
    for task in TEST_TASKS:
        for report in sorted((TEST_RESULTS_DIR / task).glob("TEST-*.xml")):
            if report.stat().st_mtime < started:
                continue  # Left over from an earlier run.
            for case in ET.parse(report).iter("testcase"):
                for problem in case.findall("failure") + case.findall("error"):
                    name = f"{task}: {case.get('classname')} > {case.get('name')}"
                    trace = (problem.text or "").splitlines()
                    causes = [line.strip() for line in trace if line.strip().startswith("Caused by:")]
                    names.append(name)
                    details.append("\n".join([name, problem.get("message", "").strip()[:MAX_MESSAGE_LENGTH], *causes]))
    return names, details


def _integration_tests_ran() -> bool:
    # Not filtered by time: an up-to-date task keeps the reports of its last run, and Gradle deletes them
    # once the test classes are gone.
    for report in (TEST_RESULTS_DIR / "testIntegration").glob("TEST-*.xml"):
        for case in ET.parse(report).iter("testcase"):
            if case.find("skipped") is None:
                return True
    return False


def gradle_test(state: BackendState) -> dict[str, Any]:
    attempts = state.get("test_attempts", 0) + 1
    started = time.time()

    try:
        result = subprocess.run(
            TEST_COMMAND,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=BUILD_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        message = HumanMessage(f"Gradle tests timed out after {BUILD_TIMEOUT_SECONDS} s")
        return {"test_status": False, "test_attempts": attempts, "failed_tests": [], "build_attempts": 0, "messages": [message]}

    integration_tests_ran = _integration_tests_ran()
    if result.returncode == 0 and integration_tests_ran:
        return {"test_status": True, "test_attempts": attempts, "failed_tests": []}

    names, details = _failed_tests(started)
    parts = ["Tests failed. Fix the cause, don't weaken the tests."]
    if not integration_tests_ran:
        # Gradle passes an empty testIntegration folder, so the node checks it itself.
        names.append("testIntegration: no integration tests ran")
        parts.append(NO_INTEGRATION_TESTS)
    if details:
        parts.extend(details[:MAX_FAILURES])
        if len(details) > MAX_FAILURES:
            parts.append(f"...and {len(details) - MAX_FAILURES} more failed tests.")
    elif result.returncode != 0:
        # No failed test cases: the tasks failed before running tests, e.g. the testIntegration task is missing.
        parts.append("\n".join((result.stdout + result.stderr).splitlines()[-MAX_LOG_LINES:]))
    message = HumanMessage("\n\n".join(parts))
    # A fix starts a new cycle: the build gets its attempts back, as after the reviewer's issues.
    return {"test_status": False, "test_attempts": attempts, "failed_tests": names, "build_attempts": 0, "messages": [message]}
