from dotenv import load_dotenv
import os, uuid
load_dotenv()

from langfuse import observe, get_client, propagate_attributes
from openai import OpenAI   # ← plain openai (no double-generation)

langfuse = get_client()
client  = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

SYSTEM = "You are a QA Architect. Answer concisely in 2-3 sentences."


@observe(name="qa-turn", as_type="generation")
def ask_question(question: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": question},
        ],
    )
    answer = response.choices[0].message.content
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[{"role": "user", "content": question}],
        output=answer,
        usage_details={
            "input_tokens":  response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    )
    return answer


if __name__ == "__main__":
    # Generate one session_id for this entire conversation
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    user_id    = "user-123"
    print(f"Session: {session_id}\n")

    questions = [
        "What is boundary value analysis?",
        "Give me a real-world example of it.",
        "How is it different from equivalence partitioning?",
    ]

    for i, question in enumerate(questions, 1):
        # Each question = one trace, all share the same session_id
        with propagate_attributes(
            trace_name=f"Turn {i}: {question[:30]}...",
            session_id=session_id,       # ← same for all turns
            user_id=user_id,
            tags=["qa", "session-demo"],
            metadata={"turn": str(i)},
        ):
            answer = ask_question(question)
            print(f"Q{i}: {question}")
            print(f"A{i}: {answer[:120]}...\n")

    langfuse.flush()
    print(f"✓ 3 traces sent. Find session '{session_id}' in Langfuse → Sessions.")
