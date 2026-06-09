from dotenv import load_dotenv
import os, uuid, json
load_dotenv("../.env")

from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")

JUDGE_PROMPT = """You are evaluating a QA Architect chatbot response.

User question: {input}
Assistant response: {output}

Does the response give actionable, practical advice the user can implement immediately?
- TRUE (1): Response contains specific steps, examples, or concrete techniques
- FALSE (0): Response is vague, theoretical only, or doesn't answer what was asked

Return ONLY: {{"score": 1, "reasoning": "one sentence"}}"""


@observe(name="qa-answer", as_type="generation",
         capture_input=False, capture_output=False)
def get_answer(question: str) -> str:
    """Get answer from QA Architect chatbot."""
    system = "You are a QA Architect. Answer with practical, actionable advice."
    
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[{"role": "user", "content": question}],
    )
    
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
    )
    answer = response.choices[0].message.content
    
    langfuse.update_current_generation(output=answer,
        usage_details={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens})
    
    return answer


def judge_response(question: str, answer: str) -> dict:
    """Use LLM as a judge to score the response."""
    judge_input = JUDGE_PROMPT.format(input=question, output=answer)
    
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "user", "content": judge_input},
        ],
        temperature=0,
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        return {"score": float(result.get("score", 0)), "reasoning": result.get("reasoning", "")}
    except:
        return {"score": 0.0, "reasoning": "Failed to parse judge response"}


@observe(name="qa-with-judgment")
def ask_and_judge(question: str) -> str:
    """Ask question, get answer, and judge the response."""
    answer = get_answer(question)
    print(f"\nQA Architect: {answer}\n")
    
    # Judge the response
    judgment = judge_response(question, answer)
    print(f"Judge Score: {judgment['score']} - {judgment['reasoning']}\n")
    
    # Score the current trace/span
    langfuse.score_current_trace(
        name="judge_score",
        value=judgment["score"],
        data_type="BOOLEAN",
        comment=judgment["reasoning"],
    )
    
    return answer


if __name__ == "__main__":
    questions = [
        "What is the smoke testing technique?",
        "How do you decide which tests to automate?",
        "What's the difference between unit and integration tests?",
    ]
    
    session_id = f"judge-{uuid.uuid4().hex[:8]}"
    print(f"\n🤖 QA Architect with Judge Demo")
    print(f"   Session: {session_id}\n")
    
    with propagate_attributes(
        session_id=session_id,
        user_id="user-123",
        tags=["judge-demo", "day2"],
        metadata={"tutorial": "day2-hour3"},
    ):
        for q in questions:
            ask_and_judge(q)
    
    langfuse.flush()
    print(f"✓ Session complete. Check Sessions → {session_id}")