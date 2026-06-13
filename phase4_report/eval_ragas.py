import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2_agent.agent import app as agent_app

# 5 test queries with expected answers for manual grading
test_queries = [
    {
        "query": "What was Apple's total iPhone revenue in 2023?",
        "tool_expected": "SQL"
    },
    {
        "query": "What did NVIDIA say about AI demand in their 2023 report?",
        "tool_expected": "Vector"
    },
    {
        "query": "What was Microsoft's cloud revenue in Q3 2023 and what did they say about Azure growth?",
        "tool_expected": "SQL + Vector"
    },
    {
        "query": "What were the main risks mentioned by Meta in their 2023 annual report?",
        "tool_expected": "Vector"
    },
    {
        "query": "Compare Amazon AWS revenue between Q1 and Q3 2023",
        "tool_expected": "SQL"
    },
]

results = []

print("=" * 70)
print("RAGAS EVALUATION — Enterprise AI Data Analyst")
print("=" * 70)

for i, test in enumerate(test_queries):
    print(f"\n[{i+1}/5] QUERY: {test['query']}")
    print(f"Expected tool: {test['tool_expected']}")
    print("-" * 50)

    try:
        final_state = agent_app.invoke({"messages": [("user", test["query"])]})

        last_msg = final_state['messages'][-1]
        if isinstance(last_msg.content, list):
            answer = " ".join(
                block['text'] for block in last_msg.content
                if isinstance(block, dict) and block.get('type') == 'text'
            )
        else:
            answer = last_msg.content

        print(f"\nANSWER: {answer[:400]}")

        # Manual grading
        faithfulness = float(input("\nFaithfulness score (0.0 to 1.0): "))
        relevance = float(input("Answer Relevance score (0.0 to 1.0): "))

        results.append({
            "query": test["query"],
            "answer": answer[:400],
            "tool": test["tool_expected"],
            "faithfulness": faithfulness,
            "relevance": relevance
        })

    except Exception as e:
        print(f"ERROR: {e}")
        results.append({
            "query": test["query"],
            "answer": f"ERROR: {e}",
            "tool": test["tool_expected"],
            "faithfulness": 0.0,
            "relevance": 0.0
        })

# Summary
print("\n" + "=" * 70)
print("EVALUATION SUMMARY")
print("=" * 70)
print(f"{'#':<4} {'Tool':<15} {'Faithfulness':<15} {'Relevance':<15}")
print("-" * 50)

avg_faith = 0
avg_rel = 0

for i, r in enumerate(results):
    print(f"{i+1:<4} {r['tool']:<15} {r['faithfulness']:<15} {r['relevance']:<15}")
    avg_faith += r['faithfulness']
    avg_rel += r['relevance']

avg_faith /= len(results)
avg_rel /= len(results)

print("-" * 50)
print(f"{'AVG':<4} {'':<15} {avg_faith:<15.2f} {avg_rel:<15.2f}")
print(f"\nAverage Faithfulness : {avg_faith:.2f}")
print(f"Average Answer Relevance : {avg_rel:.2f}")

# Save results
os.makedirs("phase4_report", exist_ok=True)
with open("phase4_report/eval_results.md", "w") as f:
    f.write("# RAGAS Evaluation Results\n\n")
    f.write("| # | Query | Tool | Faithfulness | Relevance |\n")
    f.write("|---|-------|------|:---:|:---:|\n")
    for i, r in enumerate(results):
        f.write(f"| {i+1} | {r['query']} | {r['tool']} | {r['faithfulness']} | {r['relevance']} |\n")
    f.write(f"\n**Average Faithfulness: {avg_faith:.2f}**\n")
    f.write(f"**Average Answer Relevance: {avg_rel:.2f}**\n")

print("\nResults saved to phase4_report/eval_results.md")