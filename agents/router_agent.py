# agents/router_agent.py
"""
Router Agent - Orchestrates Data and Support agents
Uses LLM reasoning from Support Agent + Data access from Data Agent
"""
import re
from typing import Dict, Any, Optional
from data_agent import DataAgent
from support_agent import SupportAgent


class RouterAgent:
    """
    Router Agent - The Orchestrator
    
    Responsibilities:
    - Receive customer queries
    - Analyze intent (extract customer ID, detect query type)
    - Coordinate Data Agent and Support Agent
    - Manage multi-step workflows
    - Return final response to user
    
    Workflow:
    1. Analyze query (extract customer ID, understand intent)
    2. Call Support Agent for reasoning
    3. If Support Agent needs data → call Data Agent
    4. If Support Agent wants ticket → call Data Agent to create
    5. Synthesize final response
    """
    
    def __init__(self):
        """Initialize Router with Data and Support agents"""
        self.data_agent = DataAgent()
        self.support_agent = SupportAgent()
        self.agent_name = "Router Agent"
        self.max_steps = 5  # Prevent infinite loops
    
    def _extract_customer_id(self, query: str) -> Optional[int]:
        """
        Extract customer ID from query using regex
        
        Args:
            query: User query string
            
        Returns:
            Customer ID if found, None otherwise
        """
        # Try patterns like "customer 123", "ID 123", "customer ID 123"
        patterns = [
            r'customer\s+(?:id\s+)?(\d+)',
            r'id\s+(\d+)',
            r'customer\s+(\d+)',
            r'\b(\d+)\b',  # Any standalone number
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return int(match.group(1))
        
        return None
    
    async def process_query(self, query: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Main orchestration function
        
        Args:
            query: User's query string
            customer_id: Optional customer ID (if not provided, will try to extract)
            
        Returns:
            Dictionary with:
            - response: Final response text
            - scenario: Which coordination scenario was used
            - coordination_log: List of agent interactions
            - customer_info: Customer data if fetched
            - ticket: Ticket info if created
        """
        print(f"\n{'='*60}")
        print(f"[{self.agent_name}] Processing query: {query}")
        print(f"{'='*60}")
        
        coordination_log = []
        customer_data = None
        ticket_data = None
        
        # Step 1: Extract customer ID if not provided
        if customer_id is None:
            customer_id = self._extract_customer_id(query)
            if customer_id:
                print(f"[{self.agent_name}] Extracted customer ID: {customer_id}")
                coordination_log.append(f"Router extracted customer ID: {customer_id}")
        
        # Step 2: Initial call to Support Agent (without customer data)
        print(f"[{self.agent_name}] → Calling Support Agent for initial reasoning")
        coordination_log.append("Router → Support Agent: Analyze query")
        
        support_result = await self.support_agent.process(
            query=query,
            customer=None,
            tickets=None
        )
        
        action = support_result.get("action")
        print(f"[{self.agent_name}] ← Support Agent action: {action}")
        coordination_log.append(f"Support Agent → Router: action={action}")
        
        # Step 3: Handle different actions
        if action == "request_data":
            # Support Agent needs customer data
            print(f"[{self.agent_name}] Support Agent needs customer data")
            
            if customer_id:
                # Fetch customer data
                print(f"[{self.agent_name}] → Calling Data Agent for customer {customer_id}")
                coordination_log.append(f"Router → Data Agent: Get customer {customer_id}")
                
                customer_data = await self.data_agent.get_customer(customer_id)
                
                if customer_data:
                    print(f"[{self.agent_name}] ← Got customer: {customer_data.get('name')}")
                    coordination_log.append(f"Data Agent → Router: Customer data retrieved")
                    
                    # Also get ticket history
                    print(f"[{self.agent_name}] → Getting ticket history")
                    coordination_log.append(f"Router → Data Agent: Get ticket history")
                    
                    history = await self.data_agent.get_customer_history(customer_id)
                    tickets = history.get("tickets", [])
                    
                    print(f"[{self.agent_name}] ← Got {len(tickets)} tickets")
                    coordination_log.append(f"Data Agent → Router: {len(tickets)} tickets found")
                    
                    # Call Support Agent again with customer data
                    print(f"[{self.agent_name}] → Calling Support Agent with customer context")
                    coordination_log.append("Router → Support Agent: Process with customer data")
                    
                    support_result = await self.support_agent.process(
                        query=query,
                        customer=customer_data,
                        tickets=tickets
                    )
                    
                    action = support_result.get("action")
                    print(f"[{self.agent_name}] ← Support Agent action: {action}")
                    coordination_log.append(f"Support Agent → Router: action={action}")
                else:
                    support_result["response_text"] = f"I couldn't find customer {customer_id} in our system."
            else:
                support_result["response_text"] = "I'd be happy to help! Could you provide your customer ID?"
        
        if action == "create_ticket":
            # Support Agent wants to create a ticket
            print(f"[{self.agent_name}] Support Agent wants to create ticket")
            
            # Make sure we have customer_id
            if not customer_id:
                # Try to get from customer_data if we fetched it
                if customer_data:
                    customer_id = customer_data.get("id")
                else:
                    customer_id = 1  # Default for testing
            
            # Get ticket info from Support Agent
            ticket_info = support_result.get("ticket", {})
            issue = ticket_info.get("issue") or query
            priority = ticket_info.get("priority", "medium")
            
            print(f"[{self.agent_name}] → Creating {priority} priority ticket")
            coordination_log.append(f"Router → Data Agent: Create ticket (priority={priority})")
            
            ticket_data = await self.data_agent.create_ticket(
                customer_id=customer_id,
                issue=issue,
                priority=priority
            )
            
            if ticket_data:
                ticket_id = ticket_data.get("ticket_id")
                print(f"[{self.agent_name}] ← Ticket {ticket_id} created")
                coordination_log.append(f"Data Agent → Router: Ticket {ticket_id} created")
                
                # Add ticket info to response
                support_result["response_text"] += f"\n\nTicket #{ticket_id} has been created with {priority} priority."
        
        # Step 4: Build final response
        final_response = support_result.get("response_text", "I'm here to help!")
        
        # Determine scenario type
        scenario = self._determine_scenario(coordination_log)
        
        print(f"[{self.agent_name}] ✅ Complete! Scenario: {scenario}")
        print(f"{'='*60}\n")
        
        return {
            "query": query,
            "response": final_response,
            "scenario": scenario,
            "coordination_log": coordination_log,
            "customer_info": customer_data,
            "ticket": ticket_data,
            "success": True
        }
    
    def _determine_scenario(self, coordination_log: list) -> str:
        """
        Determine which coordination scenario was used
        
        Args:
            coordination_log: List of coordination steps
            
        Returns:
            Scenario name
        """
        log_str = " ".join(coordination_log)
        
        if "Create ticket" in log_str:
            return "Task Allocation + Ticket Creation"
        elif "Get customer" in log_str and "Get ticket history" in log_str:
            return "Multi-Step Coordination"
        elif "Get customer" in log_str:
            return "Task Allocation"
        else:
            return "Simple Query"
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Return A2A Agent Card metadata
        
        Returns:
            Agent Card with capabilities and skills
        """
        return {
            "name": "Router Agent",
            "description": "Orchestrator agent that coordinates Data and Support agents using LLM reasoning",
            "version": "1.0.0",
            "capabilities": {
                "orchestration": True,
                "multi_agent_coordination": True,
                "intent_analysis": True,
                "workflow_management": True,
            },
            "skills": [
                {
                    "id": "route_query",
                    "name": "Route Query",
                    "description": "Analyze and route customer queries to appropriate agents",
                },
                {
                    "id": "coordinate_agents",
                    "name": "Coordinate Agents",
                    "description": "Coordinate multiple agents for complex queries",
                },
                {
                    "id": "synthesize_response",
                    "name": "Synthesize Response",
                    "description": "Combine responses from multiple agents into coherent answer",
                },
            ],
            "sub_agents": ["Data Agent", "Support Agent"],
        }


# ======================
# Test the Router
# ======================
async def test_router_agent():
    """Test the Router Agent"""
    router = RouterAgent()
    
    print("\n" + "="*80)
    print("Testing Router Agent - Multi-Agent Coordination")
    print("="*80)
    
    # Test 1: Simple query with customer ID
    print("\n  Test 1: Simple customer lookup")
    result = await router.process_query("Get customer information for ID 1")
    print(f"\n  Final Response:\n{result['response']}")
    print(f"\n  Scenario: {result['scenario']}")
    print(f"\n  Coordination Steps:")
    for step in result['coordination_log']:
        print(f"   - {step}")
    
    # Test 2: Query needing support
    print("\n" + "="*80)
    print("\n  Test 2: Customer wants upgrade")
    result = await router.process_query("I'm customer 1 and I want to upgrade my account")
    print(f"\n  Final Response:\n{result['response']}")
    print(f"\n  Scenario: {result['scenario']}")
    print(f"\n  Coordination Steps:")
    for step in result['coordination_log']:
        print(f"   - {step}")
    
    # Test 3: Urgent issue requiring ticket
    print("\n" + "="*80)
    print("\n  Test 3: Urgent billing issue")
    result = await router.process_query("I'm customer 1 and I've been charged twice!", customer_id=1)
    print(f"\n  Final Response:\n{result['response']}")
    print(f"\n  Scenario: {result['scenario']}")
    if result.get('ticket'):
        print(f"\n  Ticket Created: #{result['ticket'].get('ticket_id')}")
    print(f"\n  Coordination Steps:")
    for step in result['coordination_log']:
        print(f"   - {step}")
    
    print("\n" + "="*80)
    print("✅ Router Agent tests complete!")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    print("⚠️  Make sure MCP server is running: python mcp/mcp_server.py")
    asyncio.run(test_router_agent())