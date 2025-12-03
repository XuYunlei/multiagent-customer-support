# agents/a2a_server.py
"""
A2A Server - Agent-to-Agent Protocol Implementation

Runs three agents as independent HTTP services:
- Router Agent (port 10020) - Orchestrator
- Data Agent (port 10021) - Database access via MCP
- Support Agent (port 10022) - LLM reasoning with OpenAI

Each agent exposes:
- /.well-known/agent-card.json - A2A metadata
- /process - Main endpoint for queries
- /health - Health check
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import multiprocessing
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router_agent import RouterAgent
from data_agent import DataAgent
from support_agent import SupportAgent


# ======================
# Request/Response Models
# ======================

class QueryRequest(BaseModel):
    """Standard query request format"""
    query: str
    customer_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Standard agent response format"""
    success: bool
    response: str
    metadata: Optional[Dict[str, Any]] = None


# ======================
# Router Agent Server (Port 10020)
# ======================

def create_router_app():
    """Create FastAPI app for Router Agent"""
    app = FastAPI(title="Router Agent A2A Server")
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Router Agent
    router_agent = RouterAgent()
    
    @app.get("/.well-known/agent-card.json")
    async def get_agent_card():
        """A2A Agent Card endpoint"""
        return router_agent.get_agent_card()
    
    @app.post("/process")
    async def process_query(request: QueryRequest):
        """Main query processing endpoint"""
        try:
            print(f"\n[Router Server] Received query: {request.query}")
            
            result = await router_agent.process_query(
                query=request.query,
                customer_id=request.customer_id
            )
            
            return {
                "success": True,
                "response": result.get("response"),
                "metadata": {
                    "scenario": result.get("scenario"),
                    "coordination_log": result.get("coordination_log"),
                    "customer_info": result.get("customer_info"),
                    "ticket": result.get("ticket"),
                }
            }
        except Exception as e:
            print(f"[Router Server] Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "agent": "Router Agent", "port": 10020}
    
    return app


# ======================
# Data Agent Server (Port 10021)
# ======================

def create_data_app():
    """Create FastAPI app for Data Agent"""
    app = FastAPI(title="Data Agent A2A Server")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Data Agent
    data_agent = DataAgent()
    
    @app.get("/.well-known/agent-card.json")
    async def get_agent_card():
        """A2A Agent Card endpoint"""
        return data_agent.get_agent_card()
    
    @app.post("/get_customer")
    async def get_customer(customer_id: int):
        """Get customer by ID"""
        try:
            customer = await data_agent.get_customer(customer_id)
            return {"success": True, "data": customer}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/list_customers")
    async def list_customers(status: str = "active", limit: int = 100):
        """List customers by status"""
        try:
            customers = await data_agent.list_customers(status, limit)
            return {"success": True, "data": customers}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/create_ticket")
    async def create_ticket(customer_id: int, issue: str, priority: str = "medium"):
        """Create a support ticket"""
        try:
            ticket = await data_agent.create_ticket(customer_id, issue, priority)
            return {"success": True, "data": ticket}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/get_history")
    async def get_history(customer_id: int):
        """Get customer ticket history"""
        try:
            history = await data_agent.get_customer_history(customer_id)
            return {"success": True, "data": history}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "agent": "Data Agent", "port": 10021}
    
    return app


# ======================
# Support Agent Server (Port 10022)
# ======================

def create_support_app():
    """Create FastAPI app for Support Agent"""
    app = FastAPI(title="Support Agent A2A Server")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Support Agent
    support_agent = SupportAgent()
    
    @app.get("/.well-known/agent-card.json")
    async def get_agent_card():
        """A2A Agent Card endpoint"""
        return support_agent.get_agent_card()
    
    @app.post("/process")
    async def process_query(
        query: str,
        customer: Optional[Dict[str, Any]] = None,
        tickets: Optional[list] = None
    ):
        """Process customer query with LLM"""
        try:
            result = await support_agent.process(query, customer, tickets)
            return {"success": True, "data": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "agent": "Support Agent", "port": 10022}
    
    return app


# ======================
# Server Process Functions
# ======================

def run_router_server():
    """Run Router Agent server"""
    print("\n🚀 Starting Router Agent Server on port 10020...")
    app = create_router_app()
    uvicorn.run(app, host="0.0.0.0", port=10020, log_level="info")


def run_data_server():
    """Run Data Agent server"""
    print("\n🚀 Starting Data Agent Server on port 10021...")
    app = create_data_app()
    uvicorn.run(app, host="0.0.0.0", port=10021, log_level="info")


def run_support_server():
    """Run Support Agent server"""
    print("\n🚀 Starting Support Agent Server on port 10022...")
    app = create_support_app()
    uvicorn.run(app, host="0.0.0.0", port=10022, log_level="info")


# ======================
# Main Entry Point
# ======================

def main():
    """Start all three agent servers"""
    print("="*80)
    print("A2A Multi-Agent Customer Service System")
    print("="*80)
    print("\n📋 Starting 3 independent agent servers:")
    print("   • Router Agent  → http://localhost:10020")
    print("   • Data Agent    → http://localhost:10021")
    print("   • Support Agent → http://localhost:10022")
    print("\n⚠️  Make sure MCP server is running on port 8001!")
    print("   Run: python mcp/mcp_server.py\n")
    print("="*80 + "\n")
    
    # Create processes for each server
    processes = []
    
    try:
        # Start Router Agent
        p1 = multiprocessing.Process(target=run_router_server, name="RouterAgent")
        p1.start()
        processes.append(p1)
        
        # Start Data Agent
        p2 = multiprocessing.Process(target=run_data_server, name="DataAgent")
        p2.start()
        processes.append(p2)
        
        # Start Support Agent
        p3 = multiprocessing.Process(target=run_support_server, name="SupportAgent")
        p3.start()
        processes.append(p3)
        
        print("\n✅ All agents running! Press Ctrl+C to stop.\n")
        
        # Wait for all processes
        for p in processes:
            p.join()
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all agents...")
        for p in processes:
            p.terminate()
            p.join()
        print("✅ All agents stopped.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        for p in processes:
            p.terminate()
            p.join()


if __name__ == "__main__":
    # Required for multiprocessing on some platforms
    multiprocessing.set_start_method('spawn', force=True)
    main()