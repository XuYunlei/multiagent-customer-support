# agents/data_agent.py
"""
Data Agent - Google ADK Agent with MCP Tools
A2A-compatible agent that provides database access via MCP
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TransportProtocol,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from mcp_impl.mcp_tools import (
    get_customer,
    list_customers,
    update_customer,
    create_ticket,
    get_customer_history,
    ALL_TOOLS
)

# Create Google ADK Agent with MCP tools
customer_data_agent = Agent(
    name='customer_data_agent',
    model='gemini-2.0-flash-lite',
    instruction="""You are a Data Agent in a customer support system.
            Your role:
            - Access customer information from the database using MCP tools
            - Retrieve customer details, ticket history, and related data
            - Update customer information when requested
            - Create support tickets when needed

            Available Tools:
            - get_customer(customer_id): Get customer information by ID
            - list_customers(status, limit): List customers by status
            - update_customer(customer_id, data): Update customer information
            - create_ticket(customer_id, issue, priority): Create a support ticket
            - get_customer_history(customer_id): Get all tickets for a customer

            CRITICAL INSTRUCTIONS:
            - ALWAYS extract customer IDs from queries when mentioned (e.g., "customer 1", "ID 5", "customer ID 12345")
            - If a query mentions "my account", "my tickets", "my email" without an ID, use customer_id=1 as default for demo purposes
            - DO NOT ask for customer ID if it can be extracted from the query or inferred
            - ALWAYS use MCP tools to retrieve data - never guess or make up information
            - When a query asks for customer info, tickets, or account status, IMMEDIATELY call the appropriate tool
            - For queries like "show me all tickets" or "my account status", use get_customer(1) and get_customer_history(1) if no ID is specified

            Guidelines:
            - Always use the appropriate tool to access data
            - Return clear, structured responses with actual data from the database
            - Handle errors gracefully
            - Provide helpful error messages if data is not found
            """,
    tools=ALL_TOOLS,
)

customer_data_agent_card = AgentCard(
    name='Customer Data Agent',
    url='http://localhost:10021',
    description='Specialist agent for accessing and managing customer database information via MCP tools',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain', 'application/json'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='get_customer_info',
            name='Get Customer Information',
            description='Retrieves customer details by ID using customers.id field',
            tags=['customer', 'data', 'retrieval', 'mcp'],
            examples=[
                'Get customer information for ID 1',
                'Retrieve customer 12345',
                'Show me customer details for ID 5',
            ],
        ),
        AgentSkill(
            id='list_customers',
            name='List Customers',
            description='Lists customers with optional status filtering using customers.status field',
            tags=['customer', 'list', 'filter', 'mcp'],
            examples=[
                'List all active customers',
                'Show me customers with disabled status',
                'Get 10 customers',
            ],
        ),
        AgentSkill(
            id='update_customer',
            name='Update Customer',
            description='Updates customer records using customers fields',
            tags=['customer', 'update', 'modify', 'mcp'],
            examples=[
                'Update email for customer 1',
                'Change phone number for customer 123',
            ],
        ),
        AgentSkill(
            id='get_customer_history',
            name='Get Customer History',
            description='Retrieves ticket history for a customer using tickets.customer_id field',
            tags=['customer', 'history', 'tickets', 'mcp'],
            examples=[
                'Show ticket history for customer 1',
                'Get all tickets for customer 12345',
            ],
        ),
        AgentSkill(
            id='get_customers_with_open_tickets',
            name='Get Customers with Open Tickets',
            description='Finds customers who have open tickets, optionally filtered by status',
            tags=['customer', 'tickets', 'query', 'mcp'],
            examples=[
                'Show active customers with open tickets',
                'List customers who have unresolved tickets',
            ],
        ),
    ],
)

# Export the agent
__all__ = ['customer_data_agent', 'customer_data_agent_card']