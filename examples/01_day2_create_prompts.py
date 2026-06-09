from dotenv import load_dotenv
load_dotenv("../.env")   # .env is one level up in langfuse-tutorial/

from langfuse import get_client

langfuse = get_client()

# ─────────────────────────────────────────────────────────────────
# PROMPT 1: Text prompt (single string, good for system messages)
# Variables use {{double_curly_brace}} syntax
# ─────────────────────────────────────────────────────────────────
text_prompt = langfuse.create_prompt(
    name="qa-architect-system",
    type="text",
    prompt=(
        "You are an experienced QA Architect with {{experience_years}} years of "
        "software industry experience. You specialise in {{specialisation}}. "
        "Your communication style is {{style}}. "
        "Always provide practical, actionable advice with concrete examples."
    ),
    config={                          # model parameters stored alongside prompt
        "model":       "llama3.2",
        "temperature": 0.5,
        "max_tokens":  500,
    },
    labels=["production"],           # immediately mark as production
)
print(f"✓ Text prompt created:  {text_prompt.name} v{text_prompt.version}")


# ─────────────────────────────────────────────────────────────────
# PROMPT 2: Chat prompt (array of messages — great for few-shot)
# ─────────────────────────────────────────────────────────────────
chat_prompt = langfuse.create_prompt(
    name="qa-test-case-chat",
    type="chat",
    prompt=[
        {
            "role": "system",
            "content": (
                "You are a QA Architect specialising in test case design. "
                "Generate test cases for the {{feature_type}} feature described. "
                "Use {{test_format}} format. Cover: happy path, edge cases, and error scenarios."
            ),
        },
        {
            "role": "user",
            "content": "Feature: {{feature_description}}",
        },
    ],
    config={
        "model":       "llama3.2",
        "temperature": 0.3,   # lower temp = more consistent test cases
    },
    labels=["production"],
)
print(f"✓ Chat prompt created:  {chat_prompt.name} v{chat_prompt.version}")
print("\nCheck Langfuse UI → Prompt Management to see both prompts.")
