from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")


@observe(name="qa-answer", as_type="generation",
         capture_input=False, capture_output=False)
def answer_with_prompt(question: str) -> str:

    # 1. Fetch the production prompt from Langfuse
    prompt_obj = langfuse.get_prompt("qa-architect-system")   # production label

    # 2. Compile with variable values
    system = prompt_obj.compile(
        experience_years="20",
        specialisation="test case design and quality strategy",
        style="concise, structured bullet points",
    )

    # 3. Update generation with model + input + PROMPT LINK
    #    langfuse_prompt links this generation to the exact prompt version
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        model_parameters={
            "temperature": prompt_obj.config.get("temperature", 0.5),
        },
        input=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
        # ✅ KEY: this links the generation to the prompt version
        prompt=prompt_obj,
    )

    # 4. Call the LLM
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
        temperature=prompt_obj.config.get("temperature", 0.5),
    )
    reply = response.choices[0].message.content

    # 5. Log output and token usage
    langfuse.update_current_generation(
        output=reply,
        usage_details={
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    )
    return reply


if __name__ == "__main__":
    questions = [
        "What is the difference between verification and validation?",
        "How do you decide test coverage thresholds for a new feature?",
        "What makes a good bug report?",
    ]

    for q in questions:
        with propagate_attributes(
            trace_name="Prompt-linked QA answer",
            user_id="user-123",
            tags=["prompt-linked", "day2"],
            metadata={"tutorial": "day2-hour1"},
        ):
            answer = answer_with_prompt(q)
            print(f"Q: {q}")
            print(f"A: {answer[:150]}...\n")

    langfuse.flush()
    print("✓ Check traces in Langfuse — each generation shows 'Prompt: qa-architect-system v1'")
