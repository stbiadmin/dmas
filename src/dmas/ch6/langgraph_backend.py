from __future__ import annotations

import re
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from dmas.config import get_api_key
from dmas.prompts import RESEARCHER_SYSTEM_MESSAGE, WRITER_SYSTEM_MESSAGE, REVIEWER_SYSTEM_MESSAGE


def _parse_score(text: str) -> int:
    """Extract the SCORE: N value from reviewer output. Returns 0 on failure."""
    match = re.search(r"SCORE:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


class PipelineState(TypedDict):
    topic: str
    research_notes: str
    draft: str
    review_feedback: str
    review_score: int
    revision_count: int
    max_revisions: int


async def run(topic: str, model: str, max_revisions: int = 3) -> None:
    """Run the research-draft-review pipeline using LangGraph StateGraph."""
    llm = ChatOpenAI(model=model, api_key=get_api_key(), streaming=True)

    async def researcher_node(state: PipelineState) -> dict:
        print(f"\n{'='*60}")
        print("  [researcher] Gathering research notes...")
        print(f"{'='*60}\n")

        messages = [
            SystemMessage(content=RESEARCHER_SYSTEM_MESSAGE),
            HumanMessage(content=f"Research the following topic thoroughly: {state['topic']}"),
        ]
        collected = []
        async for chunk in llm.astream(messages):
            if chunk.content:
                print(chunk.content, end="", flush=True)
                collected.append(chunk.content)
        print()
        return {"research_notes": "".join(collected)}

    async def writer_node(state: PipelineState) -> dict:
        revision_count = state.get("revision_count", 0)
        feedback = state.get("review_feedback", "")

        if feedback and revision_count > 0:
            print(f"\n{'='*60}")
            print(f"  [writer] Revising draft...")
            print(f"{'='*60}\n")
            prompt = (
                f"Revise this report based on the reviewer's feedback.\n\n"
                f"Current draft:\n{state['draft']}\n\n"
                f"Reviewer feedback:\n{feedback}"
            )
        else:
            print(f"\n{'='*60}")
            print("  [writer] Writing initial draft...")
            print(f"{'='*60}\n")
            prompt = f"Write a report based on these research notes:\n\n{state['research_notes']}"

        messages = [
            SystemMessage(content=WRITER_SYSTEM_MESSAGE),
            HumanMessage(content=prompt),
        ]
        collected = []
        async for chunk in llm.astream(messages):
            if chunk.content:
                print(chunk.content, end="", flush=True)
                collected.append(chunk.content)
        print()
        return {"draft": "".join(collected)}

    async def reviewer_node(state: PipelineState) -> dict:
        revision_count = state.get("revision_count", 0)
        print(f"\n{'='*60}")
        print(f"  [reviewer] Reviewing draft (round {revision_count + 1})...")
        print(f"{'='*60}\n")

        messages = [
            SystemMessage(content=REVIEWER_SYSTEM_MESSAGE),
            HumanMessage(content=f"Review this report:\n\n{state['draft']}"),
        ]
        collected = []
        async for chunk in llm.astream(messages):
            if chunk.content:
                print(chunk.content, end="", flush=True)
                collected.append(chunk.content)
        print()

        review_text = "".join(collected)
        score = _parse_score(review_text)
        print(f"\n  >> Score: {score}/10")

        return {
            "review_feedback": review_text,
            "review_score": score,
            "revision_count": revision_count + 1,
        }

    def should_revise(state: PipelineState) -> str:
        if state["review_score"] >= 8:
            print("  >> Report APPROVED")
            return "end"
        if state["revision_count"] >= state["max_revisions"]:
            print("  >> Max revisions reached — accepting current draft")
            return "end"
        print(f"  >> Revisions needed (attempt {state['revision_count']}/{state['max_revisions']})")
        return "revise"

    graph = StateGraph(PipelineState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "reviewer")
    graph.add_conditional_edges("reviewer", should_revise, {"revise": "writer", "end": END})

    app = graph.compile()

    initial_state: PipelineState = {
        "topic": topic,
        "research_notes": "",
        "draft": "",
        "review_feedback": "",
        "review_score": 0,
        "revision_count": 0,
        "max_revisions": max_revisions,
    }

    await app.ainvoke(initial_state)
