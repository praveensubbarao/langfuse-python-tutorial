from dotenv import load_dotenv
import os, time
load_dotenv("../.env")

from langfuse import get_client
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

QUESTION = "What is exploratory testing and when should I use it?"


def run_with_current_production_prompt(label: str = "production") -> dict:
    """Fetch production prompt, compile, call LLM. Returns version used + answer."""
    prompt_obj = langfuse.get_prompt("qa-architect-system", label=label,
                                       cache_ttl_seconds=300)  # bypass cache for demo
    system = prompt_obj.compile(
        experience_years="20",
        specialisation="exploratory and session-based testing",
        style="practical",
    )
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": QUESTION},
        ],
    )
    return {
        "version": prompt_obj.version,
        "answer":  response.choices[0].message.content[:200],
    }


# ── PHASE 1: Run with current production (v1) ────────────────────
print("=== PHASE 1: Running with current production prompt ===")
result_v1 = run_with_current_production_prompt()
print(f"Prompt version used : v{result_v1['version']}")
print(f"Answer snippet      : {result_v1['answer']}...\n")


# ── PHASE 2: Create v2 with improved prompt ──────────────────────
print("=== PHASE 2: Creating improved v2 prompt ===")
v2 = langfuse.create_prompt(
    name="qa-architect-system",   # same name = new version of existing prompt
    type="text",
    prompt=(
        "You are a senior QA Architect with {{experience_years}} years of "
        "deep expertise in {{specialisation}}. "
        "IMPROVED v2: Always structure your answer with: "
        "1) Definition 2) When to use 3) Concrete example 4) Common mistakes. "
        "Communication style: {{style}}."
    ),
    config={"model": "llama3.2", "temperature": 0.4},
    labels=["staging"],   # push to staging first, NOT production yet
)
print(f"Created: {v2.name} v{v2.version} (labels: {v2.labels})\n")


# ── PHASE 3: Promote v2 to production ────────────────────────────
print("=== PHASE 3: Promoting v2 to production ===")
# In a real workflow you'd test v2 in staging first.
# Here we promote immediately for the demo.
langfuse.create_prompt(
    name="qa-architect-system",
    type="text",
    prompt=v2.prompt,
    config=v2.config,
    labels=["production"],   # now this version is production
)
print("Production label moved to v2.\n")


# ── PHASE 4: Same code, new prompt, no redeploy ──────────────────
print("=== PHASE 4: Same code — picks up new production prompt ===")
result_v2 = run_with_current_production_prompt()
print(f"Prompt version used : v{result_v2['version']}")
print(f"Answer snippet      : {result_v2['answer']}...")

print("\n✓ Same function, different prompt version — zero code change!")
langfuse.flush()
