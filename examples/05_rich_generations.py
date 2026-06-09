from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import get_client, propagate_attributes
from langfuse.openai import OpenAI   # ← drop-in wrapper stays

langfuse = get_client()
client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

SYSTEM_PROMPT = (
    "You are an experienced QA Architect. "
    "Answer in structured bullet points."
)

with propagate_attributes(
    trace_name="rich-generation-demo",
    user_id="user-123",
    tags=["qa", "rich-demo"],
    metadata={"tutorial": "day1-hour2-step5"},
):
    with langfuse.start_as_current_observation(
        as_type="span",
        name="qa-request",
        input={"question": "List 5 types of software testing."},
    ) as root:

        # No manual generation span — wrapper handles it
        response = client.chat.completions.create(
            name="list-testing-types",       # ← names the auto-generated span
            model=os.getenv("OLLAMA_MODEL"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": "List 5 types of software testing."},
            ],
            temperature=0.2,
            max_tokens=400,
            metadata={"prompt_version": "1.0", "use_case": "qa-education"},
        )
        answer = response.choices[0].message.content
        root.update(output={"answer": answer})

print(answer)
langfuse.flush()