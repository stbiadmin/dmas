# dmas

Companion code for [Designing Multi-Agent Systems](https://multiagentbook.com/) by Victor Dibia. This repository re-implements the book's Chapter 1 and Chapter 4 examples as production-quality, standalone applications using [Microsoft AutoGen](https://github.com/microsoft/autogen) (v0.4+).

## Project Structure

```
dmas/
├── pyproject.toml                # Package config, dependencies, entry points
├── .env.example                  # Template for required env vars
├── src/
│   └── dmas/
│       ├── config.py             # Shared config (model client factory, env loading)
│       ├── ch1/
│       │   ├── agents.py         # Poet and Critic agent definitions
│       │   ├── team.py           # RoundRobinGroupChat setup + termination
│       │   └── main.py           # CLI entry point for the haiku collaboration
│       └── ch4/
│           ├── tools.py          # Tool functions (get_weather, calculate)
│           ├── agents.py         # Assistant agent with tools, memory, streaming
│           └── main.py           # CLI entry point for the weather/math agent
```

## Setup

**Prerequisites:** [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html), Python 3.10+, and an OpenAI API key.

```bash
# Create and activate the conda environment
conda create -n dmas python=3.10 -y
conda activate dmas

# Install the package in editable mode (pulls all dependencies)
pip install -e .

# Set up your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Chapter 1: Haiku Poet/Critic Team

A round-robin team where a poet writes haikus and a critic provides feedback. The conversation continues until the critic responds with APPROVE or the message limit is reached. Output is streamed token-by-token.

```bash
python -m dmas.ch1.main --topic "the ocean at midnight"
python -m dmas.ch1.main --topic "Star Wars and Imperialism" --model gpt-4.1-mini
```

### Chapter 4: Weather and Math Agent

A single agent with access to weather lookup (via wttr.in) and math evaluation tools, backed by conversation memory. Supports single-turn and multi-turn modes with token-level streaming.

```bash
# Single-turn: check weather for a specific city
python -m dmas.ch4.main --city "Tokyo"

# Single-turn: random city
python -m dmas.ch4.main

# Multi-turn: demonstrates memory persistence across three conversation turns
python -m dmas.ch4.main --multi-turn
```

The `--multi-turn` flag runs a three-turn conversation:

1. The user introduces themselves and states where they live.
2. The user asks about the weather "where I live" (the agent recalls the city from context).
3. The user asks a math question (the agent uses the calculate tool).

### Running under `conda run`

If you prefer not to activate the environment, use `--no-capture-output` so streaming displays in real time:

```bash
conda run --no-capture-output -n dmas python -m dmas.ch1.main --topic "the ocean at midnight"
conda run --no-capture-output -n dmas python -m dmas.ch4.main --multi-turn
```

## Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `OPENAI_API_KEY`    | Yes      | Your OpenAI API key |

Both entry points accept a `--model` flag (default: `gpt-4.1-mini`).

## Dependencies

- [autogen-agentchat](https://pypi.org/project/autogen-agentchat/) >= 0.7
- [autogen-ext[openai]](https://pypi.org/project/autogen-ext/) >= 0.7
- [python-dotenv](https://pypi.org/project/python-dotenv/) >= 1.0
- [requests](https://pypi.org/project/requests/) >= 2.31

## License

This project is for educational purposes, accompanying the *Designing Multi-Agent Systems* book.
