# Article Notes: Chapters 5 & 6 Implementation

Notes for writing the article about extending the dmas codebase with ch5 (Computer Use Agent) and ch6 (Multi-Agent Workflow Pipeline).

---

## What We Built

### Chapter 5: Computer Use Agent (Browser Automation)

A single agent that controls a headless Chromium browser via Playwright, following an observe-reason-act loop. Given a natural language task, the agent decides which browser actions to take (navigate, click, type, scroll, observe, screenshot) and iterates until the task is complete or the action limit is hit.

### Chapter 6: Multi-Agent Workflow Pipeline (Research-Draft-Review)

A 3-agent DAG pipeline: Researcher → Writer → Reviewer, with a conditional revision loop. The reviewer scores the draft (1-10); scores below 8 send the draft back to the writer with feedback. This is structurally different from ch1's round-robin — the graph has conditional edges and typed state flow.

---

## Why These Chapters

- **Ch5** introduces the observe-reason-act pattern, tool-based web interaction, and safety limits (max actions). It's a prerequisite for ch7+ which assumes browser automation capability.
- **Ch6** introduces DAG-based orchestration with conditional routing, typed state between agents, and revision loops. Distinct from ch1's round-robin — agents have specialized roles and the workflow has branching logic.
- Both chapters get all 3 framework backends (AutoGen, Agent Framework, LangGraph), matching the existing pattern from ch1 and ch4.

---

## Architecture Decisions

### Ch5: Tool closures with action counter

The 6 Playwright tool functions in `ch5/tools.py` are framework-agnostic — they take a `BrowserSession` as the first arg. Each backend creates closures that bind the session and add an action counter for `max_actions` enforcement. This keeps the tool logic in one place while letting each framework wrap them differently (AutoGen: plain functions, Agent Framework: `@tool` decorator, LangGraph: `@tool` decorator).

### Ch5: BrowserSession as async context manager

`BrowserSession` is a dataclass with `__aenter__`/`__aexit__`. It catches `ImportError` with a helpful install message if Playwright isn't installed, since it's an optional dependency (`pip install 'dmas[computer-use]'`).

### Ch6: Score parsing

All 3 backends share a `_parse_score(text) -> int` helper using regex `SCORE:\s*(\d+)`. Returns 0 on failure, which is a safe default — it triggers revision rather than falsely approving.

### Ch6: LangGraph uses StateGraph, not create_react_agent

Ch1 uses `MessagesState` with `astream(stream_mode="messages")`. Ch6 uses a custom `PipelineState` TypedDict with `ainvoke()` — streaming happens inside each node via `llm.astream()`. This is a fundamentally different LangGraph architecture (data-flow DAG vs. message-passing). Good to highlight this contrast in the article.

### Ch6: Writer session reuse (Agent Framework)

In the Agent Framework backend, the writer's session is reused across revision rounds so it accumulates context. The reviewer gets a fresh session each round to avoid bias from prior reviews.

---

## Implementation Gotchas & Fixes

### AutoGen `max_tool_iterations` (ch5)

**Problem:** The agent navigated to Hacker News, called `observe_page`, then immediately exited back to the command prompt — completing only one tool-call round.

**Root cause:** AutoGen's `AssistantAgent` defaults `max_tool_iterations=1`. With `reflect_on_tool_use=True`, each tool call consumes 2 model calls (call + reflection). After one iteration, the agent stops. Ch4 gets away with it because weather queries complete in 1-2 tool calls. Ch5's browser automation needs many sequential calls (navigate → observe → click → observe → ...).

**Fix:** Set `max_tool_iterations=max_actions` on the AssistantAgent constructor.

**Lesson:** When building tool-heavy agents in AutoGen, always set `max_tool_iterations` explicitly. The default of 1 is fine for simple single-tool agents but breaks any multi-step workflow.

### AutoGen Console verbosity (ch5)

**Problem:** AutoGen's `Console()` prints every internal event type (`ToolCallRequestEvent`, `ToolCallExecutionEvent`, full `FunctionExecutionResult` content). For `observe_page`, this dumps 3000+ characters of page text and 30 interactive elements into the terminal.

**Decision:** Added an optional `--silent` flag (default off). When enabled, the backend manually iterates the stream and only prints `[calling tool_name...]` indicators and the agent's text reasoning — matching the cleaner output of Agent Framework and LangGraph backends.

**Why default off:** The verbose Console output is useful for debugging and understanding the agent's behavior. For articles and demos, `--silent` produces cleaner output.

### AutoGen Console verbosity (ch6)

**Same problem as ch5:** `Console()` echoes the full `TextMessage (user)` blocks, which contain the research notes and draft being passed as input to the next agent. This means you see every piece of text twice — once when the agent generates it, and again when it's sent as input to the next agent.

**Fix:** Same `--silent` flag approach. In silent mode, the backend uses a `_stream_and_collect()` helper that iterates `ModelClientStreamingChunkEvent` messages only, printing the agent's generated text and returning the full collected string for passing to the next stage.

### Weather API reliability (ch4)

**Problem:** wttr.in (the primary weather API) has been down/timing out, causing ch4 to always fall through to the Open-Meteo fallback. Shipping code that hits a broken API first adds 8 seconds of latency on every weather call.

**Fix:** Swapped the call order — Open-Meteo is now primary (reliable, two-step geocode + forecast), wttr.in is now the fallback. The code structure is unchanged; only the call order in `get_weather()` was reversed. This is a zero-risk change since both APIs return the same format string.

---

## Test Results

### Ch5: Computer Use Agent

**Task:** "Go to Hacker News and list the top 5 stories with their titles and scores."

| Backend | `--max-actions` | Result |
|---------|----------------|--------|
| AutoGen (verbose) | 5 | Navigated, observed, listed 5 stories. Verbose Console output with full tool results. |
| AutoGen (silent) | 5 | Same behavior, clean output — only `[calling tool_navigate...]`, `[calling tool_observe_page...]`, then the summary. |
| Agent Framework | 5 | Navigated, observed, listed 5 stories. Clean output matching silent AutoGen. |
| LangGraph | 5 | Navigated, observed, listed 5 stories. Clean output matching silent AutoGen. |

**Observation — ordering variability:** The model interpreted "top 5" differently across runs. Some runs returned stories by page position (rank 1-5); the first AutoGen run cherry-picked high-point stories from across the page (ranks 1, 10, 17, 8, 4 — selecting by score rather than position). This is a model reasoning quirk, not a code issue. The prompt "top 5 stories" is ambiguous — top by position vs. top by score. All four runs successfully extracted real data from the live page.

**Observation — real-time data shifts:** Point counts changed between runs (583→584, 238→239) because Hacker News updates in real time. Story rankings also shifted (story #4 "Don't Make Me Talk to Your Chatbot" appeared in later runs but not the first).

### Ch6: Workflow Pipeline

**Topic:** "benefits of exercise", `--max-revisions 1`

| Backend | `--max-revisions` | Result |
|---------|-------------------|--------|
| AutoGen (verbose) | 1 | Full pipeline ran: researcher produced structured notes with headings/bullets, writer produced a multi-section report, reviewer gave SCORE: 9 and approved. Verbose Console output echoed the full research notes and draft as `TextMessage (user)` blocks between stages. |
| AutoGen (silent) | 1 | Same pipeline, clean output — only the generated text from each agent with section headers. No echoed inputs. |
| Agent Framework | 1 | Full pipeline ran successfully. Clean streaming output. Reviewer approved. |
| LangGraph | 1 | Full pipeline ran successfully via StateGraph with conditional edges. Reviewer approved. Clean streaming output from `llm.astream()` inside each node. |

**Observation — first-draft approval:** With `gpt-4.1-mini`, the reviewer consistently scored the initial draft 8+ (typically 9/10), meaning the revision loop rarely triggered. To demonstrate the revision loop for the article, you may want to either lower the approval threshold, use a stricter reviewer prompt, or use a weaker model. Alternatively, `--max-revisions 0` shows the pipeline without any revision possibility.

**Observation — AutoGen verbose vs. silent:** The verbose output is especially noisy for ch6 because the research notes (~2000 chars) get echoed as a `TextMessage` input to the writer, then the draft (~3000 chars) gets echoed as input to the reviewer. The `--silent` flag eliminates this duplication entirely.

### Regression: Ch1 + Ch4

All passing. Ch1 haiku poet/critic ran correctly with AutoGen. Ch4 weather agent returned results immediately using Open-Meteo (no 8-second wttr.in timeout).

---

## Key Differences Between Frameworks (for article comparison sections)

### Ch5 comparison

| Aspect | AutoGen | Agent Framework | LangGraph |
|--------|---------|----------------|-----------|
| Tool wrapping | Plain async closures | `@tool(description=...)` closures | `@tool` closures (docstring = description) |
| Agent creation | `AssistantAgent(tools=..., max_tool_iterations=N)` | `Agent(client, tools=...)` | `create_react_agent(llm, tools, prompt=...)` |
| Streaming | `Console()` (verbose) or manual iteration (silent) | Manual: iterate `AgentResponseUpdate` | `astream(stream_mode="messages")` |
| Key parameter | `max_tool_iterations` — must set explicitly | No equivalent needed — agent loops naturally | No equivalent needed — ReAct loop handles it |
| Boilerplate | Least (Console does everything) | Medium (manual stream + `get_final_response()`) | Medium (manual stream iteration) |

### Ch6 comparison

| Aspect | AutoGen | Agent Framework | LangGraph |
|--------|---------|----------------|-----------|
| Architecture | Sequential `Console()` calls with explicit Python loop | Sequential `_stream_and_collect()` with explicit loop | `StateGraph` with conditional edges — the DAG IS the loop |
| State management | Return values captured from `result.messages[-1].content` | Return values from `_stream_and_collect()` | `PipelineState` TypedDict flows through the graph |
| Revision loop | Python `for` loop with `break` | Python `for` loop with `break` | `should_revise()` conditional edge → "revise" or "end" |
| Streaming | `Console()` per agent call | `llm.astream()` inside helper | `llm.astream()` inside each node |
| Graph visibility | Implicit in code flow | Implicit in code flow | Explicit — `graph.add_edge()`, `graph.add_conditional_edges()` |
| Best for article | Shows AutoGen can do sequential pipelines, not just teams | Shows session management and streaming patterns | **Centerpiece** — this is what LangGraph is designed for |

---

## CLI Reference

```bash
# Ch5
python -m dmas.ch5.main --task "..." --max-actions 5 --framework autogen
python -m dmas.ch5.main --task "..." --max-actions 5 --framework autogen --silent
python -m dmas.ch5.main --task "..." --max-actions 5 --framework agent-framework
python -m dmas.ch5.main --task "..." --max-actions 5 --framework langgraph
python -m dmas.ch5.main --no-headless  # visible browser
python -m dmas.ch5.main --url "https://example.com" --task "Find the link"

# Ch6
python -m dmas.ch6.main --topic "benefits of exercise" --max-revisions 2 --framework autogen
python -m dmas.ch6.main --topic "benefits of exercise" --max-revisions 2 --framework autogen --silent
python -m dmas.ch6.main --topic "benefits of exercise" --max-revisions 2 --framework agent-framework
python -m dmas.ch6.main --topic "benefits of exercise" --max-revisions 2 --framework langgraph
```
