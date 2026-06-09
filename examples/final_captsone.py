from dotenv import load_dotenv
import os, uuid, json, re
load_dotenv("../.env")

from langfuse import observe, get_client, propagate_attributes
from openai import OpenAI

langfuse = get_client()
client   = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")
FALLBACK  = "You are an experienced QA Architect. Provide practical advice."


# ── Scoring helpers ───────────────────────────────────────────────
def _auto_scores(text: str, question: str):
    words    = len(text.split())
    has_struct = any(c in text for c in ["1.","•","- ","\n\n"])
    has_eg     = "example" in text.lower()
    q_words    = {w.lower() for w in re.findall(r'\b\w{4,}\b',question)}
    coverage   = round(sum(1 for w in q_words if w in text.lower())/max(len(q_words),1),3)
    if   words>=60 and has_struct and has_eg: quality="excellent"
    elif words>=30 and (has_struct or has_eg):  quality="good"
    elif words>=10:                               quality="acceptable"
    else:                                          quality="poor"
    return quality, coverage


@observe(name="llm-call", as_type="generation", capture_input=False, capture_output=False)
def call_llm(messages: list, prompt_obj, turn: int, question: str) -> str:
    langfuse.update_current_generation(
        model=os.getenv("OLLAMA_MODEL"), input=messages, prompt=prompt_obj,
        metadata={"turn": str(turn)},
    )
    response = client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL"), messages=messages)
    answer = response.choices[0].message.content
    langfuse.update_current_generation(output=answer,
        usage_details={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens})

    quality, coverage = _auto_scores(answer, question)
    langfuse.score_current_trace(name="auto_quality", value=quality, data_type="CATEGORICAL")
    langfuse.score_current_span(name="keyword_coverage", value=coverage, data_type="NUMERIC")
    return answer


@observe(name="chat-turn")
def process_turn(messages, prompt_obj, turn, question): return call_llm(messages, prompt_obj, turn, question)


class FinalChatbot:
    def __init__(self, user_id="user-123"):
        self.user_id=user_id; self.session_id=f"final-{uuid.uuid4().hex[:8]}"; self.turn=0
        try:
            self.prompt_obj = langfuse.get_prompt("qa-architect-system", cache_ttl_seconds=300, fallback=FALLBACK)
            sys = self.prompt_obj.compile(experience_years="20", specialisation="quality engineering", style="structured with examples")
        except: self.prompt_obj=None; sys=FALLBACK
        self.history=[{"role":"system","content":sys}]
        v=getattr(self.prompt_obj,"version","fallback")
        print(f"\n{'='*55}\n  QA Architect · Final Capstone · Prompt v{v}\n  Session: {self.session_id}\n  y=👍  n=👎  quit=exit\n{'='*55}\n")

    def chat(self, q):
        self.turn+=1; self.history.append({"role":"user","content":q})
        trace_id=None
        with propagate_attributes(trace_name=f"Turn {self.turn}: {q[:35]}",
            session_id=self.session_id, user_id=self.user_id,
            tags=["final-capstone","day3"], metadata={"turn":str(self.turn)}):
            reply=process_turn(self.history,self.prompt_obj,self.turn,q)
            trace_id=langfuse.get_current_trace_id()
        self.history.append({"role":"assistant","content":reply})
        return reply, trace_id

    def feedback(self,trace_id,up,comment=""):
        langfuse.create_score(name="user_feedback",value=1 if up else 0,
            data_type="BOOLEAN",trace_id=trace_id,comment=comment or None)

    def end(self):
        langfuse.flush()
        print(f"\n✓ {self.turn} turns complete · Session: {self.session_id}")


if __name__ == "__main__":
    bot=FinalChatbot()
    while True:
        q=input("You: ").strip()
        if q.lower() in ("quit","q"): break
        if not q: continue
        reply, tid = bot.chat(q)
        print(f"\nQA Architect: {reply}\n")
        r=input("Helpful? (y/n/skip): ").strip().lower()
        if r in ("y","n") and tid:
            c=input("Comment (Enter to skip): ").strip()
            bot.feedback(tid,r=="y",c)
            print(f"  {'👍' if r=='y' else '👎'} recorded\n")
    bot.end()
