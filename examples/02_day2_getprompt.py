from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

# ─────────────────────────────────────────────────────────────────
# PATTERN 1: Text prompt — get, compile, use
# ─────────────────────────────────────────────────────────────────

# get_prompt() fetches from Langfuse (cached 60s)
# No label = uses 'production' label automatically
system_prompt_obj = langfuse.get_prompt("qa-architect-system")

print(f"Loaded: {system_prompt_obj.name} v{system_prompt_obj.version}")
print(f"Labels: {system_prompt_obj.labels}\n")

# compile() fills {{variables}} with actual values → returns a string
compiled_system = system_prompt_obj.compile(
    experience_years="5",
    specialisation="test stragegy and automation",
    style="concise and practical and oneliner simple language",
)
print("Compiled system prompt:")
print(compiled_system)
print()


# ─────────────────────────────────────────────────────────────────
# PATTERN 2: Chat prompt — get, compile, use as messages list
# ─────────────────────────────────────────────────────────────────
chat_prompt_obj = langfuse.get_prompt("qa-test-case-chat")

# For chat prompts, compile() returns a list of {role, content} dicts
compiled_messages = chat_prompt_obj.compile(
    feature_type="login",
    test_format="Gherkin (Given/When/Then)",
    feature_description="User login with email and password. Max 3 attempts before lockout.",
)
print("Compiled chat messages:")
for msg in compiled_messages:
    print(f"  [{msg['role']}]: {msg['content'][:80]}...")
print()


# ─────────────────────────────────────────────────────────────────
# PATTERN 3: Get specific version or label
# ─────────────────────────────────────────────────────────────────
# Get a specific version number
v1_prompt = langfuse.get_prompt("qa-architect-system", version=1)
print(f"Specific version: v{v1_prompt.version}")

# Get a specific label (e.g. staging)
# latest_prompt = langfuse.get_prompt("qa-architect-system", label="latest")

# Read model config stored with the prompt
print(f"Config from prompt: {system_prompt_obj.config}")
model      = system_prompt_obj.config.get("model", os.getenv("OLLAMA_MODEL"))
temperature = system_prompt_obj.config.get("temperature", 0.5)

print(f"\nUsing model={model}, temperature={temperature}\n")

# ─────────────────────────────────────────────────────────────────
# PATTERN 4: Use the compiled prompt in an actual LLM call
# ─────────────────────────────────────────────────────────────────
print("Sending to LLM...")
response = client.chat.completions.create(
    model=os.getenv("OLLAMA_MODEL"),
    messages=[
        {"role": "system", "content": compiled_system},
        {"role": "user",   "content": "What are the top 3 test types for an API?"},
    ],
    temperature=temperature,
)
print("\nResponse:")
print(response.choices[0].message.content)
