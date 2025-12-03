# Quick Start Script for Multi-Agent Customer Service System

echo "=================================="
echo "  Multi-Agent System Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your OPENAI_API_KEY"
    echo ""
    echo "Example:"
    echo "  echo 'OPENAI_API_KEY=sk-proj-your-key-here' > .env"
    echo ""
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Check if database exists
if [ ! -f src/support.db ]; then
    echo "⚠️  Database not found. Creating..."
    python src/database_setup.py
    echo ""
fi

echo "✅ Database ready"
echo ""

echo "📋 Starting servers..."
echo ""

# Start MCP server in background
echo "1️⃣  Starting MCP Server (port 8001)..."
python mcp/mcp_server.py > logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo "   PID: $MCP_PID"

sleep 2

# Start A2A server in background
echo "2️⃣  Starting A2A Server (ports 10020-10022)..."
python a2a_server.py > logs/a2a_server.log 2>&1 &
A2A_PID=$!
echo "   PID: $A2A_PID"

sleep 5

echo ""
echo "✅ All servers running!"
echo ""
echo "📊 Server Status:"
echo "   • MCP Server:    http://localhost:8001 (PID: $MCP_PID)"
echo "   • Router Agent:  http://localhost:10020"
echo "   • Data Agent:    http://localhost:10021"
echo "   • Support Agent: http://localhost:10022"
echo ""
echo "🚀 Running demo in 3 seconds..."
echo ""

sleep 3

# Run demo
python demo.py

echo ""
echo "=================================="
echo "          Demo Complete!"
echo "=================================="
echo ""
echo "To stop servers:"
echo "  kill $MCP_PID $A2A_PID"
echo ""
echo "Or press Ctrl+C and run:"
echo "  pkill -f 'python.*mcp_server.py'"
echo "  pkill -f 'python.*a2a_server.py'"
echo ""