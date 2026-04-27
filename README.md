# Claude Tool Agent

A tool-use agent powered by the Claude API. The agent can call tools autonomously to answer your questions.

## Available Tools

- **calculate** — Evaluate math expressions (e.g., `2**10 + 15`)
- **get_current_time** — Get the current time in a specific timezone
- **read_file** — Read local file contents

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
python -m agent.cli
```

Then ask questions like:
- "What time is it in Tokyo?"
- "Calculate 2^10 + 15"
- "Read the contents of pyproject.toml"
