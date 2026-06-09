from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import observe, get_client, propagate_attributes
from langfuse.openai import OpenAI

langfuse = get_client()
client  = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

# Simulated knowledge base
KNOWLEDGE_BASE = {
    "boundary value analysis": [
        "Test at exact boundaries and just outside them.",
        "For input 1-100: test 0, 1, 2, 99, 100, 101.",
    ],
    "equivalence partitioning": [
        "Divide inputs into classes that should behave identically.",
        "Test one value from each partition (valid and invalid).",
    ],
    "default": ["General QA knowledge base. No specific context found."],
}

SYSTEM_PROMPT = (
    "You are an experienced QA Architect with 20 years of software "
    "industry experience. Provide concise, practical answers with examples."
)


@observe(name="qa-knowledge-retrieval", capture_output=False)
def retrieve_knowledge(query: str) -> list[str]:
    query_lower = query.lower()
    for key, docs in KNOWLEDGE_BASE.items():
        if key in query_lower:
            langfuse.update_current_span(
                output={"matched_key": key, "chunks": len(docs)},
                metadata={"source": "local-kb"},
            )
            return docs
    langfuse.update_current_span(output={"matched_key": "default", "chunks": 1})
    return KNOWLEDGE_BASE["default"]


@observe(name="llm-answer", as_type="generation", capture_input=False, capture_output=False)
def generate_qa_answer(question: str, context: list[str]) -> str:
    context_text = "\n".join(f"- {c}" for c in context)
    user_msg = f"Context:\n{context_text}\n\nQuestion: {question}"

    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        model_parameters={"temperature": 0.3, "max_tokens": 500},
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        metadata={"prompt_version": "2.0", "context_used": "true"},
    )

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    answer = response.choices[0].message.content

    langfuse.update_current_generation(
        output=answer,
        usage_details={
            "input_tokens":  response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    )
    return answer


@observe(name="qa-architect-knowledge-pipeline")
def qa_architect_query(question: str) -> str:
    context = retrieve_knowledge(question)
    answer  = generate_qa_answer(question, context)
    return answer


if __name__ == "__main__":
    questions = [
        "Explain boundary value analysis with an example.",
        "How do you prioritise test cases in an Agile sprint?",
    ]

    for q in questions:
        with propagate_attributes(
            trace_name="QA Architect Assistant",
            user_id="user-123",
            tags=["qa", "architect", "hour2-project"],
            metadata={
                "sdk_version": "4.7.1",
                "use_case": "qa-education",
            },
        ):
            result = qa_architect_query(q)
            print(f"\nQ: {q}\nA: {result[:200]}...\n")

    langfuse.flush()
    print("\n✓ All 3 traces sent to Langfuse. Check your dashboard!")
