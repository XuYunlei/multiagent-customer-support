import sys
from pathlib import Path
import asyncio

# Add project root to Python path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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

        response = await router.execute(user_input, customer_id=1)

        print("\n--- FINAL ANSWER ---")
        print(response)
        print("\n-----------------------------------\n")


if __name__ == "__main__":
    asyncio.run(chat_cli())
