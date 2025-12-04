# agents/router_agent.py
"""
Router Agent - Google ADK SequentialAgent with A2A Coordination
A2A-compatible orchestrator that coordinates Data and Support agents
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from google.adk.agents import SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TransportProtocol,
)

# Create remote references to other agents
remote_customer_data_agent = RemoteA2aAgent(
    name='customer_data',
    description='Specialist agent for accessing customer database information',
    agent_card=f'http://localhost:10021{AGENT_CARD_WELL_KNOWN_PATH}',
)

remote_support_agent = RemoteA2aAgent(
    name='support',
    description='Specialist agent for handling customer support queries',
    agent_card=f'http://localhost:10022{AGENT_CARD_WELL_KNOWN_PATH}',
)

# Router agent - uses SequentialAgent which automatically routes through sub-agents
# SequentialAgent will intelligently route queries to appropriate sub-agents
router_agent = SequentialAgent(
    name='router_agent',
    sub_agents=[remote_customer_data_agent, remote_support_agent],
    # Note: SequentialAgent uses LLM to determine which sub-agent to use
    # It will route data queries to customer_data_agent and support queries to support_agent
)

router_agent_card = AgentCard(
    name='Router Agent',
    url='http://localhost:10020',
    description='Orchestrator agent that receives queries, analyzes intent, and routes to appropriate specialist agents',
    version='1.0',
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id='route_query',
            name='Route Customer Query',
            description='Analyzes query intent and routes to appropriate specialist agent',
            tags=['routing', 'orchestration', 'coordination'],
            examples=[
                'Get customer information for ID 5',
                'I\'m customer 1 and need help upgrading my account',
                'Show me all active customers who have open tickets',
            ],
        ),
        AgentSkill(
            id='coordinate_agents',
            name='Coordinate Multiple Agents',
            description='Coordinates responses from multiple specialist agents for complex queries',
            tags=['coordination', 'multi-agent', 'orchestration'],
            examples=[
                'Update my email and show my ticket history',
                'I want to cancel but have billing issues',
            ],
        ),
        AgentSkill(
            id='analyze_intent',
            name='Analyze Query Intent',
            description='Analyzes customer queries to determine intent and required actions',
            tags=['analysis', 'intent', 'routing'],
            examples=[
                'Determine if query needs data retrieval or support',
                'Identify if multiple agents are needed',
            ],
        ),
    ],
)

# Export the agent
__all__ = ['router_agent', 'router_agent_card']