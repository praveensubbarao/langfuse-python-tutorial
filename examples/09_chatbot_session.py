from dotenv import load_dotenv
import os, uuid
load_dotenv()

from langfuse import observe, get_client, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client  = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

SYSTEM_PROMPT = (
    "You are an experienced QA Architect with 20 years of experience. "
    "You help software teams improve their testing strategies. "
    "Be concise and practical."
)


@observe(name="chat-turn", as_type="generation",
         capture_input=False, capture_output=False)
def chat_turn(messages: list, turn_num: int) -> str:
    """
    One LLM turn. Receives the FULL conversation history as messages.
    Returns the assistant reply.
    """
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        model_parameters={"temperature": 0.7},
        input=messages,    # ← full history sent to LLM
        metadata={"turn_num": str(turn_num)},
    )

    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=messages,
        temperature=0.7,
    )
    reply = response.choices[0].message.content

    langfuse.update_current_generation(
        output=reply,
        usage_details={
            "input_tokens":  response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    )
    return reply


class QAChatbot:
    def __init__(self, user_id: str):
        self.user_id    = user_id
        self.session_id = f"chat-{uuid.uuid4().hex[:10]}"
        self.turn       = 0
        # Conversation history — grows with each turn
        self.messages   = [{"role": "system", "content": SYSTEM_PROMPT}]
        print(f"🤖 QA Architect Chatbot")
        print(f"   Session : {self.session_id}")
        print(f"   User    : {self.user_id}")
        print(f"   Type your question and press Enter to submit")
        print(f"   Type 'quit' to exit\n")

    def chat(self, user_input: str) -> str:
        self.turn += 1

        # Append user message to history
        self.messages.append({"role": "user", "content": user_input})

        # Each turn = one trace, all grouped under same session_id
        with propagate_attributes(
            trace_name=f"Turn {self.turn}",
            session_id=self.session_id,
            user_id=self.user_id,
            tags=["chatbot", "qa-architect"],
            metadata={
                "turn":         str(self.turn),
                "history_len":  str(len(self.messages)),
            },
        ):
            reply = chat_turn(self.messages, self.turn)

        # Append assistant reply to history for next turn
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def end_session(self):
        langfuse.flush()
        print(f"\n✓ Session complete. {self.turn} turns traced.")
        print(f"  Find it in Langfuse → Sessions → {self.session_id}")


if __name__ == "__main__":
    bot = QAChatbot(user_id="user-123")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        reply = bot.chat(user_input)
        print(f"\nQA Architect: {reply}\n")

    bot.end_session()
