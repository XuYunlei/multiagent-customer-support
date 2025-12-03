# demo/demo.py
"""
Demo Script - Test Multi-Agent System via A2A HTTP Endpoints
Uses Google ADK agents exposed as A2A-compatible HTTP services
"""

import asyncio
import httpx
import json
import time
from uuid import uuid4
from typing import Dict, Any

# A2A Router Agent endpoint
ROUTER_AGENT_URL = "http://localhost:10020"

# Rate limiting: delay between requests to avoid quota limits
# Increased to 30 seconds to avoid hitting free tier quota limits
DELAY_BETWEEN_QUERIES = 30  # seconds - increased due to quota limits

async def send_a2a_message(agent_url: str, query: str) -> Dict[str, Any]:
    """
    Send a message to an A2A agent using JSON-RPC message/send protocol
    
    Args:
        agent_url: The agent's HTTP endpoint
        query: The user query to send
        
    Returns:
        The agent's response as a dictionary
    """
    message_id = str(uuid4())
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": query
                    }
                ]
            }
        },
        "id": 1
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                agent_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error communicating with agent: {e}")
            return {"error": str(e)}

def is_rate_limit_error(a2a_response: Dict[str, Any]) -> bool:
    """Check if the response indicates a rate limit error (429)"""
    if "error" in a2a_response:
        error = a2a_response['error']
        if isinstance(error, dict):
            error_code = error.get('code')
            error_message = error.get('message', '')
            return error_code == 429 or '429' in str(error_code) or 'RESOURCE_EXHAUSTED' in error_message
        elif isinstance(error, str):
            return '429' in error or 'RESOURCE_EXHAUSTED' in error
    return False

def extract_response_text(a2a_response: Dict[str, Any]) -> str:
    """
    Extract the text response from an A2A response structure
    
    Args:
        a2a_response: The A2A JSON-RPC response
        
    Returns:
        The text response as a string
    """
    if "error" in a2a_response:
        error = a2a_response['error']
        # Handle both dict and string error formats
        if isinstance(error, dict):
            error_msg = error.get('message', 'Unknown error')
            # Check if it's a rate limit error
            if is_rate_limit_error(a2a_response):
                return f"⚠️  Rate Limit Error (429): {error_msg}\n💡 Tip: Wait 30-60 seconds and try again, or upgrade your Google API quota."
            return f"Error: {error_msg}"
        else:
            if is_rate_limit_error(a2a_response):
                return f"⚠️  Rate Limit Error (429): {error}\n💡 Tip: Wait 30-60 seconds and try again."
            return f"Error: {error}"
    
    result = a2a_response.get("result", {})
    
    # Check for artifacts (final response)
    artifacts = result.get("artifacts", [])
    if artifacts:
        for artifact in artifacts:
            parts = artifact.get("parts", [])
            for part in parts:
                if part.get("kind") == "text":
                    return part.get("text", "")
    
    # Check history for agent messages
    history = result.get("history", [])
    for message in reversed(history):  # Start from most recent
        if message.get("role") == "agent":
            parts = message.get("parts", [])
            for part in parts:
                if part.get("kind") == "text":
                    text = part.get("text", "")
                    if text and not text.startswith("Error"):
                        return text
    
    # Check status message
    status = result.get("status", {})
    status_msg = status.get("message", {})
    if status_msg:
        parts = status_msg.get("parts", [])
        for part in parts:
            if part.get("kind") == "text":
                return part.get("text", "")
    
    return "No response text found"

async def run_demo():
    """Run demo scenarios using A2A HTTP endpoints"""
    
    test_queries = [
        "Hi, what's the status of my account?",
        "I was charged twice this month, please help!",
        "I want to upgrade my account and also fix my login issue.",
        "Show me all my tickets.",
        "Please update my email to new_email@gmail.com",
    ]

    print("\n============================")
    print(" MULTI-AGENT DEMO STARTED")
    print("============================")
    print(f"Router Agent: {ROUTER_AGENT_URL}")
    print("============================\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n====== TEST SCENARIO {i} ======")
        print(f"User Query: {query}\n")

        # Send query to router agent via A2A
        a2a_response = await send_a2a_message(ROUTER_AGENT_URL, query)
        
        # Extract response text
        response_text = extract_response_text(a2a_response)
        
        print("\n--- FINAL ANSWER ---")
        print(response_text)
        
        # Show task status if available
        result = a2a_response.get("result", {})
        status = result.get("status", {})
        if status:
            state = status.get("state", "unknown")
            print(f"\n--- TASK STATUS ---")
            print(f"State: {state}")
        
        # Check for rate limit errors
        if is_rate_limit_error(a2a_response):
            print(f"\n⚠️  429 RESOURCE_EXHAUSTED detected!")
            print(f"   Most likely cause: Free tier daily request limit (200/day)")
            print(f"   Check quotas: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
            print(f"   Look for: 'Request limit per model per day for a project in the free tier'")
            print(f"   With billing enabled, request an increase or wait for daily reset")
            print(f"   Waiting {DELAY_BETWEEN_QUERIES * 2} seconds before next query...")
            await asyncio.sleep(DELAY_BETWEEN_QUERIES * 2)  # Wait longer after rate limit
        else:
            # Normal delay between queries to avoid hitting limits
            if i < len(test_queries):  # Don't wait after last query
                print(f"\n⏳ Waiting {DELAY_BETWEEN_QUERIES} seconds before next query...")
                await asyncio.sleep(DELAY_BETWEEN_QUERIES)
        
        print("\n------------------------------")
        print(" End of Scenario")
        print("------------------------------\n")

if __name__ == "__main__":
    print("\n⚠️  Prerequisites:")
    print("   1. MCP Server must be running: python mcp_impl/mcp_server.py")
    print("   2. A2A Server must be running: python agents/a2a_server.py")
    print(f"\n⏱️  Rate Limiting: {DELAY_BETWEEN_QUERIES}s delay between queries to avoid quota limits")
    print("\nStarting demo in 2 seconds...\n")
    
    time.sleep(2)
    
    asyncio.run(run_demo())
