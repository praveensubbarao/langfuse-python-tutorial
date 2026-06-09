from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client

langfuse = get_client()

# ── 1. Create the dataset ─────────────────────────────────────────
dataset = langfuse.create_dataset(
    name="qa-architect-eval-v1",
    description="Golden QA Architect questions with expected answer criteria",
    metadata={"created_by": "tutorial-day3", "version": "1"},
)
print(f"✓ Dataset created: {dataset.name}")

# ── 2. Add items (input + expected output criteria) ───────────────
items = [
    {
        "input":    {"question": "What is boundary value analysis?"},
        "expected": "Should include: definition, boundary examples (min-1, min, min+1), practical use case",
        "metadata": {"topic": "test-design", "difficulty": "beginner"},
    },
    {
        "input":    {"question": "How do you build a regression test suite?"},
        "expected": "Should include: test selection criteria, automation strategy, maintenance approach",
        "metadata": {"topic": "test-strategy", "difficulty": "intermediate"},
    },
    {
        "input":    {"question": "What is exploratory testing and when is it most valuable?"},
        "expected": "Should include: definition, comparison to scripted testing, when to use, session-based approach",
        "metadata": {"topic": "test-types", "difficulty": "intermediate"},
    },
    {
        "input":    {"question": "How do you measure test coverage effectively?"},
        "expected": "Should include: coverage metrics, tools, what coverage doesn't tell you, risk-based approach",
        "metadata": {"topic": "metrics", "difficulty": "advanced"},
    },
    {
        "input":    {"question": "Explain the test pyramid and why it matters for CI/CD."},
        "expected": "Should include: unit/integration/E2E layers, ratios, speed vs confidence tradeoff, CI/CD implications",
        "metadata": {"topic": "architecture", "difficulty": "advanced"},
    },
]

for item in items:
    langfuse.create_dataset_item(
        dataset_name=dataset.name,
        input=item["input"],
        expected_output=item["expected"],
        metadata=item["metadata"],
    )
    print(f"  + Added: {item['input']['question'][:50]}...")

langfuse.flush()
print(f"\n✓ {len(items)} items added → Langfuse UI → Datasets → {dataset.name}")
