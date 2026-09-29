import subprocess
from typing import Any

from langchain_core.messages import HumanMessage

from backend_state import BackendState
from tools import WORKSPACE


# Compiles the code and both test source sets without running the tests: gradle_test runs them.
GRADLE_COMMAND = [str(WORKSPACE / "gradlew.bat"), "assemble", "testClasses", "testIntegrationClasses"]
BUILD_TIMEOUT_SECONDS = 600
MAX_LOG_LINES = 60
NO_INTEGRATION_TESTS = (
    "The project has no integration tests. Set up the testIntegration suite in build.gradle.kts and write "
    "the integration tests in src/testIntegration/java exactly as described in the conventions, section 7, "
    "even if the task doesn't mention tests."
)


def gradle_build(state: BackendState) -> dict[str, Any]:
    attempts = state.get("build_attempts", 0) + 1

    try:
        result = subprocess.run(
            GRADLE_COMMAND,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=BUILD_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        message = HumanMessage(f"Gradle build timed out after {BUILD_TIMEOUT_SECONDS} s")
        return {"compile_status": False, "build_attempts": attempts, "messages": [message]}

    if result.returncode == 0:
        return {"compile_status": True, "build_attempts": attempts}

    log_tail = "\n".join((result.stdout + result.stderr).splitlines()[-MAX_LOG_LINES:])
    # Without the testIntegration suite Gradle doesn't know its compile task.
    hint = f"{NO_INTEGRATION_TESTS}\n\n" if "'testIntegrationClasses' not found" in log_tail else ""
    message = HumanMessage(f"Gradle build failed. Fix errors. \n\n{hint}{log_tail}")
    return {"compile_status": False, "build_attempts": attempts, "messages": [message]}