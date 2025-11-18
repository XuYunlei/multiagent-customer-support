import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from agents.router_agent import RouterAgent

async def run_demo():
    router = RouterAgent()

    test_queries = [
        "Hi, what's the status of my account?",
        "I was charged twice this month, please help!",
        "I want to upgrade my account and also fix my login issue.",
        "Show me all my tickets.",
        "Please update my email to new_email@gmail.com",
    ]

    print("\n============================")
    print(" MULTI-AGENT DEMO STARTED")
    print("============================\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n====== TEST SCENARIO {i} ======")
        print(f"User Query: {query}\n")

        final_answer = await router.execute(query, customer_id=1)

        print("\n--- FINAL ANSWER ---")
        print(final_answer)

        print("\n------------------------------")
        print(" End of Scenario")
        print("------------------------------\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
