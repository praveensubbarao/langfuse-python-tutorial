from dotenv import load_dotenv
load_dotenv("../.env")
from langfuse import get_client

langfuse = get_client()

# Fetch traces with high user_feedback scores from the last 7 days
# These are your "golden" examples — users said these were helpful
traces = langfuse.api.trace.list(
    tags=["qa"],
    limit=20,
).data

print(f"Found {len(traces)} traces to review")

promoted = 0
for trace in traces:
    # Check if this trace has a positive user_feedback score
    scores = langfuse.api.scores.get_many(trace_id=trace.id, name="user_feedback").data
    if not scores:
        continue

    if scores[0].value == 1:   # user gave thumbs up
        # Promote this trace's input to the dataset
        langfuse.create_dataset_item(
            dataset_name="qa-architect-eval-v1",
            input={"question": trace.input},
            expected_output=trace.output,     # use actual good output as reference
            metadata={
                "source": "production-trace",
                "trace_id": trace.id,
                "promoted_from": "user-thumbs-up",
            },
        )
        promoted += 1
        print(f"  + Promoted trace {trace.id[:12]}...")

langfuse.flush()
print(f"\n✓ Promoted {promoted} production traces to dataset")
print("  Dataset grows organically as users give positive feedback")
