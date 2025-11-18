## Multi-Agent Customer Service System (A2A + MCP)

This project implements a multi-agent customer service workflow using:

* **A2A (Agent-to-Agent) communication**
* **A custom MCP server with database-backed tools**
* **Python-based agents for data retrieval and support logic**

This repository is part of my Applied Generative AI coursework and designed to be production-quality and portfolio-ready.

---

### 📘 Overview

(You will fill later after implementation.)

---

### 🧠 Architecture

**Agents**

* Router Agent
* Customer Data Agent
* Support Agent

**MCP Server Tools**

* `get_customer`
* `list_customers`
* `update_customer`
* `create_ticket`
* `get_customer_history`

---

### 🗂 Folder Structure

```
multiagent-customer-support/
│
├── README.md
│
├── mcp_server/
│   ├── server.py
│   ├── database_setup.py
│   └── README.md (optional)
│
├── agents/
│   ├── router_agent.py
│   ├── data_agent.py
│   └── support_agent.py
│
├── demo/
│   ├── run_demo.py
│   └── sample_logs.txt
│
└── notebooks/
    └── HW5_demo.ipynb

```

---

### 🚀 How to Run

**1. Install the package in development mode (recommended):**

```bash
pip install -e .
```

This installs the package so you can import `agents` from anywhere without path issues.

**2. Alternative: Set PYTHONPATH (if not using pip install):**

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**3. Run the demo:**

```bash
python demo/run_demo.py
```

**4. Run individual agents:**

```bash
# Test data agent
python -m agents.data_agent

# Test support agent
python -m agents.support_agent

# Test router agent
python -m agents.router_agent
```

---

### 🧪 Test Queries

(Will fill after coding)

---

### 🎓 What I Learned

(Will fill at the end — great for your resume)
