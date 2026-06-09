from dotenv import load_dotenv
import os, uuid
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


@observe(name="qa-answer-with-feedback", as_type="generation",
         capture_input=False, capture_output=False)
def get_answer_and_score(question: str) -> str:
    """Get answer from LLM and score based on user feedback."""
    system = "You are a QA Architect. Be concise."
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[{"role": "user", "content": question}],
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
    
    print(f"\nQA Architect: {answer}\n")
    
    # Ask for feedback and score immediately (inside @observe context)
    rating = input("Was this helpful? (y/n/skip): ").strip().lower()
    print(f"  [DEBUG] rating={rating}")
    if rating in ("y", "n"):
        comment = input("Optional comment (or Enter to skip): ").strip()
        # Score the current SPAN (this span wraps the generation)
        langfuse.score_current_span(
            name="user_feedback",
            value=1.0 if rating == "y" else 0.0,
            data_type="BOOLEAN",
            comment=comment if comment else None,
        )
        emoji = "👍" if rating == "y" else "👎"
        print(f"  {emoji} Feedback recorded")
    print()
    
    return answer


def interactive_feedback_session():
    """
    Simulate a real chatbot UI:
    1. User asks a question
    2. Bot answers
    3. User gives thumbs up/down
    4. Score is recorded against the generation
    """
    session_id = f"feedback-{uuid.uuid4().hex[:8]}"
    print(f"\n🤖 QA Architect — Feedback Demo")
    print(f"   Session: {session_id}")
    print(f"   After each answer, rate with 👍 (y) or 👎 (n)")
    print(f"   Type 'quit' to exit\n")

    with propagate_attributes(
        session_id=session_id,
        user_id="user-123",
        tags=["feedback-demo", "day2"],
        metadata={"tutorial": "day2-hour2"},
    ):
        while True:
            question = input("You: ").strip()
            if question.lower() in ("quit", "q"):
                break
            if not question:
                continue

            get_answer_and_score(question)

    langfuse.flush()
    print(f"\n✓ Session complete. Check Sessions → {session_id}")
    print(f"  [DEBUG] Langfuse flushed")


if __name__ == "__main__":
    interactive_feedback_session()
