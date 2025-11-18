# Multi-Agent Customer Support System  
### MCP-Powered • OpenAI GPT-4o-mini • LangGraph-Style Routing • SQLite-Grounded

This project implements a fully functional **multi-agent customer support platform** built for the Applied Generative AI course at the University of Chicago.  
It combines **LLM reasoning**, **database-backed tools**, **MCP**, **LangGraph-style orchestration**, and **multimodal interfaces** (text + voice).

---

## Project Overview

This system simulates an intelligent customer support workflow. Three core agents collaborate to:

- Understand user intent  
- Retrieve customer details  
- Resolve multi-step queries  
- Create or update support tickets  
- Provide helpful natural-language responses  
- Interact through CLI, Streamlit Web UI, or speech-to-speech interface  

The pipeline is **grounded in a real SQLite database** via an MCP Server (FastMCP), and orchestrated by a **custom Router Agent** inspired by LangGraph.

---

## Project Structure

```bash
MULTIAGENT-CUSTOMER-SUPPORT/
├── agents/                 # Multi-agent logic
│   ├── data_agent.py       # MCP client
│   ├── router_agent.py     # LangGraph-style orchestrator
│   └── support_agent.py    # GPT-4o-mini reasoning
│
├── demo/                   # Homework test cases
│   └── run_demo.py
│
├── extras/                 # Optional UI components
│   ├── chat_cli.py         # CLI demo 
│   ├── streamlit_app.py    # Web UI
│   └── voice_chat.py       # Speech-to-speech assistant
│
├── mcp_server/ # MCP Server + SQLite grounding
│   ├── database_setup.py
│   ├── server.py
│   └── support.db # SQLite database
│
├── README.md
├── setup.py
└── .gitignore
```

---

## System Architecture

```
                 +------------------------------+
                 |        User Interfaces       |
                 |   CLI  •  Streamlit  • Voice |
                 +---------------+--------------+
                                 |
                                 v
                        +------------------+
                        |   Router Agent   |
                        |   (Controller)   |
                        +--------+---------+
                                 |
           -----------------------------------------------
          |                        |                      |
          v                        v                      v
  +---------------+      +------------------+    +--------------------+
  | Support Agent |      |   Data Agent     |    | Ticket Generation  |
  | (GPT-4o-mini) |      |  (MCP Client)    |    |   (create_ticket)  |
  +---------------+      +------------------+    +--------------------+
                                 |
                                 v
                      +-----------------------+
                      |   FastMCP Server      |
                      |   SQLite Database     |
                      +-----------------------+
```

---

## Features

### Support Agent (GPT-4o-mini)
- Intent classification  
- Multi-intent detection  
- Action planning (respond, request_data, create_ticket)  
- Structured JSON output for routing  

### Data Agent (MCP Client)
- Calls MCP server via StdioTransport  
- Exposes tool functions:
  - `get_customer`
  - `list_customers`
  - `update_customer`
  - `get_customer_history`
  - `create_ticket`

### MCP Server (FastMCP + SQLite)
- Persistent storage  
- Database-backed tool functions  
- Deterministic grounding for LLMs  

### Router Agent (LangGraph Style)
- Multi-step reasoning  
- Node-based routing  
- Condition-driven transitions  
- Final response synthesis  

### User Interfaces
- CLI chat  
- Automated HW scenario runner  
- Streamlit web UI  
- Full speech-to-speech interaction (Whisper + TTS)

---

## Installation

### 1. Clone the repo
``` python
git clone https://github.com/XuYunlei/multiagent-customer-support.git
cd multiagent-customer-support
```

### 2. Create environment
``` python
conda create -n mcp python=3.10 -y
conda activate mcp
```

### 3. Install dependencies
``` python
pip install -r requirements.txt
pip install streamlit sounddevice simpleaudio pydub
brew install ffmpeg
```

---

## How to Run

### 🔹 Test Scenarios
``` python
python demo/run_demo.py
```

### 🔹 Interactive CLI Chat
``` python
python extras/chat_cli.py
```

### 🔹 Streamlit Web App
``` python
streamlit run extras/streamlit_app.py
```

### 🔹 Speech-to-Speech Voice Assistant
``` python
python extras/voice_chat.py
```

---

## Skills Demonstrated

- Multi-Agent Systems  
- Model Context Protocol (MCP)  
- FastMCP Server Development  
- OpenAI GPT-4o-mini (LLM Reasoning)  
- OpenAI Whisper (ASR)  
- OpenAI TTS (Speech Generation)  
- Async Python (asyncio)  
- SQLite database design  
- Tool-grounded LLMs  
- LangGraph-style orchestration  
- Streamlit UI development  
- Audio processing (sounddevice, pydub)  

---

## Future Enhancements

- Multi-turn session memory  
- Dashboard for customer & ticket management  
- Integration with external APIs  
- RAG-enhanced support answers  
- Multi-user support with authentication  
- Persistent voice history  

---

## Acknowledgements  
Course: *Applied Generative AI and Multi-Modal Intelligence*  
University of Chicago, 2025  


