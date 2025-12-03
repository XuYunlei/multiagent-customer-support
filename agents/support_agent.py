# agents/support_agent.py
"""
Support Agent - Google ADK Agent with LLM Reasoning
A2A-compatible agent that provides customer support using Gemini
"""

import sys
from pathlib import Path
from google.adk.agents import Agent
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TransportProtocol,
)
from mcp_impl.mcp_tools import ALL_TOOLS  

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Create Google ADK Agent for customer support
support_agent = Agent(
    name="support_agent",
    model="gemini-2.0-flash-lite",
    description="LLM-powered customer support agent that analyzes queries and provides helpful responses",
    instruction="""You are an intelligent Support Agent in a customer service system.

Your role:
1. Understand customer queries and provide helpful responses
2. Analyze customer needs and determine appropriate actions
3. Provide professional, friendly, and empathetic support
4. Escalate urgent issues appropriately
5. Use MCP tools to access customer data and create tickets when needed

CRITICAL INSTRUCTIONS:
- ALWAYS extract customer IDs from queries when mentioned (e.g., "I'm customer 1", "customer ID 5")
- If a query mentions "my account", "my tickets", "my email" without an ID, use customer_id=1 as default for demo purposes
- DO NOT ask for customer ID if it can be extracted from the query
- USE MCP TOOLS proactively: get_customer(), get_customer_history(), create_ticket()
- For billing issues, duplicate charges, or urgent matters, create a high-priority ticket immediately
- For account upgrades or changes, first get customer info, then provide guidance

Guidelines:
- Be professional, friendly, and helpful
- For urgent issues (billing, refunds, security), create high-priority tickets immediately
- For simple questions, provide direct answers using available data
- For problems that need tracking, create a ticket using create_ticket()
- Use get_customer() and get_customer_history() to access customer context before responding

When responding:
- Use clear, natural language
- Be empathetic to customer concerns
- Provide actionable solutions based on actual customer data
- Only ask clarifying questions when absolutely necessary
""",
    tools=ALL_TOOLS,
)

support_agent_card = AgentCard(
    name='Support Agent',
    url='http://localhost:10022',
    description='Specialist agent for handling customer support queries, ticket creation, and issue resolution',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='create_ticket',
            name='Create Support Ticket',
            description='Creates a new support ticket using tickets fields',
            tags=['support', 'ticket', 'create', 'mcp'],
            examples=[
                'Create a ticket for customer 1 about account upgrade',
                'Open a high priority ticket for billing issue',
            ],
        ),
        AgentSkill(
            id='handle_support_query',
            name='Handle Support Query',
            description='Processes general customer support queries and provides solutions',
            tags=['support', 'help', 'assistance'],
            examples=[
                'I need help with my account',
                'How do I upgrade my subscription?',
                'I have a billing question',
            ],
        ),
        AgentSkill(
            id='escalate_issue',
            name='Escalate Issue',
            description='Escalates complex or urgent issues appropriately',
            tags=['support', 'escalation', 'urgent'],
            examples=[
                'I\'ve been charged twice, please refund immediately!',
                'My account has been compromised',
            ],
        ),
    ],
)

# Export the agent
__all__ = ['support_agent', 'support_agent_card']