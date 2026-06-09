# Capstone Project: QA Architect Chatbot
# load_dotenv function from the dotenv Python library its purpose is to load environment variables from a .env file into the system's environment variables. This is a common practice for managing configuration settings, such as API keys, database credentials, or other sensitive information
from dotenv import load_dotenv
import os, uuid
load_dotenv()


from langfuse import observe, get_client, propagate_attributes
from langfuse.openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

# ── Knowledge base (replaces vector DB for tutorial) ──────────────
KB = {
    "boundary value":     ["Test at exact edges and just outside them."],
    "equivalence":        ["Divide inputs into classes with identical behaviour."],
    "smoke":              ["Shallow tests to verify the build is stable."],
    "regression":         ["Re-run tests to ensure existing features still work."],
    "exploratory":        ["Unscripted testing guided by tester intuition."],
}

SYSTEM = (
    "You are an experienced QA Architect mentoring a junior tester. Answer their questions with practical testing"
    "experience. Use the provided context when available. Be concise and practical."
)


@observe(name="knowledge-lookup", capture_output=False)
def lookup_knowledge(query: str) -> list[str]:
    query_l = query.lower()
    matched = [docs for key, docs in KB.items() if key in query_l]
    results = matched[0] if matched else []
    langfuse.update_current_span(
        output={"found": bool(results), "chunks": len(results)},
        metadata={"source": "local-kb"},
    )
    return results


@observe(name="llm-response", as_type="generation",
         capture_input=False, capture_output=False)
def generate_response(messages: list, context: list[str], turn: int) -> str:
    # Build enriched messages with context injected
    context_text = "\n".join(f"- {c}" for c in context) if context else "None"
    enriched = messages[:-1] + [{
        "role": "user",
        "content": (
            f"Context:\n{context_text}\n\n"
            if context else ""
        ) + messages[-1]["content"],
    }]

    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        model_parameters={"temperature": 0.5},
        input=enriched,
        metadata={
            "turn":            str(turn),
            "context_used":    str(bool(context)),
            "prompt_version":  "capstone-1.0",
        },
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL"),
            messages=enriched,
            temperature=0.5,
        )
        reply = response.choices[0].message.content
        langfuse.update_current_generation(
            output=reply,
            usage_details={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        )
        return reply

    except Exception as e:
        langfuse.update_current_generation(
            level="ERROR",
            status_message=str(e),
        )
        raise


@observe(name="chat-turn-pipeline")
def process_turn(question: str, history: list, turn: int) -> str:
    context = lookup_knowledge(question)
    reply   = generate_response(history, context, turn)
    return reply


class QAArchitectChatbot:
    """
    Day 1 Capstone: fully instrumented, session-aware QA Architect chatbot.
    Every turn is traced with user_id, session_id, tags, and rich generation data.
    """
    def __init__(self, user_id: str = "user-123"):
        self.user_id    = user_id
        self.session_id = f"qa-{uuid.uuid4().hex[:10]}"
        self.turn       = 0
        self.history    = [{"role": "system", "content": SYSTEM}]

        print(f"\n{'='*50}")
        print(f"  QA Architect Chatbot — Day 1 Capstone")
        print(f"  Session : {self.session_id}")
        print(f"  User    : {self.user_id}")
        print(f"  Quit    : type 'quit'")
        print(f"{'='*50}\n")

    def chat(self, user_input: str) -> str:
        self.turn += 1
        self.history.append({"role": "user", "content": user_input})

        with propagate_attributes(
            trace_name=f"Turn {self.turn}: {user_input[:40]}",
            session_id=self.session_id,
            user_id=self.user_id,
            tags=["qa", "architect", "capstone", "day1"],
            metadata={
                "turn":        str(self.turn),
                "history_len": str(len(self.history)),
                "sdk_version": "4.7.1",
            },
        ):
            reply = process_turn(user_input, self.history, self.turn)

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def end(self):
        langfuse.flush()
        print(f"\n{'='*50}")
        print(f"  Session complete · {self.turn} turns traced")
        print(f"  Dashboard → Sessions → {self.session_id}")
        print(f"{'='*50}")


if __name__ == "__main__":
    bot = QAArchitectChatbot(user_id="user-123")
    while True:
        q = input("You: ").strip()
        if q.lower() in ("quit", "q", "exit"):
            break
        if q:
            reply = bot.chat(q)
            print(f"\nQA Architect: {reply}\n")
    bot.end()
