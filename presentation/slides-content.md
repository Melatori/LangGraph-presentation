# Using LangGraph for Coding — slide content

Source for moving the deck into a corporate template. `Using-LangGraph-for-Coding.pptx` next to this file has the same slides and speaker notes.

## How to move it into your template

- **By hand.** Open the corporate template → Home → New Slide → Reuse Slides, pick this .pptx and leave “Keep source formatting” unchecked. Or copy the slides and paste them with “Use Destination Theme”. Titles sit in real title placeholders and take the template’s style; layout names match the Office defaults (Title Slide, Title Only, Section Header). Diagrams, code and tables are regular shapes — you only need to move and recolor them.
- **With an agent.** Give an agent the template and this file, for example: “Build the deck in corporate.potx from slides-content.md: pick a fitting template layout for each slide, move the text, set code in a monospace font, use native tables, redraw the diagrams as shapes in the template’s colors, and put the speaker notes into the slide notes.”
- **Colors carry meaning.** Purple means “the LLM decides”, teal means “code guarantees”. Replace them with two contrasting brand colors, but keep the distinction on every slide.

## Timing (30 minutes + 15 minutes of Q&A)

| Block | Time | Slides |
|---|---|---|
| Introduction | 0:00–2:00 | 1–2 |
| Bridge from the familiar | 2:00–5:00 | 3–4 |
| When an IDE agent is not enough | 5:00–7:00 | 5 |
| Concepts on our example | 7:00–13:00 | 6–10 |
| Demo | 13:00–21:00 | 11–12 |
| Hybrid | 21:00–24:00 | 13–14 |
| When not to use it, risks | 24:00–27:00 | 15–17 |
| Takeaways | 27:00–29:00 | 18 |
| Buffer | 29:00–30:00 | — |
| Q&A | 15 minutes | 19, backup 21–24 |

---

## 1. Using LangGraph for Coding

**Time:** 0:00–2:00 (together with “About me”) · **Layout:** Title Slide

**Subtitle:** When your IDE agent needs a process

**Byline:** [Name Surname] · [role, team] · [date]

**Visual:** dark background; a tiny graph of three dots in the corner (purple — teal — purple).

**Speaker notes:**

> Name the topic and the key question of the talk: why LangGraph, if you already have Claude Code and Copilot? The answer comes at the end, but promise it right away.

---

## 2. About me

**Time:** 0:00–2:00 (together with the title slide) · **Layout:** Title Only

**Left:** space for a photo.

**Right:**

- [Name Surname]
- [Role, team]
- [What you work on — one line]
- [Which agents you use every day: Claude Code, Copilot…]
- [Why LangGraph — one sentence, the motivation for the talk]

**Speaker notes:**

> — Who you are and what you do.
> — One sentence on why you got into LangGraph: it’s the motivation for the whole talk.
> If you decided to start a fresh run in the background, start it now: “while I’m talking, the agent is working”. Come back to it at the end or during Q&A.

---

## 3. You already use a graph

**Time:** 2:00–3:30 · **Layout:** Title Only

**Visual (diagram):** a two-node loop. “task from you” → **LLM** (purple) ⇄ **Tools** (read · edit · bash · grep); arrows labeled “tool call” and “result”; LLM → “answer to you”. Caption: Claude Code · Copilot agent mode.

**Right, large:** The model picks every step.

There is a graph here too — it’s just hidden inside the agent, and the LLM chooses the transitions.

**Speaker notes:**

> Inside Claude Code and Copilot agent mode there’s a simple loop: the model picks a tool, gets the result, picks the next step. That’s a two-node graph. You already use it — it’s just hidden, and the LLM chooses the transitions. You give the task, you get the answer: you’re right there.

---

## 4. The problem: the model picks the next step

**Time:** 3:30–5:00 · **Layout:** Title Only

- **It may skip the tests** …and confidently report “done”.
- **It may “fix” a test** by deleting an assert or marking the test @Disabled.
- **It may invent a version** of a library or plugin — from memory, often outdated.

In the IDE that’s fine: you’re there and see everything. **Without you, it isn’t.**

**Visual:** three cards numbered in purple circles.

**Speaker notes:**

> Ask the room: whose agent has reported “done” without running the tests? Usually many hands go up. All three examples come from one thing: the model picks the next step. In the IDE that’s fine — you’re there and will correct it. When nobody is around, it becomes a problem.

---

## 5. When an IDE agent is not enough

**Time:** 5:00–7:00 · **Layout:** Title Only

- **Issue → PR in CI** — a bot takes a ticket from the tracker and opens a PR
- **Mass migrations** — hundreds of files or dozens of repos, in parallel
- **Test generation** — accepted only if tests are green and coverage went up
- **Dependency updates** — a nightly run: update, build, verify

**What they share:** no human in the loop · repeatable · mandatory checks → jobs for a graph, not for a chat.

**Visual:** a 2×2 grid of cards; three teal pills on the right.

**Speaker notes:**

> Go through the four scenarios, one sentence each. What they share is on the right: they run without a human, they’re repeatable, and the checks are mandatory. If people have their own examples — great, but don’t linger.

---

## 6. Our example: a Spring Boot pipeline

**Time:** 7:00–8:30 · **Layout:** Title Only

Task in → a project that builds, passes the tests and the review.

**Visual (graph diagram):**

- START → **agent** (purple, “writes code”) → **gradle_build** (teal, “build and tests”) → “ok” → **reviewer** (purple, “checks conventions”) → “approved” → END
- Back edge below: gradle_build → agent, label “failed → error log to the agent, up to 3 attempts”
- Back edge above: reviewer → agent, label “issues → back to the agent (up to 5 rounds)”
- Legend: purple — the LLM decides; teal — code guarantees. On the right: “Limit reached → END”

**Speaker notes:**

> Our example is a Spring Boot pipeline. Purple nodes are where the LLM decides: the developer and the reviewer. Teal is where plain code runs: build and tests. Note the back edges: if the build fails, the error log goes back to the agent; if the reviewer has issues, those go back to the agent too. The number of attempts is capped.

---

## 7. The whole graph fits on one screen

**Time:** 8:30–10:00 · **Layout:** Title Only

```python
MAX_BUILD_ATTEMPTS = 3
MAX_REVIEW_ROUNDS = 5

def route_after_build(state: BackendState) -> str:
    if state.get("compile_status"):
        return "reviewer"
    if state.get("build_attempts", 0) >= MAX_BUILD_ATTEMPTS:
        return END
    return "agent"

def route_after_review(state: BackendState) -> str:
    if state.get("review_approved") or state.get("review_rounds", 0) >= MAX_REVIEW_ROUNDS:
        return END
    return "agent"

def build_graph():
    builder = StateGraph(BackendState)
    builder.add_node("agent", agent)
    builder.add_node("gradle_build", gradle_build)
    builder.add_node("reviewer", reviewer)

    builder.add_edge(START, "agent")
    builder.add_edge("agent", "gradle_build")
    builder.add_conditional_edges("gradle_build", route_after_build, ["agent", "reviewer", END])
    builder.add_conditional_edges("reviewer", route_after_review, ["agent", END])
    return builder.compile()
```

*graph.py (imports omitted)*

**Right:**

- **3 nodes** — agent, gradle_build, reviewer
- **2 conditional edges** — the routers are plain Python functions
- **Limits live in code** — constants, not a request in the prompt

**Speaker notes:**

> This is the entire graph. Three nodes, two conditional edges. The routers are plain Python functions: they read the state and return the name of the next node. The limits are constants in code, not a plea to the model like “no more than three attempts”.

---

## 8. A node without an LLM: code runs the build

**Time:** 10:00–11:00 · **Layout:** Title Only

```python
def gradle_build(state: BackendState) -> dict[str, Any]:
    attempts = state.get("build_attempts", 0) + 1

    result = subprocess.run(
        GRADLE_COMMAND,                  # gradlew.bat build
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=BUILD_TIMEOUT_SECONDS,
    )

    if result.returncode == 0:
        return {"compile_status": True, "build_attempts": attempts}

    log = (result.stdout + result.stderr).splitlines()
    log_tail = "\n".join(log[-MAX_LOG_LINES:])
    message = HumanMessage(f"Gradle build failed. Fix errors.\n\n{log_tail}")
    return {"compile_status": False, "build_attempts": attempts, "messages": [message]}
```

*nodes/gradle_build.py (reformatted)*

**Code runs the build, not the model** — it can’t be skipped or “forgotten”.

**Right, card “State — the graph’s shared memory”:**

```python
class BackendState(AgentState):
    compile_status: NotRequired[bool]
    build_attempts: NotRequired[int]
    review_approved: NotRequired[bool]
    review_issues: NotRequired[list[str]]
    review_rounds: NotRequired[int]
```

- messages comes from AgentState: the agent’s conversation history
- a node returns only the fields it changed
- a router reads the state and picks the next node

**Speaker notes:**

> The main point of the talk is on this slide: code runs the build, not the model. The model can’t skip it or “forget” it. If the build fails, the tail of the log becomes a message to the agent. State is the graph’s shared memory: nodes return only the fields they changed.

---

## 9. The reviewer: a separate agent with a strict answer

**Time:** 11:00–12:00 · **Layout:** Title Only

```python
class Review(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)

reviewer_agent = create_agent(
    model=init_chat_model(MODEL),
    tools=[list_files, read_file],       # read-only
    system_prompt=build_system_prompt(REVIEWER_ROLE),
    response_format=Review,              # strict schema
)
```

*nodes/reviewer.py (simplified)*

> “The project already builds and the tests pass; that was checked before you. Look for what the build doesn’t catch.” — from the reviewer prompt (translated)

**Right (numbered list):**

- **Read-only** — list_files and read_file: it can’t fix the code itself
- **Clean context** — sees the task and the code, not the developer’s reasoning
- **Only after a green build** — the expensive LLM review runs only once the cheap check has passed
- **Schema-bound answer** — the router checks review_approved instead of parsing text

**Speaker notes:**

> The reviewer is a separate agent. It can only read files, and it sees the task and the code but not the developer’s reasoning — like Claude Code subagents with their own context. It runs only after a green build, so it looks for what the build doesn’t catch. The answer follows a Pydantic schema, so routing works on a bool, not on parsing text.

---

## 10. Pause and persistence: checkpointer + interrupt()

**Time:** 12:00–13:00 · **Layout:** Title Only

```python
def human_approval(state: BackendState) -> dict[str, Any]:
    answer = interrupt("Reviewer approved. Accept the changes?")  # pause
    return {"human_approved": answer == "yes"}

conn = sqlite3.connect("demo.db", check_same_thread=False)
graph = builder.compile(checkpointer=SqliteSaver(conn))
config = {"configurable": {"thread_id": "demo-1"}}

graph.invoke({"messages": [HumanMessage(task)]}, config)  # ~20 min, stops at interrupt
graph.invoke(Command(resume="yes"), config)               # resume, even a day later
```

*Sketch for the demo: an approval node and persisted state (not in the project yet).*

**Visual (mini diagram):** reviewer → “approved” → human_approval (interrupt()) → END.

**Right:**

- **Checkpointer** saves the state after every step. Crashed at minute 18? Resume from minute 18, not from scratch.
- **interrupt()** stops the graph and waits for a human — for as long as it takes.

**Speaker notes:**

> BEFORE THE TALK: this code isn’t in the project yet. Add a human_approval node between the reviewer’s approval and END, a checkpointer (SqliteSaver from the langgraph-checkpoint-sqlite package) and a thread_id in main.py.
>
> What to say: the checkpointer saves the state after every step, so the graph survives a crash and resumes where it stopped. interrupt() stops the graph and waits for a human — for as long as needed. That’s exactly how the next demo works.

---

## 11. Demo: a run started before the talk

**Time:** 13:00–21:00 · **Layout:** Title Only

**Run task:** “Upgrade the project to Java 25 and the latest Spring Boot 3.5.x”

**Steps (a timeline of 5 circles; step 4 is teal — it happens live):**

1. **Graph in Studio** — “It ran for 20 minutes before the talk and is waiting for me now” (1 min)
2. **Thread history** — the state after every step, the failed build, the retry (3 min)
3. **LangSmith trace** — time and tokens spent on each node (1 min)
4. **Live approval** — Command(resume="yes") — the graph finishes in seconds (2 min)
5. **Takeaway** — code ran the build, not the model (1 min)

Fallback: a screen recording and screenshots in the next tab.

**Speaker notes:**

> 40–60 minutes before the talk: start a run with the task from the slide. It will reach interrupt() and wait. Disable sleep mode on the laptop and check that the thread is there before you go on stage.
>
> 1 min — graph in Studio: “it ran for 20 minutes before the talk and is waiting for me now”.
> 3 min — thread history: the state after every step, the failed build and the retry.
> 1 min — LangSmith trace: time and tokens per node.
> 2 min — live approval: graph.invoke(Command(resume="yes"), config); the graph finishes in seconds.
> 1 min — takeaway: code ran the build, not the model. That’s also why this process doesn’t belong in the IDE: you don’t want to watch an agent for 20 minutes.
>
> Fallback: a screen recording in the next tab and the log slide that follows.

---

## 12. What a run looks like

**Time:** part of the demo (13:00–21:00) · **Layout:** Title Only

```text
agent -> list_files()
agent -> read_file(path=build.gradle.kts)
agent -> get_library_version(group_id=org.springframework.boot, artifact_id=org.springframework.boot.gradle.plugin)
agent -> write_file(path=build.gradle.kts, content=...)
write_file -> agent: Written build.gradle.kts (… chars).
agent: <short summary: what was done and which assumptions were made>
gradle_build -> agent: build failed (attempt 1): <first error line>
agent -> write_file(path=build.gradle.kts, content=...)
gradle_build -> reviewer: build passed (attempt 2)
reviewer -> read_file(path=src/test/java/com/example/hello/HelloControllerTest.java)
reviewer -> agent: 1 issue (round 1)
  - (conventions, section 7) <file: what is wrong, how to fix it>
agent -> write_file(path=src/test/java/com/example/hello/HelloControllerTest.java, content=...)
gradle_build -> reviewer: build passed (attempt 1)
reviewer -> END: code approved (round 2)
```

*Example of main.py output (messages translated) — replace with an excerpt from a real run.*

**Line colors:** purple — LLM nodes (agent, reviewer); teal — the build (gradle_build); grey — tool results and review issues.

**Speaker notes:**

> Show this if the demo runs in a terminal or Studio isn’t available. BEFORE THE TALK: replace the example with an excerpt from a real log. main.py prints exactly this format, but its messages are in Russian — translate the strings in main.py if the audience needs English. Colors: purple lines are LLM nodes, teal is the build, grey is tool results and review issues.

---

## 13. A Claude Code subagent prompt → a graph node

**Time:** 21:00–22:30 · **Layout:** Title Only

**Visual (diagram):** a file card `.claude/agents/java-spring-developer.md` (“one file”) → two arrows:

- **Claude Code: a subagent** — the java-spring-dev plugin from a local marketplace
- **LangGraph: the system prompt of the agent node** — build_system_prompt() = this file + conventions.md + role

**Bottom:** conventions.md overrides the rules for the pipeline (translated):

> “There is no human around: don’t ask questions or request confirmation.”
>
> “The rules above about running ./mvnw or ./gradlew don’t apply.”

**Takeaway:** One agent — different rules for the IDE and for the pipeline.

**Speaker notes:**

> The most valuable point for this audience: the developer prompt in the graph is the same Claude Code subagent — the same file. What you’ve already invested in Claude Code carries over. Only the operating rules change: conventions.md tells the agent there’s no human around and the pipeline runs the build.

---

## 14. Hybrid: the graph runs the process, the agent writes code

**Time:** 22:30–24:00 · **Layout:** Title Only

**Left (teal card) — LangGraph owns the process:**

- build and tests
- attempt limits
- review and routing
- human approval
- persisted state

**Right (purple card) — The agent owns the code:**

- editing code
- today: create_agent from LangChain
- can be swapped for the Claude Agent SDK or claude -p with the same subagent
- the graph doesn’t change

- **MCP:** servers you already use in Claude Code plug in here too, via langchain-mcp-adapters
- **Ready-made:** deepagents (a Claude Code-style harness on LangGraph), Open SWE (an agent from issue to PR)

**Speaker notes:**

> Division of roles: the graph owns the process — checks, limits, review, pauses, persisted state. The agent owns editing code. You can swap the agent node for the Claude Agent SDK or claude -p with the same subagent, and the graph stays the same. MCP servers you already use in Claude Code plug in here as well.

---

## 15. When you don’t need LangGraph

**Time:** 24:00–25:00 · **Layout:** Title Only

| Task | Use |
|---|---|
| Interactive development, exploring code | Claude Code / Copilot in the IDE |
| A one-off task in CI | claude -p, Copilot coding agent |
| Your own agent built on the Claude Code loop | Claude Agent SDK |
| Several steps with mandatory checks, pauses and long runs | LangGraph |
| 2–3 steps, no branching | a plain Python loop |

*The LangGraph row is highlighted.*

**Right — LangGraph downsides:**

- you write the file-editing tools and the sandbox yourself
- context management, too
- it takes time to learn
- LangChain ecosystem APIs have changed often in the past

**Speaker notes:**

> Be honest — this audience will appreciate it. For interactive work Claude Code is better: its tools, context handling and history compaction are polished. LangGraph is for when there’s a process with mandatory steps.

---

## 16. A rule in the prompt is not a rule

**Time:** 25:00–26:00 · **Layout:** Title Only

| Rule | Where it lives | Status |
|---|---|---|
| Build and tests | code: the gradle_build node | guaranteed |
| Attempt limits | code: MAX_BUILD_ATTEMPTS, MAX_REVIEW_ROUNDS, recursion_limit | guaranteed |
| Stay inside the project folder | code: _resolve() in tools.py | guaranteed |
| Reviewer answer format | Pydantic schema Review | guaranteed |
| Library versions | the get_library_version tool exists, but “use it” is only in the prompt | partial |
| Don’t touch gradlew.bat and gradle/wrapper | only in the prompt | just a request |

*Statuses are color-coded: guaranteed — teal, partial — amber, just a request — red.*

Anything that must always happen — **move it from the prompt into code.**

**Speaker notes:**

> This table comes straight from our project. The top rows are guarantees in code. The bottom rows are rules that live only in the prompt — in other words, requests. Takeaway: anything that must always happen, move from the prompt into code.

---

## 17. Risks and cost

**Time:** 26:00–27:00 · **Layout:** Title Only

**No shell ≠ a sandbox.** The agent writes build.gradle.kts and tests — code that the build runs on your machine. It can also overwrite gradlew.bat. **→ run it in a container**

**Prompt injection.** The task text and repository contents end up in the prompt. A bot that opens PRs on its own is a target. **→ least-privilege tokens**

**15** agent runs in the worst case: 5 review rounds × 3 build attempts. The message history grows with every round. **→ limits, tracing, a per-run budget**

*Visual: three cards; the third one has a large number 15.*

**Speaker notes:**

> Having no shell tool isn’t a sandbox: build.gradle.kts and the tests are code that the build runs on your machine. The task text and the repository end up in the prompt — that’s a prompt injection vector. And cost: in the worst case, 5 review rounds × 3 build attempts = 15 agent runs, and the message history grows every round.

---

## 18. Takeaways

**Time:** 27:00–29:00 · **Layout:** Title Only

1. **The IDE agent is for you.** LangGraph is for a process that runs without you.
2. **Anything that must always happen —** do it in code, not by asking the model.
3. **Start with a hybrid:** the graph as the orchestrator, a proven agent as the worker.

**Speaker notes:**

> Three points — that’s what should stick. Read them slowly and pause. The spare minute is for transitions.

---

## 19. Thank you! Questions?

**Time:** Q&A, 15 minutes · **Layout:** Section Header

**Subtitle:** [contacts] · [link to the example repository]

**Speaker notes:**

> If the room is quiet, use a starter:
> — “People often ask me how this differs from the Claude Agent SDK…” (backup slide “Alternatives”).
> — “I can show the LangSmith trace of this run: what cost money and where the agent went wrong.”
> — “I can show how to roll back to an earlier state” (backup slide).
> If you started a background run at the beginning, show what it has done.

---

## 20. Backup slides

**Layout:** Section Header

**Subtitle:** for questions from the audience

**Speaker notes:**

> Show only when asked.

---

## 21. Alternatives

**Time:** backup slide · **Layout:** Title Only

| Tool | What it is | When to use |
|---|---|---|
| Claude Agent SDK | the Claude Code agent loop as a library: tools, context, subagents | you need a strong worker and no graph of your own |
| OpenAI Agents SDK | agents that hand off control to each other (handoffs) | your team is on the OpenAI stack |
| Temporal | durable execution for any code, not just LLMs | your company already runs Temporal |
| n8n | low-code automation and integrations | integrations without programming |
| LangGraph | explicit graph, state, checkpointer, interrupt(), Studio | a process with mandatory checks around an LLM |

You can combine them: the Claude Agent SDK inside a LangGraph node.

**Speaker notes:**

> Key point: these tools aren’t mutually exclusive. The Claude Agent SDK works well inside a LangGraph node.

---

## 22. Production: what to add

**Time:** backup slide · **Layout:** Title Only

- **State** — a Postgres checkpointer instead of SQLite or memory
- **Observability** — LangSmith tracing: steps, time, tokens
- **Evals** — a task set that shows a graph change didn’t make results worse
- **Cost** — recursion_limit, attempt limits, a cheap model for routing and a strong one for code
- **Isolation** — a container per run, least-privilege tokens, no secrets for the agent

**Speaker notes:**

> Answers “how do you run this for real?”. The most important parts are isolation and evals.

---

## 23. Rolling back to an earlier state (time travel)

**Time:** backup slide · **Layout:** Title Only

```python
config = {"configurable": {"thread_id": "demo-1"}}

# full history: a state snapshot after every step
for snapshot in graph.get_state_history(config):
    print(snapshot.next, snapshot.values.get("build_attempts"))

# resume from the chosen step — the graph takes a new branch
graph.invoke(None, snapshot.config)
```

*Requires a checkpointer.*

- every step is a checkpoint with the full state
- you can edit the state (update_state) and continue
- careful: from an early step the graph runs for ~20 minutes again

**Speaker notes:**

> Show the history, but don’t start a branch from an early step: the graph would run for 20 minutes again.

---

## 24. What else LangGraph has

**Time:** backup slide · **Layout:** Title Only

- **Send** — parallel fan-out: e.g. one node per file
- **Subgraphs** — a graph inside a node: our agent and reviewer are subgraphs
- **Streaming** — stream_mode="updates" and subgraphs=True — that’s how main.py prints its log
- **Studio** — graph visualization, runs, thread history
- **LangGraph.js** — the same thing in TypeScript

**Speaker notes:**

> A quick tour of features that didn’t make it into the main part.
