from dotenv import load_dotenv
import os
load_dotenv("../.env")

from langfuse import get_client, Evaluation
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

# ── Two prompt versions to compare ───────────────────────────────
PROMPT_V1 = "You are a QA Architect. Answer the question clearly."

PROMPT_V2 = (
    "You are a senior QA Architect with 20 years of experience. "
    "Structure every answer with: 1) Definition 2) When/Why to use "
    "3) Practical example 4) Common pitfalls. Be concise but complete."
)


def run_llm(system: str, question: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def eval_against_expected(answer: str, expected: str) -> float:
    """Simple keyword coverage: how many expected criteria appear in answer."""
    criteria = [c.strip() for c in expected.split(",")]
    answer_lower = answer.lower()
    hits = sum(1 for c in criteria
               if any(word in answer_lower for word in c.lower().split()))
    return round(hits / max(len(criteria), 1), 3)


def run_experiment(run_name: str, system_prompt: str) -> float:
    print(f"\n{'='*50}")
    print(f"Running experiment: {run_name}")
    print(f"{'='*50}")

    dataset = langfuse.get_dataset("qa-architect-eval-v1")

    def task(*, item, **kwargs):
        question = item.input["question"]
        answer = run_llm(system_prompt, question)
        word_count = len(answer.split())
        print(f"  Q: {question[:50]}...")
        return {"answer": answer, "word_count": word_count}

    def evaluator(*, input, output, expected_output, **kwargs):
        coverage = eval_against_expected(output["answer"], expected_output or "")
        word_count = output["word_count"]
        print(f"  Score: {coverage} | Words: {word_count}")
        return Evaluation(
            name="criteria_coverage",
            value=coverage,
            comment=f"{word_count} words",
        )

    result = dataset.run_experiment(
        name=run_name,
        run_name=run_name,
        task=task,
        evaluators=[evaluator],
    )

    scores = [
        ev.value
        for ir in result.item_results
        for ev in ir.evaluations
        if ev.name == "criteria_coverage"
    ]
    avg = round(sum(scores) / len(scores), 3) if scores else 0.0
    print(f"\n  Average criteria_coverage: {avg}")
    return avg


if __name__ == "__main__":
    avg_v1 = run_experiment("prompt-v1-baseline", PROMPT_V1)
    avg_v2 = run_experiment("prompt-v2-structured", PROMPT_V2)

    langfuse.flush()
    print(f"\n{'='*50}")
    print(f"v1 avg: {avg_v1} | v2 avg: {avg_v2}")
    print(f"Winner: {'v2 (+' + str(round((avg_v2-avg_v1)*100))+'%)' if avg_v2>avg_v1 else 'v1'}")
    print("\n✓ Check Langfuse → Datasets → qa-architect-eval-v1 → Runs tab")
    print("  Compare the two runs side-by-side in the UI")
