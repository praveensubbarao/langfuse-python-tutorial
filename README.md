# Langfuse Python Tutorial

A hands-on, three-day learning path for [Langfuse](https://langfuse.com) — an open-source LLM observability and tracing platform. All examples use a **QA Architect chatbot** as the domain so concepts stay concrete and consistent across the progression.

---

## What you will learn

| Day | Theme | What you build |
|-----|-------|----------------|
| Day 1 | Core tracing | First traces, spans, generations, sessions, async, FastAPI |
| Day 2 | Scoring & prompt management | Numeric/boolean/LLM-judge scores, prompt versioning |
| Day 3 | Datasets & experiments | Eval datasets, A/B experiments, golden sets, cost tracking |

---

## Prerequisites

- Python 3.10+
- A free [Langfuse Cloud](https://cloud.langfuse.com) account (or self-hosted instance)
- [Ollama](https://ollama.com) running locally for most examples (`mistral` or `llama3.2`)
- An OpenAI API key only for `basic_tracing.py` and `llm_pipeline.py`

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd langfuse-python-tutorial
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` (or create `.env` from scratch) at the repo root:

```bash
# Langfuse credentials — from your Langfuse project settings
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"

# Ollama local LLM — used by most examples
OLLAMA_BASE_URL="http://localhost:11434/v1"
OLLAMA_MODEL="mistral"

# OpenAI — only needed for basic_tracing.py and llm_pipeline.py
OPENAI_API_KEY="sk-..."
```

### 3. Start Ollama

```bash
ollama pull mistral          # or: ollama pull llama3.2
ollama serve                 # starts on http://localhost:11434

# Verify it's running
curl http://localhost:11434/v1/models
```

### 4. Run an example

```bash
# From the repo root
python examples/01_first_trace.py
```

> **Note on `.env` path**: Most numbered examples (`01_day2_*.py` etc.) call `load_dotenv("../.env")` — they expect to be run from the repo root (not from inside `examples/`). The reference examples (`basic_tracing.py`, `llm_pipeline.py`) use `load_dotenv()` which searches upward automatically.

---

## Example Catalog

### Reference examples (start here)

Clean, standalone examples that work with OpenAI. Good first read before diving into the numbered series.

| File | What it demonstrates |
|------|----------------------|
| [examples/basic_tracing.py](examples/basic_tracing.py) | Minimal `@observe` decorator quickstart — one trace, nested span, one generation |
| [examples/llm_pipeline.py](examples/llm_pipeline.py) | Full RAG pipeline: retrieval → rerank → generation, plus post-hoc scoring |

---

### Day 1 — Core Tracing

Learn the two tracing APIs (decorator and context manager), attach metadata, handle errors, group turns into sessions, go async, and integrate with FastAPI.

| File | Key concept |
|------|-------------|
| [examples/01_first_trace.py](examples/01_first_trace.py) | `@observe` + `propagate_attributes` — the v4 pattern for attaching `user_id`, `tags`, `trace_name` to a trace |
| [examples/02_context_managers.py](examples/02_context_managers.py) | Low-level `langfuse.start_as_current_observation()` — root span → child retrieval span → child generation |
| [examples/04_observe_decorator.py](examples/04_observe_decorator.py) | Decorator pipeline: three `@observe` functions auto-nest into a parent/child hierarchy |
| [examples/05_rich_generations.py](examples/05_rich_generations.py) | `langfuse.openai` drop-in wrapper — automatic generation tracing with no manual `update_current_generation` calls |
| [examples/06_error_handling.py](examples/06_error_handling.py) | Marking spans `level="ERROR"` for failed steps; graceful degradation so the LLM still answers |
| [examples/07_qa_architect_pipeline.py](examples/07_qa_architect_pipeline.py) | `capture_input=False / capture_output=False` to suppress auto-capture; manual `update_current_generation` for full control |
| [examples/08_sessions.py](examples/08_sessions.py) | `session_id` — group multiple traces from the same conversation under one Langfuse session |
| [examples/09_chatbot_session.py](examples/09_chatbot_session.py) | Stateful chatbot class with growing message history; each turn is its own trace sharing a `session_id` |
| [examples/10_async_chatbot.py](examples/10_async_chatbot.py) | `@observe` on `async def` — async retrieval + async LLM call with child spans preserved correctly |
| [examples/06_fastapiapp.py](examples/06_fastapiapp.py) | FastAPI integration: `@observe` on route handler, `/ask` and `/feedback` endpoints, `get_current_trace_id()` returned in response |
| [examples/01_capstone_qa_chatbot.py](examples/01_capstone_qa_chatbot.py) | **Day 1 capstone** — fully instrumented chatbot combining all Day 1 concepts |

---

### Day 2 — Scoring & Prompt Management

Attach quality scores to traces (numeric, boolean, LLM-as-judge), and manage prompts as versioned, labelled assets in Langfuse.

#### Scoring

| File | Key concept |
|------|-------------|
| [examples/01_day2_numericscore.py](examples/01_day2_numericscore.py) | `score_current_span` and `score_current_trace` with `data_type="NUMERIC"` — length and structure scores |
| [examples/02_day2_boolean_score.py](examples/02_day2_boolean_score.py) | Interactive user feedback (`y/n`) scored as `data_type="BOOLEAN"` on a span |
| [examples/01_day2_customerjudge.py](examples/01_day2_customerjudge.py) | LLM-as-a-judge: second LLM call evaluates the first; score posted with `score_current_trace` |

#### Prompt Management

| File | Key concept |
|------|-------------|
| [examples/01_day2_create_prompts.py](examples/01_day2_create_prompts.py) | `langfuse.create_prompt()` — create text and chat prompt types with `{{variables}}`, config, and `production` label |
| [examples/02_day2_getprompt.py](examples/02_day2_getprompt.py) | `langfuse.get_prompt()` + `.compile()` — fetch by label or version, fill variables, read model config |
| [examples/03_day2_linkedtracewithprompts.py](examples/03_day2_linkedtracewithprompts.py) | `prompt=prompt_obj` in `update_current_generation` — links every generation trace to the exact prompt version used |
| [examples/04_day2_createpromptanddynamicuse.py](examples/04_day2_createpromptanddynamicuse.py) | Prompt versioning lifecycle: create v2 in `staging`, promote to `production`, run same code with zero redeploy |

---

### Day 3 — Datasets, Experiments & Cost Tracking

Build an evaluation dataset, run prompt A/B experiments, grow a golden set from production thumbs-ups, integrate LangChain, and track token costs.

| File | Key concept |
|------|-------------|
| [examples/01_day3_dataset.py](examples/01_day3_dataset.py) | `langfuse.create_dataset()` and `create_dataset_item()` — build an eval dataset with inputs and expected-output criteria |
| [examples/02_day3_experimentwithdataset.py](examples/02_day3_experimentwithdataset.py) | `dataset.run_experiment()` — run two prompt versions (v1 baseline vs v2 structured) against the dataset and compare scores |
| [examples/03_day3_promotegoldenset.py](examples/03_day3_promotegoldenset.py) | Query production traces with `user_feedback=1`; promote each to the eval dataset as a golden example |
| [examples/04_day3_langchain.py](examples/04_day3_langchain.py) | LangChain integration via `langfuse.langchain.CallbackHandler` — whole chain auto-traced with one line |
| [examples/07_day3_costtracking.py](examples/07_day3_costtracking.py) | `cost_details` in `update_current_generation` — token counts and simulated dollar costs visible in Langfuse dashboard |
| [examples/final_captsone.py](examples/final_captsone.py) | **Final capstone** — production-grade chatbot combining prompt management, auto-scoring, user feedback, and session tracking |

---

## Key API Patterns (SDK v4)

### Always use `get_client()`, never `Langfuse()`

```python
from dotenv import load_dotenv
load_dotenv()                     # must come before SDK imports

from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()           # module-level singleton
```

### `@observe` decorator (recommended)

```python
@observe(name="pipeline")         # outermost = trace root
def run_pipeline(question: str) -> str:
    context = retrieve(question)
    return call_llm(context, question)

@observe(as_type="span", name="retrieve")
def retrieve(query: str) -> list[str]:
    return ["relevant doc..."]

@observe(as_type="generation", name="llm-call")
def call_llm(context: list, question: str) -> str:
    response = client.chat.completions.create(...)
    langfuse.update_current_generation(
        model="mistral", output=response.choices[0].message.content,
        usage_details={"input_tokens": ..., "output_tokens": ...},
    )
    return response.choices[0].message.content
```

### `propagate_attributes` for trace metadata

```python
with propagate_attributes(
    trace_name="My Pipeline",
    user_id="user-123",
    session_id=session_id,
    tags=["prod", "qa"],
    metadata={"version": "1.0"},   # values must be strings
):
    result = run_pipeline(question)
```

### Always flush at script exit

```python
langfuse.flush()   # required — events are sent asynchronously
```

---

## Project Structure

```
.
├── examples/
│   ├── basic_tracing.py             # reference: minimal quickstart (OpenAI)
│   ├── llm_pipeline.py              # reference: full RAG pipeline (OpenAI)
│   ├── 01_first_trace.py            # Day 1: first trace
│   ├── 02_context_managers.py       # Day 1: low-level context manager API
│   ├── 04_observe_decorator.py      # Day 1: decorator pipeline
│   ├── 05_rich_generations.py       # Day 1: langfuse.openai wrapper
│   ├── 06_error_handling.py         # Day 1: error spans
│   ├── 06_fastapiapp.py             # Day 1: FastAPI integration
│   ├── 07_qa_architect_pipeline.py  # Day 1: manual generation control
│   ├── 08_sessions.py               # Day 1: session_id grouping
│   ├── 09_chatbot_session.py        # Day 1: stateful chatbot
│   ├── 10_async_chatbot.py          # Day 1: async @observe
│   ├── 01_capstone_qa_chatbot.py    # Day 1 capstone
│   ├── 01_day2_numericscore.py      # Day 2: numeric scores
│   ├── 02_day2_boolean_score.py     # Day 2: boolean feedback scores
│   ├── 01_day2_customerjudge.py     # Day 2: LLM-as-judge
│   ├── 01_day2_create_prompts.py    # Day 2: create prompts
│   ├── 02_day2_getprompt.py         # Day 2: fetch & compile prompts
│   ├── 03_day2_linkedtracewithprompts.py  # Day 2: link trace to prompt version
│   ├── 04_day2_createpromptanddynamicuse.py  # Day 2: prompt versioning
│   ├── 01_day3_dataset.py           # Day 3: create eval dataset
│   ├── 02_day3_experimentwithdataset.py  # Day 3: A/B prompt experiments
│   ├── 03_day3_promotegoldenset.py  # Day 3: promote production traces
│   ├── 04_day3_langchain.py         # Day 3: LangChain integration
│   ├── 07_day3_costtracking.py      # Day 3: cost tracking
│   └── final_captsone.py            # Final capstone
├── .claude/
│   └── skills/langfuse-tracing/
│       └── SKILL.md                 # tracing best practices & checklist
├── Tutorial Documentation/          # original HTML tutorial docs (reference)
├── requirements.txt
├── CLAUDE.md
└── .env                             # credentials (gitignored)
```

---

## Dependencies

```
langfuse>=3.0.0
openai>=1.0.0
python-dotenv>=1.0.0
```

Day 3 LangChain example also requires:
```bash
pip install langchain langchain-openai
```

---

## LLM Mental Model for QA Engineers

The LinkedIn post in [Tutorial Documentation/LinkedIn Post.md](Tutorial%20Documentation/LinkedIn%20Post.md) maps Langfuse concepts to familiar QA vocabulary:

| Traditional QA | Langfuse equivalent |
|---------------|---------------------|
| Test logs | Traces |
| Test assertions | Scores |
| Regression suite | Dataset experiments |
| Manual test cases | Golden set (production-promoted) |
| CI cost report | Token + cost dashboard |

---

## Troubleshooting

**Ollama not responding**
```bash
lsof -i :11434          # find the PID if stuck
kill <pid>
ollama serve            # restart
```

**Events not appearing in Langfuse dashboard**
- Ensure `langfuse.flush()` is called before script exit
- Verify `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_BASE_URL` are set

**`load_dotenv` not finding `.env`**
- Run scripts from the repo root: `python examples/01_first_trace.py`
- Day 2/3 examples use `load_dotenv("../.env")` which resolves relative to the script; running from the repo root works correctly

**Upgrading packages**
```bash
pip install --upgrade langfuse openai
```
