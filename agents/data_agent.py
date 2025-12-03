# agents/data_agent.py
"""
Data Agent - Interfaces with MCP server for database operations
"""
import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path to import mcp modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.mcp_client import MCPHTTPClient


class DataAgent:
    """
    Data Agent - Handles all database operations via MCP
    
    Responsibilities:
    - Get customer information
    - List customers
    - Update customer data
    - Create tickets
    - Get customer history
    
    This agent doesn't use LLM - it's a pure data access layer
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001"):
        """
        Initialize Data Agent with MCP client
        
        Args:
            mcp_server_url: URL of the MCP server
        """
        self.mcp_client = MCPHTTPClient(mcp_server_url)
        self.agent_name = "Data Agent"
        
        # Initialize MCP connection
        try:
            self.mcp_client.initialize()
            print(f"[{self.agent_name}] Connected to MCP server at {mcp_server_url}")
        except Exception as e:
            print(f"[{self.agent_name}] Warning: MCP initialization failed: {e}")
    
    async def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer information by ID
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data or None if not found
        """
        print(f"[{self.agent_name}] Fetching customer {customer_id}")
        try:
            customer = self.mcp_client.get_customer(customer_id)
            if customer:
                print(f"[{self.agent_name}] Found customer: {customer.get('name')}")
            else:
                print(f"[{self.agent_name}] Customer {customer_id} not found")
            return customer
        except Exception as e:
            print(f"[{self.agent_name}] Error getting customer: {e}")
            return None
    
    async def list_customers(
        self,
        status: str = "active",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List customers by status
        
        Args:
            status: Customer status ('active' or 'disabled')
            limit: Maximum number of customers
            
        Returns:
            List of customer records
        """
        print(f"[{self.agent_name}] Listing {status} customers (limit={limit})")
        try:
            customers = self.mcp_client.list_customers(status, limit)
            print(f"[{self.agent_name}] Found {len(customers)} customers")
            return customers
        except Exception as e:
            print(f"[{self.agent_name}] Error listing customers: {e}")
            return []
    
    async def update_customer(
        self,
        customer_id: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        Update customer information
        
        Args:
            customer_id: Customer ID to update
            data: Fields to update (email, phone, name, status)
            
        Returns:
            True if successful, False otherwise
        """
        print(f"[{self.agent_name}] Updating customer {customer_id}: {data}")
        try:
            success = self.mcp_client.update_customer(customer_id, data)
            if success:
                print(f"[{self.agent_name}] Customer {customer_id} updated successfully")
            else:
                print(f"[{self.agent_name}] Failed to update customer {customer_id}")
            return success
        except Exception as e:
            print(f"[{self.agent_name}] Error updating customer: {e}")
            return False
    
    async def create_ticket(
        self,
        customer_id: int,
        issue: str,
        priority: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a support ticket
        
        Args:
            customer_id: Customer ID
            issue: Issue description
            priority: Priority level ('low', 'medium', 'high')
            
        Returns:
            Created ticket data or None if failed
        """
        print(f"[{self.agent_name}] Creating {priority} priority ticket for customer {customer_id}")
        try:
            ticket = self.mcp_client.create_ticket(customer_id, issue, priority)
            if ticket:
                print(f"[{self.agent_name}] Ticket {ticket.get('ticket_id')} created")
            else:
                print(f"[{self.agent_name}] Failed to create ticket")
            return ticket
        except Exception as e:
            print(f"[{self.agent_name}] Error creating ticket: {e}")
            return None
    
    async def get_customer_history(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """
        Get customer ticket history
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dictionary with customer_id, tickets list, and count
        """
        print(f"[{self.agent_name}] Getting ticket history for customer {customer_id}")
        try:
            tickets = self.mcp_client.get_customer_history(customer_id)
            result = {
                "customer_id": customer_id,
                "tickets": tickets if tickets else [],
                "count": len(tickets) if tickets else 0
            }
            print(f"[{self.agent_name}] Found {result['count']} tickets")
            return result
        except Exception as e:
            print(f"[{self.agent_name}] Error getting history: {e}")
            return {"customer_id": customer_id, "tickets": [], "count": 0}
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Return A2A Agent Card metadata
        
        Returns:
            Agent Card with capabilities and skills
        """
        return {
            "name": "Data Agent",
            "description": "Database access agent using MCP protocol",
            "version": "1.0.0",
            "capabilities": {
                "mcp_integration": True,
                "database_access": True,
                "customer_management": True,
                "ticket_management": True,
            },
            "skills": [
                {
                    "id": "get_customer",
                    "name": "Get Customer",
                    "description": "Retrieve customer information by ID",
                },
                {
                    "id": "list_customers",
                    "name": "List Customers",
                    "description": "List customers by status",
                },
                {
                    "id": "update_customer",
                    "name": "Update Customer",
                    "description": "Update customer information",
                },
                {
                    "id": "create_ticket",
                    "name": "Create Ticket",
                    "description": "Create a support ticket",
                },
                {
                    "id": "get_history",
                    "name": "Get History",
                    "description": "Get customer ticket history",
                },
            ],
            "transport": "MCP HTTP",
        }


# ======================
# Test the agent
# ======================
async def test_data_agent():
    """Test the Data Agent"""
    agent = DataAgent()
    
    print("\n" + "="*60)
    print("Testing Data Agent with MCP")
    print("="*60)
    
    # Test 1: Get customer
    print("\n  Test 1: Get customer by ID")
    customer = await agent.get_customer(1)
    if customer:
        print(f"   Name: {customer.get('name')}")
        print(f"   Email: {customer.get('email')}")
        print(f"   Status: {customer.get('status')}")
    
    # Test 2: List customers
    print("\n  Test 2: List active customers")
    customers = await agent.list_customers(status="active", limit=3)
    print(f"   Found {len(customers)} active customers")
    
    # Test 3: Get history
    print("\n  Test 3: Get customer history")
    history = await agent.get_customer_history(1)
    print(f"   Customer has {history['count']} tickets")
    
    # Test 4: Create ticket
    print("\n  Test 4: Create support ticket")
    ticket = await agent.create_ticket(
        customer_id=1,
        issue="Test ticket from Data Agent",
        priority="low"
    )
    if ticket:
        print(f"   Created ticket #{ticket.get('ticket_id')}")
    
    print("\n" + "="*60)
    print("✅ Data Agent tests complete!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    # Make sure MCP server is running first!
    print("⚠️  Make sure MCP server is running: python mcp/mcp_server.py")
    asyncio.run(test_data_agent())