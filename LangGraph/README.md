# Java/Spring Boot agent pipeline (LangGraph demo)

A LangGraph pipeline that works on the Spring Boot project in `../application`:

```
agent -> gradle_build -> gradle_test -> reviewer -> END
  ^           |              |             |
  +-----------+--------------+-------------+   build failed / tests failed / reviewer issues
```

- `agent` — developer agent (Claude) with file tools; writes the code. When the task is ambiguous, it can ask you a question with the `ask_human` tool: the run pauses until you answer.
- `gradle_build` — runs `gradlew.bat assemble testClasses testIntegrationClasses` (compiles the code and the tests without running them); on failure sends the log back to the agent (up to 3 attempts).
- `gradle_test` — runs `gradlew.bat test testIntegration --continue`; on failure sends the failed tests with their messages (from the JUnit XML reports) back to the agent (up to 3 attempts). A run where no integration test ran also counts as failed: the agent is told to write them.
- `reviewer` — read-only reviewer agent; checks the task and `conventions.md`, sends issues back (up to 5 rounds).

The project must have both test tasks: unit tests in `src/test/java` (`test`), tests with the full Spring context in `src/testIntegration/java` (`testIntegration`). `conventions.md` tells the agents how to set them up; if the project doesn't have them yet, the agent adds them.

State is saved to `demo.db` after every step, so a run can be paused, inspected and resumed.

## Requirements

- Windows 10/11 (the build node runs `gradlew.bat`).
- JDK 25, with `JAVA_HOME` pointing to it.
- Python 3.14.
- Git.
- An Anthropic API key in `LangGraph/.env`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ```

## Network access

These hosts must be reachable:

| Host | Used for |
|---|---|
| `api.anthropic.com` | model calls of the agent and the reviewer |
| `repo1.maven.org` | Maven Central: project dependencies, `get_library_version` |
| `plugins.gradle.org` | Gradle plugins, `get_library_version` |
| `services.gradle.org` | Gradle distribution downloaded by the wrapper |

## Installation

In PowerShell:

```powershell
git clone https://github.com/Melatori/LangGraph-presentation.git
cd LangGraph-presentation\LangGraph
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Set-Content .env "ANTHROPIC_API_KEY=sk-ant-..."
```

Check the setup:

```powershell
.venv\Scripts\python -c "from graph import build_graph; build_graph()"
.venv\Scripts\python main.py --draw
..\application\gradlew.bat -p ..\application --version
```

The last command also downloads Gradle, so the first build during the demo does not wait for it.

## Commands

Run all commands from the `LangGraph` folder.

| Command | What it does |
|---|---|
| `.venv\Scripts\python main.py [--thread <id>] "<task>"` | New run. Without `--thread` an id is generated and printed first. |
| `.venv\Scripts\python main.py --resume <id> [--answer "<text>"]` | Answers the agent's question (asked in the terminal if `--answer` is omitted), or continues a run that stopped midway from its last checkpoint. |
| `.venv\Scripts\python main.py --history <id>` | One line per checkpoint: step, next nodes, `build_attempts`, `test_attempts`, `review_rounds`, `compile_status`, `test_status`, `review_approved`. |
| `.venv\Scripts\python main.py --draw` | Saves the graph as Mermaid text to `graph.mmd`. |

Every run and resume ends with a table per node: runs, total time, input and output tokens.

When the agent asks a question, `main.py` prints it as `agent asks: ...`. In a terminal you answer right there and the run continues in the same process. Without a terminal (output redirected to a file) the run stays paused and prints the `--resume <id> --answer "<text>"` command to continue it.

## Demo scenario

**Before the demo:** delete `demo.db` or use a new thread id. A new run with an existing thread id continues that thread's state (attempt and round counters included).

The demo builds a calculator service from scratch.

1. **Empty `application/`:** keep only the Gradle wrapper, `.gitignore` and `.git`:
   ```powershell
   Remove-Item -Recurse -Force ..\application\build.gradle.kts, ..\application\settings.gradle.kts, ..\application\src, ..\application\build, ..\application\.gradle -ErrorAction SilentlyContinue
   ```

2. **Run the task.** About 3 minutes if the build, the tests and the review pass the first time, longer with fix rounds:
   ```powershell
   .venv\Scripts\python main.py --thread demo "Create a Spring Boot service named calculator-service from scratch: a REST API for a basic calculator. GET /api/v1/calculator/{operation}?a=<number>&b=<number> returns JSON {'result': <number>}. Operations: add, subtract, multiply, divide, power (a to the power of b), sqrt (square root of a, b is not used). Division by zero, the square root of a negative number, an unknown operation or a missing parameter return 400. Use Java 25, the latest Spring Boot 3.5.x and Gradle Kotlin DSL. The Gradle wrapper is already in the project."
   ```
   The output shows who passes control to whom: agent tool calls, build and test results, reviewer issues. The run ends when the reviewer approves the code or the attempt/round limits are reached.

   To show a question from the agent, leave the API contract out of the task (e.g. "Create a Spring Boot calculator service with add, subtract, multiply, divide, power and sqrt. Use Java 25, …"). The agent will most likely ask about the API format:
   ```
   agent asks: <question, options, recommendation>
   answer> 
   ```

3. **Show the saved history and the result:**
   ```powershell
   .venv\Scripts\python main.py --history demo
   ..\application\gradlew.bat -p ..\application bootRun
   ```
   Then open `http://localhost:8080/api/v1/calculator/add?a=2&b=3` (`{"result":5.0}`) and `http://localhost:8080/api/v1/calculator/divide?a=1&b=0` (400). Stop the server with Ctrl+C.

4. **Pause and resume:** press Ctrl+C during a run, then continue it from the last checkpoint:
   ```powershell
   .venv\Scripts\python main.py --resume demo
   ```

**Another scenario — upgrade an existing project.** The `baseline` branch holds a hello-service on Spring Boot 3.3.4 with `options.release(21)`. Empty `application/` (step 1), then unpack the baseline into it:
```powershell
git archive -o baseline.zip origin/baseline; Expand-Archive baseline.zip ..\application -Force; Remove-Item baseline.zip
```
Then run the task "Upgrade the project to Java 25 and the latest Spring Boot 3.5.x". Besides the upgrade, the agent moves the baseline's integration tests to `src/testIntegration/java`. This scenario hasn't been run with the current pipeline and takes longer.
