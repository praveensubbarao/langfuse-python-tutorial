"""
Basic Langfuse tracing example using the @observe decorator (SDK v4+).

Run:
    .venv/bin/python examples/basic_tracing.py

What you'll see in the Langfuse dashboard:
    - One trace named "answer-question"
    - A nested span named "build-prompt"
    - A nested generation named "openai-chat" with token usage and cost
"""

from dotenv import load_dotenv
load_dotenv()  # must come before any Langfuse import

import openai
from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()  # single module-level instance; reused across all calls


@observe(as_type="span", name="build-prompt")
def build_prompt(question: str) -> list[dict]:
    """Construct the messages list sent to the model."""
    return [
        {"role": "system", "content": "You are a concise assistant. Answer in one sentence."},
        {"role": "user", "content": question},
    ]


@observe(as_type="generation", name="openai-chat")
def call_openai(messages: list[dict]) -> str:
    """Call OpenAI and attach model + token metadata to the generation span."""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    answer = response.choices[0].message.content

    # In v4, update the current generation via the client — langfuse_context is gone
    langfuse.update_current_generation(
        model=response.model,
        usage_details={
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
        output=answer,
    )
    return answer


@observe(name="answer-question")
def answer_question(user_id: str, question: str) -> str:
    """
    Root trace. propagate_attributes sets user_id on every span in this context,
    enabling per-user cost and performance queries in Langfuse.
    The outermost @observe creates the Langfuse trace automatically.
    """
    with propagate_attributes(
        user_id=user_id,
        tags=["basic-example"],
        metadata={"question_length": len(question)},
    ):
        messages = build_prompt(question)
        return call_openai(messages)


if __name__ == "__main__":
    result = answer_question(
        user_id="demo-user",
        question="What is Langfuse used for?",
    )
    print("Answer:", result)

    # Flush is required in scripts — events are sent asynchronously and will
    # be dropped if the process exits before the background thread completes.
    langfuse.flush()
