# extras/streamlit_app.py
import sys
from pathlib import Path
import asyncio
import streamlit as st

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

agents_dir = project_root / "agents"
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from agents.router_agent import RouterAgent

# We will keep a single RouterAgent instance in Streamlit session
if "router" not in st.session_state:
    st.session_state.router = RouterAgent()

if "history" not in st.session_state:
    st.session_state.history = []  # list of (role, text)


st.set_page_config(page_title="Multi-Agent Customer Support", page_icon="🤖")
st.title("🤖 Multi-Agent Customer Support (MCP + A2A)")

st.write(
    "Ask a question about your account, billing, tickets, or upgrades. "
    "Behind the scenes: Router Agent → Support Agent (LLM) → Data Agent (MCP) → DB."
)

# Chat UI
for role, text in st.session_state.history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(text)

user_input = st.chat_input("Type your question...")

if user_input:
    # Show user message in chat
    st.session_state.history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call router (async)
    async def run_router_query(query: str) -> str:
        result = await st.session_state.router.process_query(query, customer_id=1)
        return result.get("response", "No response generated")

    with st.chat_message("assistant"):
        with st.spinner("Thinking with multi-agent magic..."):
            answer = asyncio.run(run_router_query(user_input))

        st.markdown(answer)
        st.session_state.history.append(("assistant", answer))
