"""
Full RAG-style pipeline with Langfuse tracing (SDK v4+).

Demonstrates:
  - Multi-step traces: retrieval → rerank → generation
  - session_id for grouping multi-turn conversations
  - Scoring a trace after the fact (simulated user feedback)
  - Low-level context-manager API alongside @observe decorators

Run:
    .venv/bin/python examples/llm_pipeline.py
"""

from dotenv import load_dotenv
load_dotenv()

import openai
from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()


# ---------------------------------------------------------------------------
# Retrieval step — non-LLM, so as_type="retriever"
# ---------------------------------------------------------------------------

@observe(as_type="retriever", name="vector-retrieval")
def retrieve_docs(query: str) -> list[str]:
    """Fetch candidate documents for the query (simulated)."""
    langfuse.update_current_span(
        input={"query": query},
        metadata={"index": "demo-corpus", "top_k": 5},
    )
    docs = [
        "Langfuse is an open-source LLM observability platform.",
        "It supports traces, spans, generations, and scores.",
        "Integrates with OpenAI, Anthropic, LangChain, and more.",
    ]
    langfuse.update_current_span(output={"doc_count": len(docs)})
    return docs


# ---------------------------------------------------------------------------
# Re-ranking step
# ---------------------------------------------------------------------------

@observe(as_type="span", name="rerank")
def rerank_docs(query: str, docs: list[str]) -> list[str]:
    """Re-rank retrieved docs by relevance (simulated)."""
    langfuse.update_current_span(metadata={"strategy": "simulated-bm25"})
    return docs[:2]  # keep top-2


# ---------------------------------------------------------------------------
# Generation step — as_type="generation" unlocks model/token/cost tracking
# ---------------------------------------------------------------------------

@observe(as_type="generation", name="openai-rag-generation")
def generate_answer(query: str, context_docs: list[str]) -> str:
    """Synthesise an answer from the retrieved context."""
    context = "\n".join(f"- {d}" for d in context_docs)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer using only the provided context. "
                "Be concise.\n\nContext:\n" + context
            ),
        },
        {"role": "user", "content": query},
    ]

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
    )
    answer = response.choices[0].message.content

    # Attach model and token data so Langfuse can compute cost automatically
    langfuse.update_current_generation(
        model=response.model,
        input=messages,
        output=answer,
        usage_details={
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
        model_parameters={"temperature": 0},
    )
    return answer


# ---------------------------------------------------------------------------
# Root pipeline — outermost @observe creates the trace
# ---------------------------------------------------------------------------

@observe(name="rag-pipeline")
def rag_pipeline(user_id: str, session_id: str, query: str) -> str:
    """
    Full RAG pipeline: retrieve → rerank → generate.

    propagate_attributes sets user_id and session_id on all child spans so
    Langfuse can group traces by user/session and compute per-user costs.
    Must be called as early as possible — spans created before entering the
    context will NOT have these attributes.
    """
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=["rag", "demo"],
        metadata={"pipeline_version": "1.0"},
    ):
        docs = retrieve_docs(query)
        top_docs = rerank_docs(query, docs)
        return generate_answer(query, top_docs)


# ---------------------------------------------------------------------------
# Scoring — attach user feedback to a specific trace after the fact
# ---------------------------------------------------------------------------

def record_feedback(trace_id: str, thumbs_up: bool) -> None:
    """Record user feedback as a numeric score on the trace."""
    langfuse.score(
        trace_id=trace_id,
        name="user-feedback",
        value=1.0 if thumbs_up else 0.0,
        comment="Thumbs up" if thumbs_up else "Thumbs down",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Use a context-manager span at the top to capture the trace_id for scoring
    with langfuse.start_as_current_observation(as_type="span", name="session-root") as root:
        trace_id = langfuse.get_current_trace_id()

        answer = rag_pipeline(
            user_id="user-456",
            session_id="session-xyz-001",
            query="How does Langfuse help with LLM observability?",
        )

    print("Answer:", answer)
    print("Trace ID:", trace_id)

    # Simulate positive user feedback attached to this trace
    record_feedback(trace_id=trace_id, thumbs_up=True)

    # Always flush at the end of scripts — events are buffered asynchronously
    langfuse.flush()
