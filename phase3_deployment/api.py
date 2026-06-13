import os
import sys
import time
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from phase2_agent.agent import app as agent_app

api = FastAPI(
    title="Enterprise AI Data Analyst",
    description="Multi-modal agent combining SQL and Vector DB search",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    token_cost_usd: float
    execution_time_seconds: float

# Token cost constants (Gemini Flash pricing)
INPUT_COST_PER_1M  = 0.075
OUTPUT_COST_PER_1M = 0.30

@api.get("/health")
def health_check():
    return {"status": "ok"}

@api.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    start_time = time.time()

    # Run the agent
    final_state = agent_app.invoke(
        {"messages": [("user", request.question)]}
    )

    # Extract answer
    last_msg = final_state['messages'][-1]
    if isinstance(last_msg.content, list):
        answer = " ".join(
            block['text'] for block in last_msg.content
            if isinstance(block, dict) and block.get('type') == 'text'
        )
    else:
        answer = last_msg.content

    # Estimate token cost from message history
    total_input_tokens = 0
    total_output_tokens = 0
    for msg in final_state['messages']:
        if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
            total_input_tokens += getattr(msg.usage_metadata, 'input_tokens', 0) or 0
            total_output_tokens += getattr(msg.usage_metadata, 'output_tokens', 0) or 0

    token_cost = (total_input_tokens / 1_000_000 * INPUT_COST_PER_1M) + \
                 (total_output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)

    execution_time = time.time() - start_time

    print(f"\n[FINOPS] Input tokens: {total_input_tokens}")
    print(f"[FINOPS] Output tokens: {total_output_tokens}")
    print(f"[FINOPS] Estimated cost: ${token_cost:.6f}")
    print(f"[FINOPS] Execution time: {execution_time:.2f}s")

    return QueryResponse(
        question=request.question,
        answer=answer,
        token_cost_usd=token_cost,
        execution_time_seconds=round(execution_time, 2)
    )