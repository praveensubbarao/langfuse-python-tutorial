from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

@observe(name="cost-tracked-gen", as_type="generation",
         capture_input=False, capture_output=False)
def tracked_llm_call(question: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[{"role": "user", "content": question}],
    )
    answer = response.choices[0].message.content
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[{"role": "user", "content": question}],
        output=answer,
        usage_details={
            "input_tokens":  response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens":  response.usage.total_tokens,
        },
        # Simulated costs (Ollama is free; using GPT-4o-mini rates for demo)
        cost_details={
            "input_cost":  response.usage.prompt_tokens  * 0.00000015,
            "output_cost": response.usage.completion_tokens * 0.0000006,
            "total_cost":  (response.usage.prompt_tokens * 0.00000015)
                           + (response.usage.completion_tokens * 0.0000006),
        },
        metadata={
            "model_family": "ollama-local",
            "input_chars":  str(len(question)),
        },
    )
    return answer


if __name__ == "__main__":
    questions = [
        "What is smoke testing?",
        "Explain boundary value analysis with examples.",
        "How do you build a test automation framework from scratch? Give a detailed answer.",
    ]
    for q in questions:
        with propagate_attributes(
            trace_name="Cost-tracked QA",
            tags=["cost-demo", "day3"],
        ):
            answer = tracked_llm_call(q)
            print(f"Q: {q[:50]} → {len(answer.split())} words")

    langfuse.flush()
    print("\n✓ Check Langfuse → Dashboard → Token Usage chart")
    print("  Filter by tag 'cost-demo' to see just these traces")
