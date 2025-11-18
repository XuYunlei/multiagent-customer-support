from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError  # pip install fastmcp


# =========================
#  Database setup & helpers
# =========================

DB_PATH = Path(__file__).with_name("support.db")


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection.

    We set row_factory so we can get rows as dict-like objects later.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Create tables if they don't exist and insert some sample data."""

    conn = get_connection()
    cur = conn.cursor()

    # Create customers table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            status      TEXT CHECK(status IN ('active', 'disabled')) NOT NULL DEFAULT 'active',
            created_at  TEXT,
            updated_at  TEXT
        )
        """
    )

    # Create tickets table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            issue       TEXT NOT NULL,
            status      TEXT CHECK(status IN ('open', 'in_progress', 'resolved')) NOT NULL DEFAULT 'open',
            priority    TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) NOT NULL DEFAULT 'medium',
            created_at  TEXT,
            updated_at  TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """
    )

    # Seed sample data only if DB is empty
    cur.execute("SELECT COUNT(*) FROM customers")
    (customer_count,) = cur.fetchone()

    if customer_count == 0:
        now = datetime.utcnow().isoformat()

        sample_customers = [
            ("John Doe", "john.doe@example.com", "+1-555-0101", "active", now, now),
            ("Jane Smith", "jane.smith@example.com", "+1-555-0102", "active", now, now),
            ("Bob Johnson", "bob.johnson@example.com", "+1-555-0103", "disabled", now, now),
            ("Alice Williams", "alice.w@techcorp.com", "+1-555-0104", "active", now, now),
            ("Charlie Brown", "charlie.brown@email.com", "+1-555-0105", "active", now, now),
        ]

        cur.executemany(
            """
            INSERT INTO customers (name, email, phone, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_customers,
        )

        # Some sample tickets
        sample_tickets = [
            (1, "Unable to login", "open", "high", now, now),
            (1, "Requesting plan upgrade", "in_progress", "medium", now, now),
            (2, "Incorrect billing amount", "open", "urgent", now, now),
            (4, "App crashes on startup", "resolved", "high", now, now),
        ]

        cur.executemany(
            """
            INSERT INTO tickets (customer_id, issue, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_tickets,
        )

    conn.commit()
    conn.close()


# ================
#  Data structures
# ================

@dataclass
class Customer:
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class Ticket:
    id: int
    customer_id: int
    issue: str
    status: str
    priority: str
    created_at: Optional[str]
    updated_at: Optional[str]


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a sqlite3.Row into a plain dictionary."""
    return {k: row[k] for k in row.keys()}


# =======================
#  MCP server definition
# =======================

mcp = FastMCP("Customer Support MCP Server")


@mcp.tool
def get_customer(customer_id: int) -> Dict[str, Any]:
    """
    Get a single customer by ID.

    Args:
        customer_id: The customer's numeric ID.
    Returns:
        A JSON-serializable dict with customer fields.

    Raises:
        ToolError if the customer does not exist.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise ToolError(f"Customer with id={customer_id} not found")

    return row_to_dict(row)


@mcp.tool
def list_customers(
    status: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    List customers, optionally filtered by status.

    Args:
        status: 'active' or 'disabled' (optional)
        limit: maximum number of customers to return
    """
    conn = get_connection()
    cur = conn.cursor()

    if status:
        cur.execute(
            """
            SELECT * FROM customers
            WHERE status = ?
            ORDER BY id
            LIMIT ?
            """,
            (status, limit),
        )
    else:
        cur.execute(
            """
            SELECT * FROM customers
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        )

    rows = cur.fetchall()
    conn.close()

    return [row_to_dict(r) for r in rows]


@mcp.tool
def update_customer(customer_id: int, data_json: str) -> Dict[str, Any]:
    """
    Update fields on a customer.

    Args:
        customer_id: ID of the customer to update
        data_json: JSON string with fields to update, e.g.
                   '{"email": "new@email.com", "status": "active"}'
    Returns:
        Updated customer record as dict.
    """
    try:
        data: Dict[str, Any] = json.loads(data_json)
    except json.JSONDecodeError as e:
        raise ToolError(f"Invalid JSON for data_json: {e}")

    if not data:
        raise ToolError("No fields provided to update")

    allowed_fields = {"name", "email", "phone", "status"}
    invalid = set(data.keys()) - allowed_fields
    if invalid:
        raise ToolError(f"Invalid fields for update: {', '.join(invalid)}")

    set_clauses = []
    values: List[Any] = []
    for field, value in data.items():
        set_clauses.append(f"{field} = ?")
        values.append(value)

    # Always update updated_at
    set_clauses.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())

    values.append(customer_id)

    conn = get_connection()
    cur = conn.cursor()

    # Check existence first
    cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
    if cur.fetchone() is None:
        conn.close()
        raise ToolError(f"Customer with id={customer_id} not found")

    sql = f"UPDATE customers SET {', '.join(set_clauses)} WHERE id = ?"
    cur.execute(sql, tuple(values))
    conn.commit()

    # Return updated record
    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()

    return row_to_dict(row)


@mcp.tool
def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium",
) -> Dict[str, Any]:
    """
    Create a support ticket for a given customer.

    Args:
        customer_id: ID of the customer
        issue: Short description of the issue
        priority: 'low', 'medium', 'high', or 'urgent'
    """
    if priority not in {"low", "medium", "high", "urgent"}:
        raise ToolError("priority must be one of: low, medium, high, urgent")

    now = datetime.utcnow().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    # Ensure customer exists
    cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
    if cur.fetchone() is None:
        conn.close()
        raise ToolError(f"Customer with id={customer_id} not found")

    cur.execute(
        """
        INSERT INTO tickets (customer_id, issue, status, priority, created_at, updated_at)
        VALUES (?, ?, 'open', ?, ?, ?)
        """,
        (customer_id, issue, priority, now, now),
    )
    ticket_id = cur.lastrowid
    conn.commit()

    cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cur.fetchone()
    conn.close()

    return row_to_dict(row)


@mcp.tool
def get_customer_history(customer_id: int) -> Dict[str, Any]:
    """
    Get a customer plus all their tickets.

    Returns:
        {
          "customer": {...},
          "tickets": [{...}, ...]
        }
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer_row = cur.fetchone()
    if customer_row is None:
        conn.close()
        raise ToolError(f"Customer with id={customer_id} not found")

    cur.execute(
        """
        SELECT * FROM tickets
        WHERE customer_id = ?
        ORDER BY created_at DESC
        """,
        (customer_id,),
    )
    ticket_rows = cur.fetchall()
    conn.close()

    return {
        "customer": row_to_dict(customer_row),
        "tickets": [row_to_dict(r) for r in ticket_rows],
    }


# ===========
#  Entry point
# ===========

if __name__ == "__main__":
    # Make sure database and tables exist before starting MCP server
    init_database()

    # Start MCP server.
    # Default is stdio (good for local MCP clients). For HTTP (e.g. Inspector), you can do:
    #   mcp.run(transport="http", host="127.0.0.1", port=8000)
    mcp.run()
