# mcp_impl/mcp_server.py
"""
MCP HTTP Server for Customer Service System
Implements MCP protocol over HTTP with SQLite database operations
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Database path relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "src" / "support.db"


def get_db_connection():
    """Get database connection with row factory for dict-like access"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ======================
#    Tool Definitions
# ======================

TOOLS = [
    {
        "name": "get_customer",
        "description": "Get customer information by customer ID. Uses customers.id field.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer ID to retrieve"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "list_customers",
        "description": "List customers filtered by status. Uses customers.status field.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "disabled"],
                    "description": "Filter by customer status"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of customers to return",
                    "default": 50
                }
            },
            "required": ["status"]
        }
    },
    {
        "name": "update_customer",
        "description": "Update customer information. Uses customers fields (name, email, phone, status).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer ID to update"
                },
                "data": {
                    "type": "object",
                    "description": "Dictionary of fields to update (name, email, phone, status)",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "status": {"type": "string", "enum": ["active", "disabled"]}
                    }
                }
            },
            "required": ["customer_id", "data"]
        }
    },
    {
        "name": "create_ticket",
        "description": "Create a new support ticket. Uses tickets fields (customer_id, issue, priority).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer ID for this ticket"
                },
                "issue": {
                    "type": "string",
                    "description": "Description of the issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Priority level of the ticket",
                    "default": "medium"
                }
            },
            "required": ["customer_id", "issue", "priority"]
        }
    },
    {
        "name": "get_customer_history",
        "description": "Get all tickets for a customer. Uses tickets.customer_id field.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer ID to get ticket history for"
                }
            },
            "required": ["customer_id"]
        }
    }
]


# ======================
# Tool Implementation Functions
# ======================

def handle_tool_call(name: str, args: Dict[str, Any]) -> tuple[bool, Any]:
    """
    Execute tool and return (success, result/error)
    
    Args:
        name: Tool name
        args: Tool arguments
        
    Returns:
        Tuple of (success: bool, result: Any or error_message: str)
    """
    try:
        if name == "get_customer":
            customer_id = args.get("customer_id")
            if customer_id is None:
                return (False, "customer_id is required")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return (True, dict(row))
            else:
                return (False, f"Customer {customer_id} not found")
        
        elif name == "list_customers":
            status = args.get("status")
            limit = args.get("limit", 50)
            
            if status is None:
                return (False, "status is required")
            
            if status not in ["active", "disabled"]:
                return (False, f"Invalid status: {status}. Must be 'active' or 'disabled'")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM customers WHERE status = ? LIMIT ?",
                (status, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            return (True, [dict(row) for row in rows])
        
        elif name == "update_customer":
            customer_id = args.get("customer_id")
            data = args.get("data", {})
            
            if customer_id is None:
                return (False, "customer_id is required")
            if not data:
                return (False, "data dictionary is required")
            
            # Validate allowed fields
            allowed_fields = ["name", "email", "phone", "status"]
            update_fields = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_fields:
                return (False, f"No valid fields to update. Allowed: {allowed_fields}")
            
            # Validate status if provided
            if "status" in update_fields and update_fields["status"] not in ["active", "disabled"]:
                return (False, "status must be 'active' or 'disabled'")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
            if not cursor.fetchone():
                conn.close()
                return (False, f"Customer {customer_id} not found")
            
            # Build UPDATE query
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values())
            values.append(customer_id)
            
            query = f"UPDATE customers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            
            try:
                cursor.execute(query, values)
                conn.commit()
                conn.close()
                
                return (True, {
                    "message": f"Customer {customer_id} updated successfully",
                    "updated_fields": list(update_fields.keys())
                })
            except Exception as e:
                conn.close()
                return (False, f"Error updating customer: {str(e)}")
        
        elif name == "create_ticket":
            customer_id = args.get("customer_id")
            issue = args.get("issue")
            priority = args.get("priority", "medium")
            
            if customer_id is None:
                return (False, "customer_id is required")
            if not issue:
                return (False, "issue is required")
            if priority not in ["low", "medium", "high"]:
                return (False, "priority must be 'low', 'medium', or 'high'")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
            if not cursor.fetchone():
                conn.close()
                return (False, f"Customer {customer_id} not found")
            
            # Create ticket
            try:
                cursor.execute(
                    "INSERT INTO tickets (customer_id, issue, priority, status) VALUES (?, ?, ?, 'open')",
                    (customer_id, issue, priority)
                )
                ticket_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return (True, {
                    "ticket_id": ticket_id,
                    "customer_id": customer_id,
                    "issue": issue,
                    "priority": priority,
                    "status": "open"
                })
            except Exception as e:
                conn.close()
                return (False, f"Error creating ticket: {str(e)}")
        
        elif name == "get_customer_history":
            customer_id = args.get("customer_id")
            
            if customer_id is None:
                return (False, "customer_id is required")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if customer exists
            cursor.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
            if not cursor.fetchone():
                conn.close()
                return (False, f"Customer {customer_id} not found")
            
            # Get all tickets for customer
            cursor.execute(
                "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
                (customer_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            tickets = [dict(row) for row in rows]
            
            return (True, {
                "customer_id": customer_id,
                "tickets": tickets,
                "count": len(tickets)
            })
        
        else:
            return (False, f"Unknown tool: {name}")
    
    except Exception as e:
        return (False, f"Error executing tool {name}: {str(e)}")


# ======================
#   FastAPI Application
# ======================

app = FastAPI(title="MCP Customer Service Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol messages"""
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")
    
    # Handle initialize
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "customer-service-mcp",
                    "version": "1.0.0"
                }
            }
        })
    
    # Handle tools/list
    elif method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        })
    
    # Handle tools/call
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": "Tool name is required"
                }
            })
        
        success, result = handle_tool_call(tool_name, arguments)
        
        if success:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}]
                }
            })
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": result if isinstance(result, str) else "Tool execution failed"
                }
            })
    
    # Unknown method
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        })


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check if database exists and is accessible
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "database_path": str(DB_PATH)
    }


if __name__ == "__main__":
    print("="*80)
    print("MCP HTTP Server for Customer Service System")
    print("="*80)
    print(f"Database: {DB_PATH}")
    print(f"Server: http://localhost:8001")
    print(f"Health: http://localhost:8001/health")
    print(f"MCP Endpoint: http://localhost:8001/mcp")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)