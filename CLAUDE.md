# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a tutorial project for learning the [Langfuse](https://langfuse.com) Python SDK — an open-source LLM observability and tracing platform.

## Environment Setup

Copy `.env` and populate with your Langfuse credentials before running any code:

```
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

Load the env file at the start of scripts (e.g., via `python-dotenv`):

```python
from dotenv import load_dotenv
load_dotenv()
```

## Key Dependencies

```bash
pip install -r requirements.txt
# or: pip install langfuse openai python-dotenv
```

## Langfuse Tracing Skill

Tracing best practices, checklists, and patterns are documented in the project skill:

> [.claude/skills/langfuse-tracing/SKILL.md](.claude/skills/langfuse-tracing/SKILL.md)

Read that file before adding or modifying any Langfuse instrumentation.

## Langfuse Tracing Pattern (SDK ≥ 3.x)

Use `get_client()` (not the `Langfuse()` constructor) and `@observe` from `langfuse`:

```python
from dotenv import load_dotenv
load_dotenv()  # always before SDK imports

from langfuse import get_client, observe
from langfuse.decorators import langfuse_context

langfuse = get_client()  # single module-level instance

@observe(name="my-pipeline")
def my_pipeline(user_id: str, query: str) -> str:
    langfuse_context.update_current_trace(user_id=user_id)
    return call_llm(query)

@observe(as_type="generation", name="llm-call")
def call_llm(query: str) -> str:
    # ... call OpenAI/Anthropic, then update model+usage ...
    return "answer"

my_pipeline("u1", "Hello")
langfuse.flush()  # required before script exit
```

See [examples/basic_tracing.py](examples/basic_tracing.py) for a minimal runnable example and
[examples/llm_pipeline.py](examples/llm_pipeline.py) for a full RAG pipeline with scoring.

## Project Structure

```
.
├── .claude/
│   └── skills/
│       └── langfuse-tracing/
│           └── SKILL.md          # tracing best practices & checklist
├── examples/
│   ├── basic_tracing.py          # @observe decorator quickstart
│   └── llm_pipeline.py           # RAG pipeline with spans, generations, scores
├── requirements.txt
└── .env                          # Langfuse credentials (gitignored)
```
