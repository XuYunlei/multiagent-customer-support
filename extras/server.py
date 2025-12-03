# extras/server.py
"""
User-Facing API Server
Provides a simple REST API for the multi-agent customer service system

This is the main entry point for users/applications to interact with the system.
It forwards requests to the Router Agent (A2A) which coordinates the other agents.

Port: 8000
"""

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Customer Service API",
    description="REST API for intelligent customer service using multiple AI agents",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ROUTER_AGENT_URL = "http://localhost:10020"
DATA_AGENT_URL = "http://localhost:10021"
MCP_SERVER_URL = "http://localhost:8001"


# ======================
# Request/Response Models
# ======================

class QueryRequest(BaseModel):
    """User query request"""
    query: str = Field(..., description="Customer query or question")
    customer_id: Optional[int] = Field(None, description="Customer ID (if known)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "I need help with my account",
                "customer_id": 1
            }
        }


class QueryResponse(BaseModel):
    """Query response"""
    success: bool
    response: str
    scenario: Optional[str] = None
    coordination_steps: Optional[int] = None
    ticket_created: Optional[Dict[str, Any]] = None


class CustomerResponse(BaseModel):
    """Customer information response"""
    success: bool
    customer: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TicketResponse(BaseModel):
    """Ticket information response"""
    success: bool
    ticket: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """System health response"""
    status: str
    components: Dict[str, str]


# ======================
#    Helper Functions
# ======================

async def check_agent_health(url: str) -> bool:
    """Check if an agent is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except:
        return False


# ======================
#   Main API Endpoints
# ======================

@app.get("/", tags=["General"])
async def root():
    """API root - provides basic information"""
    return {
        "service": "Multi-Agent Customer Service System",
        "version": "1.0.0",
        "description": "Intelligent customer service using coordinated AI agents",
        "endpoints": {
            "query": "/api/query - Submit customer queries",
            "customer": "/api/customer/{id} - Get customer information",
            "tickets": "/api/tickets/{customer_id} - Get customer tickets",
            "health": "/health - System health check",
            "docs": "/docs - Interactive API documentation"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Check system health
    
    Returns the health status of all system components
    """
    components = {}
    
    # Check Router Agent
    components["router_agent"] = "healthy" if await check_agent_health(ROUTER_AGENT_URL) else "unhealthy"
    
    # Check Data Agent
    components["data_agent"] = "healthy" if await check_agent_health(DATA_AGENT_URL) else "unhealthy"
    
    # Check MCP Server
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/health")
            components["mcp_server"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        components["mcp_server"] = "unhealthy"
    
    # Overall status
    all_healthy = all(status == "healthy" for status in components.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "components": components
    }


@app.post("/api/query", response_model=QueryResponse, tags=["Customer Service"])
async def submit_query(request: QueryRequest):
    """
    Submit a customer service query
    
    The query will be processed by multiple coordinated AI agents:
    - Router Agent analyzes and routes the query
    - Support Agent provides intelligent responses using LLM
    - Data Agent accesses customer information and creates tickets
    
    Example queries:
    - "What's my account status?" (with customer_id)
    - "I need help upgrading my account"
    - "I've been charged twice, please help!"
    """
    try:
        logger.info(f"Received query: {request.query}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ROUTER_AGENT_URL}/process",
                json={
                    "query": request.query,
                    "customer_id": request.customer_id
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Router Agent request failed"
                )
            
            result = response.json()
            metadata = result.get("metadata", {})
            
            return QueryResponse(
                success=True,
                response=result.get("response", "No response generated"),
                scenario=metadata.get("scenario"),
                coordination_steps=len(metadata.get("coordination_log", [])),
                ticket_created=metadata.get("ticket")
            )
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to agent system. Please ensure all agents are running."
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
async def get_customer(customer_id: int):
    """
    Get customer information by ID
    
    Retrieves detailed information about a specific customer including:
    - Name, email, phone
    - Account status
    - Created/updated timestamps
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DATA_AGENT_URL}/get_customer",
                params={"customer_id": customer_id}
            )
            
            if response.status_code != 200:
                return CustomerResponse(
                    success=False,
                    error=f"Customer {customer_id} not found"
                )
            
            result = response.json()
            return CustomerResponse(
                success=True,
                customer=result.get("data")
            )
            
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        return CustomerResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/tickets/{customer_id}", tags=["Tickets"])
async def get_customer_tickets(customer_id: int):
    """
    Get all tickets for a customer
    
    Returns the complete ticket history including:
    - Ticket ID, issue description
    - Status (open, in_progress, resolved)
    - Priority level
    - Created timestamp
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DATA_AGENT_URL}/get_history",
                params={"customer_id": customer_id}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            result = response.json()
            return {
                "success": True,
                "customer_id": customer_id,
                "tickets": result.get("data", {}).get("tickets", []),
                "count": result.get("data", {}).get("count", 0)
            }
            
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers", tags=["Customers"])
async def list_customers(
    status: str = Query("active", description="Customer status filter"),
    limit: int = Query(10, description="Maximum number of customers to return")
):
    """
    List customers filtered by status
    
    Returns a list of customers with the specified status.
    Useful for admin interfaces or reports.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DATA_AGENT_URL}/list_customers",
                params={"status": status, "limit": limit}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to list customers")
            
            result = response.json()
            return {
                "success": True,
                "customers": result.get("data", []),
                "count": len(result.get("data", []))
            }
            
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ticket", response_model=TicketResponse, tags=["Tickets"])
async def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = Query("medium", regex="^(low|medium|high)$")
):
    """
    Create a support ticket
    
    Creates a new support ticket for a customer.
    The ticket will be tracked in the system with the specified priority.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DATA_AGENT_URL}/create_ticket",
                params={
                    "customer_id": customer_id,
                    "issue": issue,
                    "priority": priority
                }
            )
            
            if response.status_code != 200:
                return TicketResponse(
                    success=False,
                    error="Failed to create ticket"
                )
            
            result = response.json()
            return TicketResponse(
                success=True,
                ticket=result.get("data")
            )
            
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return TicketResponse(
            success=False,
            error=str(e)
        )


# ======================
# Example Queries Endpoint
# ======================

@app.get("/api/examples", tags=["General"])
async def get_examples():
    """
    Get example queries to try
    
    Returns a list of example queries that demonstrate
    different coordination scenarios
    """
    return {
        "examples": [
            {
                "scenario": "Simple Query",
                "query": "Get customer information for ID 1",
                "customer_id": 1,
                "description": "Straightforward data lookup"
            },
            {
                "scenario": "Support Request",
                "query": "I need help upgrading my account",
                "customer_id": 1,
                "description": "LLM-powered support response"
            },
            {
                "scenario": "Urgent Issue",
                "query": "I've been charged twice, please help!",
                "customer_id": 1,
                "description": "Creates high-priority ticket"
            },
            {
                "scenario": "Multi-Intent",
                "query": "Update my email to new@email.com and show my tickets",
                "customer_id": 1,
                "description": "Multiple actions in one query"
            },
            {
                "scenario": "Complex Query",
                "query": "Show me all active customers with open tickets",
                "customer_id": None,
                "description": "Complex data aggregation"
            }
        ]
    }


# ======================
# Main Entry Point
# ======================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Multi-Agent Customer Service API")
    print("="*80)
    print("\n📋 Starting user-facing API server on port 8000")
    print("\n⚠️  Prerequisites:")
    print("   1. MCP Server running on port 8001")
    print("   2. A2A Agents running on ports 10020-10022")
    print("\n📚 Once started, visit:")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/health")
    print("   • Examples: http://localhost:8000/api/examples")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )