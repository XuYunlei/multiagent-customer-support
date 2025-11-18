import json
import asyncio
from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


class CustomerDataAgent:
    """
    Customer Data Agent

    - Automatically launches the MCP server as a subprocess
    - Wraps MCP tool calls into simple Python async functions
    - Used by Router Agent & Support Agent
    """

    def __init__(self):
        # Automatically launch the MCP server in the background
        self.transport = StdioTransport(
            command="python",
            args=["mcp_server/server.py"],
        )
        self.client = Client(self.transport)

    async def start(self):
        """Start the MCP client session."""
        await self.client.__aenter__()

    async def stop(self):
        """Stop the MCP client session."""
        await self.client.__aexit__(None, None, None)

    # ------------------------------------------------------------------
    # Helper function to extract JSON response from MCP tool call
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_json(result) -> Any:
        if not result.content:
            return None
        # result.content is a list of TextContent blocks
        text = result.content[0].text
        return json.loads(text)

    # ------------------------------------------------------------------
    # MCP Tool Wrappers
    # ------------------------------------------------------------------

    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "get_customer", {"customer_id": customer_id}
        )
        return self._extract_json(result)

    async def list_customers(
        self, status: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        if status:
            params["status"] = status
        result = await self.client.call_tool("list_customers", params)
        return self._extract_json(result)

    async def update_customer(
        self, customer_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "update_customer",
            {
                "customer_id": customer_id,
                "data_json": json.dumps(data),
            },
        )
        return self._extract_json(result)

    async def create_ticket(
        self, customer_id: int, issue: str, priority: str = "medium"
    ) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "create_ticket",
            {
                "customer_id": customer_id,
                "issue": issue,
                "priority": priority,
            },
        )
        return self._extract_json(result)

    async def get_customer_history(
        self, customer_id: int
    ) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "get_customer_history", {"customer_id": customer_id}
        )
        return self._extract_json(result)


# ------------------------------------------------------------------
# Standalone Test Runner
# ------------------------------------------------------------------

async def _test_agent():
    agent = CustomerDataAgent()
    await agent.start()

    print("\n=== Test: list_customers() ===")
    print(await agent.list_customers(limit=3))

    print("\n=== Test: get_customer(1) ===")
    print(await agent.get_customer(1))

    print("\n=== Test: get_customer_history(1) ===")
    print(await agent.get_customer_history(1))

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(_test_agent())
