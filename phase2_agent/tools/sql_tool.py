import sqlite3
from langchain_core.tools import tool

DB_PATH = "./data/financial.db"

@tool
def get_database_schema() -> str:
    """Always call this tool FIRST to learn the table names and columns."""
    print("\n[TOOL] Fetching database schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    rows = cursor.fetchall()
    conn.close()
    schema = "\n".join([row[0] for row in rows if row[0]])
    print(f"[TOOL] Schema fetched:\n{schema}")
    return schema

@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query against the financial database and return the result."""
    print(f"\n[TOOL] Executing SQL: {query}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        print(f"[TOOL] Result: {result}")
        return f"Query result: {result}"
    except Exception as e:
        error_msg = f"SQL Error: {e}"
        print(f"[TOOL] {error_msg}")
        return error_msg