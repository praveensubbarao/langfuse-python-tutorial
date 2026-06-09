from dotenv import load_dotenv
import os
load_dotenv("../.env")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langfuse import get_client, observe, propagate_attributes
from openai import OpenAI

app      = FastAPI(title="QA Architect API")
langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")


class QuestionRequest(BaseModel):
    question: str
    user_id:  str = "anonymous"
    session_id: str = "default"

class FeedbackRequest(BaseModel):
    trace_id: str
    helpful:  bool
    comment:  str = ""


@observe(name="api-qa-answer", as_type="generation",
         capture_input=False, capture_output=False)
def generate_answer(question: str) -> str:
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"),
        input=[{"role": "user", "content": question}],
    )
    resp = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {"role": "system", "content": "You are a QA Architect. Be concise."},
            {"role": "user",   "content": question},
        ],
    )
    answer = resp.choices[0].message.content
    langfuse.update_current_generation(output=answer,
        usage_details={"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens})
    return answer


@app.post("/ask")
@observe(name="api-request", capture_input=False, capture_output=False)
async def ask_question(req: QuestionRequest):
    with propagate_attributes(
        user_id=req.user_id,
        session_id=req.session_id,
        tags=["api", "fastapi"],
    ):
        answer   = generate_answer(req.question)
        trace_id = langfuse.get_current_trace_id()

    return {"answer": answer, "trace_id": trace_id}


@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    langfuse.create_score(
        name="user_feedback",
        value=1 if req.helpful else 0,
        data_type="BOOLEAN",
        trace_id=req.trace_id,
        comment=req.comment or None,
    )
    langfuse.flush()
    return {"status": "recorded"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
