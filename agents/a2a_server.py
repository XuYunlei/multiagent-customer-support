# agents/a2a_server.py
"""
A2A Server - Exposes Google ADK Agents as HTTP Services
Each Google ADK agent automatically exposes A2A endpoints
"""

import asyncio
import nest_asyncio
import uvicorn
import sys
from pathlib import Path

# Add project root to path BEFORE importing agents
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Now these imports will work because project_root is in sys.path
from agents.data_agent import customer_data_agent, customer_data_agent_card
from agents.support_agent import support_agent, support_agent_card
from agents.router_agent import router_agent, router_agent_card

# Apply nest_asyncio for Jupyter/async compatibility
nest_asyncio.apply()

def create_agent_a2a_server(agent, agent_card):
    """Create an A2A server for any ADK agent.

    Args:
        agent: The ADK agent instance
        agent_card: The ADK agent card

    Returns:
        A2AStarletteApplication instance
    """
    runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=config)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    return A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

async def run_agent_server(agent, agent_card, port):
    """Run a single agent server."""
    app = create_agent_a2a_server(agent, agent_card)
    
    # Build the Starlette app
    starlette_app = app.build()
    
    # Debug: Print available routes
    print(f"\n🔍 Available routes for {agent.name}:")
    for route in starlette_app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', ['GET'])
            print(f"   {route.path} - {methods}")
    
    # Health endpoint removed to save quota

    config = uvicorn.Config(
        starlette_app,
        host='127.0.0.1',
        port=port,
        log_level='info',
        loop='none',  # Important: let uvicorn use the current loop
    )

    server = uvicorn.Server(config)
    await server.serve()

async def start_all_servers():
    """Start all agent servers."""
    print("Starting A2A Agent Servers...")
    
    # Store server tasks
    server_tasks = []
    
    # Start Customer Data Agent (port 10021)
    task1 = asyncio.create_task(
        run_agent_server(customer_data_agent, customer_data_agent_card, 10021)
    )
    server_tasks.append(task1)
    print(f"✅ Customer Data Agent starting on http://127.0.0.1:10021")
    
    # Start Support Agent (port 10022)
    task2 = asyncio.create_task(
        run_agent_server(support_agent, support_agent_card, 10022)
    )
    server_tasks.append(task2)
    print(f"✅ Support Agent starting on http://127.0.0.1:10022")
    
    # Start Router Agent (port 10020)
    task3 = asyncio.create_task(
        run_agent_server(router_agent, router_agent_card, 10020)
    )
    server_tasks.append(task3)
    print(f"✅ Router Agent starting on http://127.0.0.1:10020")
    
    print("\n🎉 All agent servers started!")
    print("   - Router Agent: http://127.0.0.1:10020")
    print("   - Customer Data Agent: http://127.0.0.1:10021")
    print("   - Support Agent: http://127.0.0.1:10022")
    print("\nPress Ctrl+C to stop all servers.\n")
    
    # Wait for all servers
    await asyncio.gather(*server_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(start_all_servers())
    except KeyboardInterrupt:
        print("\n\nShutting down all servers...")
