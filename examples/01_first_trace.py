from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import observe, propagate_attributes, get_client
from langfuse.openai import OpenAI

langfuse = get_client()

client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL"),
    api_key="ollama",
)

@observe(name="llm-call", as_type="generation")
def call_llm(question: str) -> str:
    system_prompt = (
        "You are an experienced QA Architect with 20 years of software industry experience. "
        "You are skilled in test planning, test case design, and test execution."
    )

    # Update the generation's input metadata
    langfuse.update_current_generation(
        input={"system": system_prompt, "user": question}
    )

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
    )

    answer = response.choices[0].message.content
    langfuse.update_current_generation(output=answer)
    return answer


@observe(name="qa-architect-query")
def query_qa_architect(question: str) -> str:
    return call_llm(question)


# ✅ KEY FIX: propagate_attributes wraps the TOP-LEVEL call,
#    OUTSIDE the @observe functions — this is the correct v4 pattern
if __name__ == "__main__":
    with propagate_attributes(
        trace_name="QA Architect Session",   # note: 'trace_name' not 'name' in v4
        user_id="user_456",
        tags=["qa", "architect", "test-case-design"],
        metadata={
            "tutorial_day": "1",          # ← must be strings in v4
            "hour": "1",
            "sdk_version": "4.7.1",
            "sdk_name": "langfuse-sdk",
        },
    ):
        result = query_qa_architect("What are the best strategies for regression test selection?")

    print(result)
    langfuse.flush()