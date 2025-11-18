import json
import asyncio
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI


class SupportAgent:
    """
    LLM-powered Support Agent
    - Handles intent classification
    - Produces human-friendly responses
    - Decides if more data is needed
    - Determines ticket priorities
    - Returns structured JSON signals for the Router
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI()  # uses OPENAI_API_KEY env var
        self.model = model

    async def process(
        self,
        query: str,
        customer: Optional[Dict[str, Any]] = None,
        tickets: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Main reasoning function.
        The Router will call this and pass customer & ticket info when available.
        """

        system_prompt = """
You are the Support Agent in a multi-agent customer service system.

Your job:
- Interpret the user's query.
- Decide what action is needed.
- Produce JSON with clear instructions for the Router Agent.
- If more customer data is required, request it.
- If you have enough info, generate a customer-friendly response.
- Decide if a new support ticket is needed.
- Set the ticket priority: low, medium, high, urgent.

ALLOWED ACTIONS:
1. "respond" → You have enough info. Provide a final support response.
2. "request_data" → You need customer data. Set which fields you need.
3. "create_ticket" → Recommend opening a support ticket.

Return ONLY valid JSON, with this structure:

{
  "action": "...",
  "response_text": "...",
  "requires": { ... },
  "ticket": {
      "issue": "...",
      "priority": "low/medium/high/urgent"
  }
}

If fields are not needed, set them to null.
"""

        user_prompt = {
            "query": query,
            "customer": customer,
            "tickets": tickets,
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(user_prompt)},
            ],
        )

        # Extract JSON content from the response and parse it
        content = response.choices[0].message.content
        return json.loads(content) if content else {}


# -------------------------
# Standalone test
# -------------------------

async def _test_agent():
    agent = SupportAgent()

    print("\n=== Test: simple reasoning ===")
    out = await agent.process("Hi, I want to upgrade my account.")
    print(out)

    print("\n=== Test: with customer context ===")
    dummy_cust = {"id": 1, "name": "John", "status": "active"}
    dummy_tickets = [{"id": 1, "issue": "Login issue", "priority": "high"}]
    out = await agent.process("I was charged twice this month!", dummy_cust, dummy_tickets)
    print(out)


if __name__ == "__main__":
    asyncio.run(_test_agent())
