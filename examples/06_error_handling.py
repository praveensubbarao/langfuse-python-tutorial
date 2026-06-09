from dotenv import load_dotenv
import os
load_dotenv()

from langfuse import get_client, propagate_attributes
from langfuse.openai import OpenAI

langfuse = get_client()
client  = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")


def risky_retrieval(query: str) -> list[str]:
    # Simulate a retrieval that might fail
    if "crash" in query.lower():
        raise ValueError(f"Retrieval service unavailable for query: {query}")
    return ["Relevant test case documentation..."]


def run_with_error_handling(question: str):
    with propagate_attributes(
        trace_name="error-demo",
        user_id="user-123",
        tags=["error-handling"],
        metadata={"tutorial": "day1-hour2-step6"},
    ):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="pipeline-with-error",
            input={"question": question},
        ) as root:

            try:
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="retrieval-step",
                    input={"query": question},
                ) as retrieval_span:

                    try:
                        docs = risky_retrieval(question)
                        retrieval_span.update(
                            output={"docs": docs},
                            level="DEFAULT",   # DEFAULT | DEBUG | WARNING | ERROR
                        )
                    except ValueError as e:
                        # Mark the retrieval span as ERROR — visible in dashboard
                        retrieval_span.update(
                            level="ERROR",
                            status_message=str(e),
                            output={"error": str(e)},
                        )
                        # Graceful degradation: continue without context
                        docs = []

                # Continue to LLM even if retrieval failed
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="llm-fallback",
                    model=os.getenv("OLLAMA_MODEL"),
                    input={"context_available": bool(docs), "question": question},
                ) as gen:

                    fallback_msg = (
                        "Answer from knowledge only (retrieval failed): "
                        if not docs else ""
                    )
                    response = client.chat.completions.create(
                        model=os.getenv("OLLAMA_MODEL"),
                        messages=[{
                            "role": "user",
                            "content": f"{fallback_msg}{question}",
                        }],
                    )
                    answer = response.choices[0].message.content
                    gen.update(output=answer)

                root.update(output={"answer": answer, "retrieval_failed": not bool(docs)})
                return answer

            except Exception as e:
                # Catastrophic failure — mark the root span as error
                root.update(level="ERROR", status_message=str(e))
                raise


if __name__ == "__main__":
    # Test 1: normal query
    result = run_with_error_handling("What is smoke testing?")
    print("Normal query:", result[:100])

    # Test 2: query that triggers retrieval failure
    result = run_with_error_handling("crash: What is regression testing?")
    print("Degraded query:", result[:100])

    langfuse.flush()
