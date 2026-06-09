from dotenv import load_dotenv
import os, uuid, asyncio
load_dotenv()

from langfuse import observe, get_client, propagate_attributes
from openai import AsyncOpenAI   # ← async OpenAI client

langfuse = get_client()
client   = AsyncOpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

SYSTEM = "You are a QA Architect. Be concise."


# ✅ @observe works on async def with zero changes to the decorator
@observe(name="async-retrieval")
async def retrieve_docs(query: str) -> list[str]:
    # Simulate an async DB or vector store call
    await asyncio.sleep(0.05)   # simulated I/O wait
    return [f"Relevant doc for: {query}"]


@observe(name="async-llm-call", as_type="generation",
         capture_input=False, capture_output=False)
async def call_llm(messages: list) -> str:
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=messages,
    )
    response = await client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=messages,
    )
    reply = response.choices[0].message.content
    langfuse.update_current_generation(
        output=reply,
        usage_details={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        },
    )
    return reply


@observe(name="async-qa-pipeline")
async def async_qa_turn(question: str, history: list) -> str:
    # Both awaited functions become children of this span automatically
    docs     = await retrieve_docs(question)
    messages = history + [{"role": "user", "content": question}]
    reply    = await call_llm(messages)
    return reply


async def run_async_session():
    session_id = f"async-{uuid.uuid4().hex[:8]}"
    history    = [{"role": "system", "content": SYSTEM}]

    questions = [
        "What is smoke testing?",
        "What is sanity testing?",
        "What is the key difference between the two?",
    ]

    print(f"Async session: {session_id}\n")

    for i, question in enumerate(questions, 1):
        with propagate_attributes(
            trace_name=f"Async Turn {i}",
            session_id=session_id,
            user_id="user-123",
            tags=["async", "qa-chatbot"],
            metadata={"turn": str(i)},
        ):
            reply = await async_qa_turn(question, history)

        history.append({"role": "user",      "content": question})
        history.append({"role": "assistant", "content": reply})

        print(f"Q{i}: {question}")
        print(f"A{i}: {reply[:120]}...\n")

    langfuse.flush()
    print(f"✓ Async session complete → Sessions → {session_id}")


if __name__ == "__main__":
    asyncio.run(run_async_session())
