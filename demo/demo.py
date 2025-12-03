# demo/demo.py
import sys
from pathlib import Path
import asyncio

# Add project root to Python path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add agents directory to path so router_agent.py can find data_agent and support_agent
agents_dir = project_root / "agents"
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))
    
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

        result = await router.process_query(query, customer_id=1)

        print("\n--- FINAL ANSWER ---")
        print(result.get("response", "No response generated"))

        if result.get("scenario"):
            print(f"\n--- SCENARIO ---")
            print(result["scenario"])

        print("\n------------------------------")
        print(" End of Scenario")
        print("------------------------------\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
