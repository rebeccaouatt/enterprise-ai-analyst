import os
from typing import Annotated, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from dotenv import load_dotenv

from phase2_agent.tools.sql_tool import get_database_schema, execute_sql
from phase2_agent.tools.vector_tool import search_vector_db

load_dotenv()

# Agent state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Tools
tools = [get_database_schema, execute_sql, search_vector_db]
tool_node = ToolNode(tools)

# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("API_KEY"),
    temperature=0.0
).bind_tools(tools)

# System prompt
system_msg = SystemMessage(content="""
You are an autonomous Enterprise AI Data Analyst.
You have access to two data sources:
1. A SQL database containing quarterly revenue data for major tech companies.
2. A vector database containing extracts from 10-K financial reports.

Rules:
- For numerical questions (revenue, totals, comparisons) -> use get_database_schema first, then execute_sql.
- For qualitative questions (risks, strategy, business context) -> use search_vector_db.
- For complex questions requiring both -> use both tools and combine the results.
- ALWAYS call get_database_schema before executing any SQL query.
- If execute_sql returns an error, read it, fix the query, and try again.
- Once you have all the information, provide a clear and concise answer.
""")

# Nodes
def call_model(state: AgentState):
    messages = state['messages']
    if not isinstance(messages[0], SystemMessage):
        messages = [system_msg] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}

# Routing
def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    queries = [
        "What was Apple's total iPhone revenue in 2023?",
        "What did NVIDIA say about AI demand in their 2023 report?",
        "What was Microsoft's cloud revenue in Q3 2023 and what did they say about Azure growth?"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print('='*60)

        final_state = app.invoke({"messages": [("user", query)]})

        last_msg = final_state['messages'][-1]
        if isinstance(last_msg.content, list):
            for block in last_msg.content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    print(f"\nANSWER: {block['text']}")
        else:
            print(f"\nANSWER: {last_msg.content}")