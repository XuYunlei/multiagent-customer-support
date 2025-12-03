# mcp/mcp_tools.py
"""
MCP Tools for Google ADK Agents
Wraps MCP HTTP client calls into tool functions that can be used by LLM agents
"""
from mcp_client import MCPHTTPClient
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize MCP client
mcp_client = MCPHTTPClient("http://localhost:8001")

# Initialize the connection
try:
    mcp_client.initialize()
    logger.info("MCP client initialized successfully")
except Exception as e:
    logger.warning(f"MCP initialization failed: {e}. Tools may not work properly.")


# ==================
# Tool Functions
# ==================

def get_customer(customer_id: int) -> Dict[str, Any]:
    """
    Get customer information by ID.
    
    This tool retrieves detailed information about a specific customer from the database.
    
    Args:
        customer_id: The customer's numeric ID (e.g., 1, 12345)
        
    Returns:
        Dictionary with customer information:
        - id: Customer ID
        - name: Customer name
        - email: Email address
        - phone: Phone number
        - status: 'active' or 'disabled'
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        
    Example:
        >>> get_customer(1)
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', ...}
    """
    result = mcp_client.get_customer(customer_id)
    if result:
        return result
    else:
        return {"error": f"Customer {customer_id} not found"}


def list_customers(status: str = "active", limit: int = 100) -> List[Dict[str, Any]]:
    """
    List customers filtered by status.
    
    This tool retrieves a list of customers based on their status.
    
    Args:
        status: Filter by status - 'active' or 'disabled' (default: 'active')
        limit: Maximum number of customers to return (default: 100)
        
    Returns:
        List of customer dictionaries, each containing:
        - id, name, email, phone, status, created_at, updated_at
        
    Example:
        >>> list_customers(status='active', limit=5)
        [{'id': 1, 'name': 'John Doe', ...}, {'id': 2, 'name': 'Jane Smith', ...}]
    """
    customers = mcp_client.list_customers(status, limit)
    return customers if customers else []


def update_customer(
    customer_id: int,
    email: str = None,
    phone: str = None,
    name: str = None,
    status: str = None
) -> Dict[str, Any]:
    """
    Update customer information.
    
    This tool updates one or more fields for a specific customer.
    Only provide the fields you want to update.
    
    Args:
        customer_id: The customer ID to update
        email: New email address (optional)
        phone: New phone number (optional)
        name: New name (optional)
        status: New status - 'active' or 'disabled' (optional)
        
    Returns:
        Dictionary with success status and message
        
    Example:
        >>> update_customer(1, email='newemail@example.com')
        {'success': True, 'message': 'Customer 1 updated'}
    """
    # Build data dictionary with only provided fields
    data = {}
    if email is not None:
        data['email'] = email
    if phone is not None:
        data['phone'] = phone
    if name is not None:
        data['name'] = name
    if status is not None:
        data['status'] = status
    
    if not data:
        return {"success": False, "error": "No fields provided to update"}
    
    success = mcp_client.update_customer(customer_id, data)
    
    if success:
        return {
            "success": True,
            "message": f"Customer {customer_id} updated successfully",
            "updated_fields": list(data.keys())
        }
    else:
        return {
            "success": False,
            "error": f"Failed to update customer {customer_id}"
        }


def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Create a new support ticket for a customer.
    
    This tool creates a support ticket to track customer issues.
    The ticket starts with status 'open'.
    
    Args:
        customer_id: ID of the customer who has the issue
        issue: Description of the problem or request
        priority: Priority level - 'low', 'medium', or 'high' (default: 'medium')
        
    Returns:
        Dictionary with created ticket information:
        - ticket_id: The newly created ticket ID
        - customer_id: Customer ID
        - issue: Issue description
        - status: Always 'open' for new tickets
        - priority: Priority level
        
    Example:
        >>> create_ticket(1, "Cannot login to account", "high")
        {'ticket_id': 42, 'customer_id': 1, 'issue': '...', 'status': 'open', 'priority': 'high'}
    """
    result = mcp_client.create_ticket(customer_id, issue, priority)
    
    if result:
        return result
    else:
        return {
            "error": f"Failed to create ticket for customer {customer_id}",
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority
        }


def get_customer_history(customer_id: int) -> Dict[str, Any]:
    """
    Get all support tickets for a specific customer.
    
    This tool retrieves the complete ticket history for a customer,
    showing all their past and current support interactions.
    
    Args:
        customer_id: The customer ID to get history for
        
    Returns:
        Dictionary containing:
        - customer_id: The customer ID
        - tickets: List of all tickets for this customer
        - count: Total number of tickets
        
    Example:
        >>> get_customer_history(1)
        {
            'customer_id': 1,
            'tickets': [
                {'id': 1, 'issue': 'Login problem', 'status': 'resolved', ...},
                {'id': 2, 'issue': 'Billing question', 'status': 'open', ...}
            ],
            'count': 2
        }
    """
    tickets = mcp_client.get_customer_history(customer_id)
    
    return {
        "customer_id": customer_id,
        "tickets": tickets if tickets else [],
        "count": len(tickets) if tickets else 0
    }


# ======================
# Export Tools
# ======================

# List of all available tools for Google ADK agents
ALL_TOOLS = [
    get_customer,
    list_customers,
    update_customer,
    create_ticket,
    get_customer_history,
]

# Tool descriptions for documentation
TOOL_DESCRIPTIONS = {
    "get_customer": "Retrieve detailed information about a specific customer by ID",
    "list_customers": "List customers filtered by their status (active/disabled)",
    "update_customer": "Update customer information (email, phone, name, status)",
    "create_ticket": "Create a new support ticket for customer issues",
    "get_customer_history": "Get complete ticket history for a customer",
}


def get_tool_by_name(tool_name: str):
    """
    Get a tool function by its name.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool function or None if not found
    """
    tool_map = {
        "get_customer": get_customer,
        "list_customers": list_customers,
        "update_customer": update_customer,
        "create_ticket": create_ticket,
        "get_customer_history": get_customer_history,
    }
    return tool_map.get(tool_name)


if __name__ == "__main__":
    # Test the tools
    print("Testing MCP Tools...")
    print("\n1. Listing customers:")
    customers = list_customers(status="active", limit=3)
    print(f"Found {len(customers)} customers")
    
    if customers:
        print("\n2. Getting first customer details:")
        customer = get_customer(customers[0]["id"])
        print(f"Customer: {customer.get('name')}")
        
        print("\n3. Getting customer history:")
        history = get_customer_history(customers[0]["id"])
        print(f"Customer has {history['count']} tickets")
    
    print("\n✅ MCP Tools test complete!")
