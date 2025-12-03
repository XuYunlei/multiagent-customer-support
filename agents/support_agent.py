# agents/support_agent.py
"""
Support Agent with OpenAI LLM
Handles customer support queries with intelligent reasoning
"""
import json
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()


class SupportAgent:
    """
    LLM-powered Support Agent
    
    Responsibilities:
    - Analyze customer queries using LLM
    - Provide helpful support responses
    - Decide when to create tickets
    - Determine priorities
    - Request customer data when needed
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize Support Agent with OpenAI
        
        Args:
            model: OpenAI model to use (gpt-4o-mini is fast and cheap)
        """
        self.client = AsyncOpenAI()  # Uses OPENAI_API_KEY from env
        self.model = model
        self.agent_name = "Support Agent"
    
    async def process(
        self,
        query: str,
        customer: Optional[Dict[str, Any]] = None,
        tickets: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer query using LLM reasoning
        
        Args:
            query: The customer's question or request
            customer: Customer information (if available)
            tickets: Customer's ticket history (if available)
            
        Returns:
            Dictionary with:
            - action: "respond", "request_data", or "create_ticket"
            - response_text: Human-friendly response
            - ticket: Ticket info if action is "create_ticket"
            - requires: What data is needed if action is "request_data"
        """
        
        system_prompt = """You are an intelligent Support Agent in a customer service system.

Your role:
1. Understand customer queries and provide helpful responses
2. Decide what action to take based on the situation
3. Create support tickets when issues need tracking
4. Request customer data when you need more information

AVAILABLE ACTIONS:
- "respond": You have enough information to answer the customer
- "request_data": You need customer information (specify what you need)
- "create_ticket": Create a support ticket for the issue

OUTPUT FORMAT (JSON only):
{
  "action": "respond|request_data|create_ticket",
  "response_text": "Your helpful response to the customer",
  "ticket": {
    "issue": "Brief description",
    "priority": "low|medium|high"
  },
  "requires": {
    "customer_info": true/false,
    "ticket_history": true/false
  }
}

GUIDELINES:
- Be professional, friendly, and helpful
- For urgent issues (billing, refunds, security), set priority to "high"
- For simple questions, respond directly
- For problems that need tracking, create a ticket
- If you need more context, request customer data
- For upgrade requests: if customer tier is unknown, assume basic tier and provide upgrade options to premium/enterprise

Examples:

Query: "I want to upgrade my account"
→ action: "request_data" (need to know current customer tier)

Query: "I've been charged twice!"
→ action: "create_ticket" with priority "high"

Query: "How do I reset my password?"
→ action: "respond" (can answer directly)
"""

        # Build context for the LLM
        context = {
            "query": query,
            "has_customer_info": customer is not None,
            "has_ticket_history": tickets is not None,
        }
        
        if customer:
            context["customer"] = {
                "id": customer.get("id"),
                "name": customer.get("name"),
                "status": customer.get("status"),
                "email": customer.get("email"),
            }
        
        if tickets:
            context["recent_tickets"] = [
                {
                    "id": t.get("id"),
                    "issue": t.get("issue"),
                    "status": t.get("status"),
                    "priority": t.get("priority"),
                }
                for t in tickets[:5]  # Only send recent 5
            ]
        
        # Call OpenAI
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,  # Lower = more consistent
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(context, indent=2)},
                ],
            )
            
            # Parse LLM response
            content = response.choices[0].message.content
            result = json.loads(content) if content else {}
            
            # Ensure required fields exist
            if "action" not in result:
                result["action"] = "respond"
            if "response_text" not in result:
                result["response_text"] = "I'm here to help. Could you provide more details?"
            
            return result
            
        except Exception as e:
            # Fallback if LLM fails
            print(f"[Support Agent] Error calling OpenAI: {e}")
            return {
                "action": "respond",
                "response_text": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "error": str(e)
            }
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Return A2A Agent Card metadata
        
        Returns:
            Agent Card with capabilities and skills
        """
        return {
            "name": "Support Agent",
            "description": "LLM-powered customer support agent with OpenAI GPT-4o-mini",
            "version": "1.0.0",
            "capabilities": {
                "llm_reasoning": True,
                "natural_language": True,
                "ticket_creation": True,
                "priority_assessment": True,
            },
            "skills": [
                {
                    "id": "customer_support",
                    "name": "Customer Support",
                    "description": "Answer customer questions and resolve issues",
                },
                {
                    "id": "ticket_management",
                    "name": "Ticket Management",
                    "description": "Create and manage support tickets",
                },
                {
                    "id": "escalation",
                    "name": "Issue Escalation",
                    "description": "Identify and escalate urgent issues",
                },
            ],
            "model": self.model,
            "provider": "OpenAI",
        }


# ======================
# Test the agent
# ======================
async def test_support_agent():
    """Test the Support Agent"""
    agent = SupportAgent()
    
    print("\n" + "="*60)
    print("Testing Support Agent with OpenAI LLM")
    print("="*60)
    
    # Test 1: Simple query without context
    print("\n  Test 1: Simple upgrade query")
    result = await agent.process("I want to upgrade my account")
    print(f"Action: {result.get('action')}")
    print(f"Response: {result.get('response_text')}")
    
    # Test 2: With customer context
    print("\n  Test 2: Query with customer info")
    customer = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "status": "active"
    }
    result = await agent.process("I want to upgrade my account", customer=customer)
    print(f"Action: {result.get('action')}")
    print(f"Response: {result.get('response_text')}")
    
    # Test 3: Urgent issue
    print("\n  Test 3: Urgent billing issue")
    result = await agent.process("I've been charged twice this month!", customer=customer)
    print(f"Action: {result.get('action')}")
    print(f"Response: {result.get('response_text')}")
    if result.get('ticket'):
        print(f"Ticket Priority: {result['ticket'].get('priority')}")
    
    print("\n" + "="*60)
    print("✅ Support Agent tests complete!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_support_agent())