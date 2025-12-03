# demo/test_a2a_agents.py
import asyncio
import httpx
import json
from uuid import uuid4

async def test_agent(agent_url, query):
    """Test an A2A agent using JSON-RPC with correct message/send format"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Correct format based on error message
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
        
        print(f"\n📤 Request to {agent_url}:")
        print(f"   Query: {query}")
        print(f"   Method: message/send")
        
        try:
            response = await client.post(
                agent_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            print(f"   Status: {response.status_code}")
            
            if "error" in result:
                print(f"   ❌ Error: {result['error']['message']}")
                print(f"   Full response: {json.dumps(result, indent=2)}")
            else:
                print(f"   ✅ Success!")
                print(f"   Response: {json.dumps(result, indent=2)}")
                return result
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None

async def main():
    # Test Data Agent
    print("=" * 60)
    print("Testing Data Agent (with MCP tools)")
    print("=" * 60)
    await test_agent(
        "http://localhost:10021",
        "Get customer information for customer ID 1"
    )
    
    # Test Support Agent
    print("\n" + "=" * 60)
    print("Testing Support Agent (LLM reasoning)")
    print("=" * 60)
    await test_agent(
        "http://localhost:10022",
        "I need help with my account"
    )

if __name__ == "__main__":
    asyncio.run(main())