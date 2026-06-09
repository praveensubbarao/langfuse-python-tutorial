from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")


def compute_length_score(text: str, target_words: int = 100) -> float:
    """Score 0-1: how close the response length is to the target."""
    word_count = len(text.split())
    ratio = word_count / target_words
    # Perfect score at target, decreases for too short or too long
    return round(max(0.0, 1.0 - abs(1.0 - ratio)), 3)


def compute_structure_score(text: str) -> float:
    """Score 0-1: does the response use structured formatting?"""
    indicators = ["1.", "2.", "•", "-", "\n", "first", "second"]
    hits = sum(1 for i in indicators if i in text.lower())
    return round(min(1.0, hits / 3), 3)


@observe(name="qa-answer-scored", as_type="generation",
         capture_input=False, capture_output=False)
def ask_and_score(question: str) -> str:
    system = "You are a QA Architect. Answer in structured bullet points, 80-120 words."

    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
    )

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
    )
    answer = response.choices[0].message.content
    langfuse.update_current_generation(output=answer,
        usage_details={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens})

    # ── METHOD 3: score_current_span/trace inside @observe ───────

    # Score the generation (observation-level)
    langfuse.score_current_span(
        name="response_length",
        value=compute_length_score(answer, target_words=100),
        data_type="NUMERIC",
        comment=f"{len(answer.split())} words (target: 100)",
    )

    # Score the overall trace
    langfuse.score_current_trace(
        name="structure_score",
        value=compute_structure_score(answer),
        data_type="NUMERIC",
        comment="Measures use of numbered lists, bullets, sections",
    )

    return answer


if __name__ == "__main__":
    questions = [
        "What is regression testing?",
        "Describe the test pyramid.",
        "What makes a good test case?",
    ]

    for q in questions:
        with propagate_attributes(
            trace_name="Numeric-scored QA",
            user_id="user-123",
            tags=["scoring", "numeric", "day2"],
            metadata={"tutorial": "day2-hour2"},
        ):
            answer = ask_and_score(q)
            print(f"Q: {q}")
            print(f"A: {answer[:100]}...\n")

    langfuse.flush()
    print("✓ Check Langfuse → Traces — each trace has 'response_length' and 'structure_score'")
