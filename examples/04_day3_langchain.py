from dotenv import load_dotenv
import os
load_dotenv("../.env")

# ── Langfuse LangChain callback ───────────────────────────────────
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

langfuse = get_client()
langfuse_handler = CallbackHandler()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Point LangChain at your local Ollama server
llm = ChatOpenAI(
    base_url=f"{os.getenv('OLLAMA_BASE_URL')}",
    api_key="ollama",
    model=os.getenv("OLLAMA_MODEL"),
    temperature=0.4,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a QA Architect. Be concise and practical."),
    ("human",  "{question}"),
])

chain = prompt | llm | StrOutputParser()

# ✅ Pass the Langfuse callback handler — that's it.
# All LangChain operations are automatically traced.
# propagate_attributes sets user_id/session_id/tags on the trace (v4 API)
with propagate_attributes(user_id="user-123", session_id="langchain-demo", tags=["langchain", "day3"]):
    result = chain.invoke(
        {"question": "What is the difference between QA and QC?"},
        config={"callbacks": [langfuse_handler]},
    )

print(result)
langfuse.flush()
print("✓ Trace in Langfuse. LangChain chain → spans auto-created.")
