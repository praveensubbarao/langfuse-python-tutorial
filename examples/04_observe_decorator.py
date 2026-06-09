from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import observe, get_client, propagate_attributes
from langfuse.openai import OpenAI

langfuse = get_client()
client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")


@observe(name="retrieve-docs")  # creates a SPAN automatically
def retrieve_context(query: str) -> list[str]:
    # Function args become the span input, return value becomes output
    # Simulate retrieval (replace with real vector DB in your app)
    return [
        f"Test technique relevant to: {query}",
        "Edge cases should always be tested at boundaries.",
    ]


@observe(name="llm-generation")
def generate_answer(question: str, context: list[str]) -> str:
    system = "You are a QA Architect. Use the context to answer concisely."
    user_msg = f"Context:\n{chr(10).join(context)}\n\nQuestion: {question}"

    # Update the generation with structured input for better UI display
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        model_parameters={"temperature": 0.5},
        input={"system": system, "user": user_msg},
    )

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content


@observe(name="qa-pipeline-1")  # top-level trace
def run_qa_pipeline(question: str) -> str:
    # Each call below automatically becomes a CHILD of this function's span
    context = retrieve_context(question)
    answer  = generate_answer(question, context)
    return answer


# propagate_attributes wraps the TOP-LEVEL call (the correct v4 pattern)
if __name__ == "__main__":
    with propagate_attributes(
        trace_name="QA Architect Query",
        user_id="user-123",
        tags=["qa", "decorator-demo"],
        metadata={"tutorial": "day1-hour2"},
    ):
        result = run_qa_pipeline("Explain equivalence partitioning.")

    print(result)
    langfuse.flush()
