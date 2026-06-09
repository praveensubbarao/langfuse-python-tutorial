from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import get_client, propagate_attributes
from langfuse.openai import OpenAI

langfuse = get_client()

client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    api_key="ollama",
)

# ─────────────────────────────────────────────────────────────
# FULL TRACE: root span → retrieval span → generation (nested)
# ─────────────────────────────────────────────────────────────
with propagate_attributes(
    trace_name="qa-pipeline",
    user_id="user-123",
    tags=["qa", "hour-2"],
    metadata={"tutorial": "day1-hour2"},
):
    # Root span — this DEFINES the trace
    with langfuse.start_as_current_observation(
        as_type="span",
        name="handle-user-question",
        input={"question": "What is boundary value analysis?"},
    ) as root_span:

        # ── Step 1: Simulate document retrieval ──────────────────
        with langfuse.start_as_current_observation(
            as_type="span",
            name="retrieve-context",
            input={"query": "boundary value analysis"},
        ) as retrieval_span:

            # Simulate finding relevant docs (no real DB needed)
            fake_docs = [
                "BVA tests at the edges of input domains...",
                "Equivalence partitioning divides inputs into classes...",
            ]
            retrieval_span.update(
                output={"chunks_found": 2, "docs": fake_docs},
                metadata={"source": "knowledge-base"},
            )

        # ── Step 2: LLM generation (child of root, sibling of retrieval) ─
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="generate-answer",
            model=os.getenv("OLLAMA_MODEL"),
            model_parameters={"temperature": 0.3},
            input={
                "system": "You are a QA expert. Use the context provided.",
                "context": fake_docs,
                "user": "What is boundary value analysis?",
            },
        ) as gen:

            response = client.chat.completions.create(
                model=os.getenv("OLLAMA_MODEL"),
                messages=[
                    {"role": "system", "content": "You are a QA expert."},
                    {"role": "user",   "content": "What is boundary value analysis?"},
                ],
                temperature=0.3,
            )
            answer = response.choices[0].message.content

            # Update generation with the output after the call
            gen.update(output=answer)

        # ── Step 3: Set final trace output ───────────────────────────
        root_span.update(output={"answer": answer})

print("Answer:", answer)
langfuse.flush()
