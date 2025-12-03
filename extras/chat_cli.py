# extras/chat_cli.py
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

async def chat_cli():
    router = RouterAgent()

    print("\n===================================")
    print("   MULTI-AGENT CUSTOMER SUPPORT")
    print("===================================")
    print("Type your question below.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("\nGoodbye! 👋")
            break

        if not user_input:
            continue

        print("\n[Router] Processing your request...\n")

        result = await router.process_query(user_input, customer_id=1)
        response = result.get("response", "No response generated")

        print("\n--- FINAL ANSWER ---")
        print(response)
        print("\n-----------------------------------\n")


if __name__ == "__main__":
    asyncio.run(chat_cli())