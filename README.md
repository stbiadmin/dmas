# dmas

Companion code for [Designing Multi-Agent Systems](https://multiagentbook.com/) by Victor Dibia. This repository re-implements the book's Chapter 1 and Chapter 4 examples as standalone applications supporting three agent frameworks: [AutoGen](https://github.com/microsoft/autogen), [Microsoft Agent Framework](https://pypi.org/project/agent-framework/), and [LangGraph](https://github.com/langchain-ai/langgraph).

## Project Structure

```
dmas/
├── pyproject.toml                       # Package config, optional deps per framework
├── .env.example                         # Template for required env vars
├── src/
│   └── dmas/
│       ├── config.py                    # Shared config (env + API key loading)
│       ├── prompts.py                   # Shared system message constants
│       ├── frameworks.py                # Framework enum + banner printer
│       ├── ch1/
│       │   ├── main.py                  # CLI entry point with --framework dispatch
│       │   ├── autogen_backend.py       # AutoGen implementation
│       │   ├── agentframework_backend.py # Microsoft Agent Framework implementation
│       │   └── langgraph_backend.py     # LangGraph implementation
│       └── ch4/
│           ├── tools.py                 # Framework-agnostic tool logic
│           ├── main.py                  # CLI entry point with --framework dispatch
│           ├── autogen_backend.py       # AutoGen implementation
│           ├── agentframework_backend.py # Microsoft Agent Framework implementation
│           └── langgraph_backend.py     # LangGraph implementation
```

## Setup

**Prerequisites:** [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html), Python 3.10+, and an OpenAI API key.

```bash
# Create and activate the conda environment
conda create -n dmas python=3.10 -y
conda activate dmas

# Install with all frameworks
pip install -e ".[all]"

# Or install individual frameworks
pip install -e ".[autogen]"
pip install -e ".[agent-framework]"
pip install -e ".[langgraph]"

# Set up your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

Both workflows accept a `--framework` flag to select the backend:

| Flag Value          | Framework                    |
|---------------------|------------------------------|
| `autogen` (default) | AutoGen 0.7+                 |
| `agent-framework`   | Microsoft Agent Framework RC |
| `langgraph`         | LangGraph                    |

### Chapter 1: Haiku Poet/Critic Team

A round-robin team where a poet writes haikus and a critic provides feedback. The conversation continues until the critic responds with APPROVE or the message limit is reached. Output is streamed token-by-token.

```bash
# AutoGen (default)
python -m dmas.ch1.main --topic "the ocean at midnight"

# Microsoft Agent Framework
python -m dmas.ch1.main --topic "the ocean at midnight" --framework agent-framework

# LangGraph
python -m dmas.ch1.main --topic "the ocean at midnight" --framework langgraph
```

### Chapter 4: Weather and Math Agent

A single agent with access to weather lookup (via wttr.in) and math evaluation tools, backed by conversation memory. Supports single-turn and multi-turn modes with token-level streaming.

```bash
# Single-turn: check weather for a specific city
python -m dmas.ch4.main --city "Tokyo"
python -m dmas.ch4.main --city "Tokyo" --framework agent-framework
python -m dmas.ch4.main --city "Tokyo" --framework langgraph

# Single-turn: random city
python -m dmas.ch4.main

# Multi-turn: demonstrates memory persistence across three conversation turns
python -m dmas.ch4.main --multi-turn
python -m dmas.ch4.main --multi-turn --framework agent-framework
python -m dmas.ch4.main --multi-turn --framework langgraph
```

The `--multi-turn` flag runs a three-turn conversation:

1. The user introduces themselves and states where they live.
2. The user asks about the weather "where I live" (the agent recalls the city from context).
3. The user asks a math question (the agent uses the calculate tool).

### Running under `conda run`

If you prefer not to activate the environment, use `--no-capture-output` so streaming displays in real time:

```bash
conda run --no-capture-output -n dmas python -m dmas.ch1.main --topic "the ocean at midnight"
conda run --no-capture-output -n dmas python -m dmas.ch4.main --multi-turn --framework langgraph
```

## Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `OPENAI_API_KEY`    | Yes      | Your OpenAI API key |

Both entry points accept a `--model` flag (default: `gpt-4.1-mini`).

## Dependencies

Base dependencies (always installed):

- [python-dotenv](https://pypi.org/project/python-dotenv/) >= 1.0
- [requests](https://pypi.org/project/requests/) >= 2.31

Framework extras:

- **`.[autogen]`**: [autogen-agentchat](https://pypi.org/project/autogen-agentchat/) >= 0.7, [autogen-ext\[openai\]](https://pypi.org/project/autogen-ext/) >= 0.7
- **`.[agent-framework]`**: [agent-framework](https://pypi.org/project/agent-framework/) >= 1.0.0rc1
- **`.[langgraph]`**: [langgraph](https://pypi.org/project/langgraph/) >= 0.2, [langchain-openai](https://pypi.org/project/langchain-openai/) >= 0.3

## License

This project is for educational purposes, accompanying the *Designing Multi-Agent Systems* book.
