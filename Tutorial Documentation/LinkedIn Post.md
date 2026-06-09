🧪 QA Engineers: You already know how to test code. Here's how to test your AI.

Most QA teams adding LLMs to their products hit the same wall fast:
"The AI answered correctly in testing... why is it giving garbage in production?"

I spent the last few days building with Langfuse — an open-source observability platform for LLM apps. Here's what it actually gives you, in QA terms you already understand.

🔍 1. Logging — but for AI answers

Every LLM call becomes a visible, searchable trace. You see the exact prompt sent, the exact answer returned, how long it took, and how many tokens it used. No more guessing what the model was given.


@observe(as_type="generation")
def call_llm(question: str) -> str:
    # your OpenAI/Ollama call here
    # Langfuse captures input, output, latency automatically
📊 2. Scoring — like test assertions, but for AI quality

You can attach numeric, boolean, or categorical scores to any response — automatically or from human review.


langfuse.score_current_trace(name="quality", value="excellent", data_type="CATEGORICAL")
langfuse.score_current_span(name="keyword_coverage", value=0.87, data_type="NUMERIC")
Your QA dashboard now shows which answers were good, which weren't, and why.

🧪 3. Dataset experiments — A/B testing for prompts

Built a test dataset of QA questions + expected criteria? Run two prompt versions against it and compare scores side by side.


result = dataset.run_experiment(
    name="prompt-v2-structured",
    task=lambda *, item, **_: {"answer": call_llm(item.input["question"])},
    evaluators=[coverage_evaluator],
)
This is regression testing for prompts. Run it before every release.

🏆 4. Golden test set — grows from production

When a user thumbs-up an AI response, promote that trace directly into your test dataset.


# user gave 👍 → this answer becomes a reference example
langfuse.create_dataset_item(
    dataset_name="qa-eval-golden",
    input={"question": trace.input},
    expected_output=trace.output,
)
Your test suite improves automatically as your users interact with the product.

💰 5. Cost tracking — "How much did QA cost to run?"

Every token is tracked. Every test run shows input/output tokens and estimated dollar cost. You can filter by tag, session, or user to see exactly where money is going.

🔄 The QA mental model for LLM observability:

Traditional QA	Langfuse equivalent
Test logs	Traces
Test assertions	Scores
Regression suite	Dataset experiments
Manual test cases	Golden set (production-promoted)
CI cost report	Token + cost dashboard
It's open-source, works with any LLM (OpenAI, Anthropic, local Ollama), and the Python SDK hooks in with a single decorator.

If your team is shipping AI features and relying on "it felt right in testing" — this closes that gap.

What's your current approach to validating AI quality in production? Drop it in the comments 👇

#QualityEngineering #AITesting #LLMOps #Langfuse #TestAutomation #QA #ArtificialIntelligence