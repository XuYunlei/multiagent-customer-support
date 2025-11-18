import asyncio
from typing import Any, Dict, Optional

from .data_agent import CustomerDataAgent
from .support_agent import SupportAgent


class RouterAgent:
    """
    Advanced Router Agent (LangGraph-style)
    
    Responsibilities:
    - Maintain a shared state object
    - Call SupportAgent for reasoning
    - Call CustomerDataAgent for database lookups
    - Decide next action based on SupportAgent output
    - Loop until final response is ready
    - Produce verbose logs for debugging & demonstration
    """

    def __init__(self):
        self.data_agent = CustomerDataAgent()
        self.support_agent = SupportAgent()


    # -----------------------------
    # Logging helper
    # -----------------------------
    def log(self, msg: str):
        print(f"[Router] {msg}")


    # -----------------------------
    # INITIAL STATE CREATION
    # -----------------------------
    def init_state(self, query: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a fresh state object for a new user query.
        """
        return {
            "query": query,
            "customer_id": customer_id,  # which customer this query is about
            "customer": None,            # customer record
            "tickets": None,             # ticket history
            "support_result": None,
            "created_ticket": None,
            "final_response": None,
        }


    # -----------------------------
    # Define Node
    # -----------------------------
    async def support_reasoning_node(self, state: Dict[str, Any]) -> str:
        """
        Node 1: Call the Support Agent to interpret the query or update.
        Returns:
            - "request_data"
            - "create_ticket"
            - "respond"
        """

        self.log("Calling Support Agent for reasoning...")

        # Call Support Agent
        result = await self.support_agent.process(
            query=state["query"],
            customer=state["customer"],
            tickets=state["tickets"],
        )

        # Save support result
        state["support_result"] = result

        # Log what Support Agent decided
        self.log(f"Support Agent result: {result}")

        action = result.get("action")

        # Return decision so Router knows next node
        return action

    async def data_fetch_node(self, state: Dict[str, Any]):
        """
        Node 2: Fetch customer and ticket data from the Data Agent (MCP).
        For now, if customer_id is not provided, default to 1.
        """

        self.log("Fetching customer data from Data Agent...")

        customer_id = state.get("customer_id") or 1
        self.log(f"Using customer_id={customer_id}")

        # Get core customer record
        customer = await self.data_agent.get_customer(customer_id)

        # Get customer history (tickets)
        history = await self.data_agent.get_customer_history(customer_id)

        tickets = history.get("tickets", [])

        state["customer"] = customer
        state["tickets"] = tickets

        self.log(
            f"Loaded customer: {customer.get('name')} (id={customer.get('id')}), "
            f"{len(tickets)} ticket(s) found."
        )

    async def ticket_creation_node(self, state: Dict[str, Any]):
        """
        Node 3: Create a support ticket via Data Agent, based on SupportAgent's recommendation.
        """

        support_result = state.get("support_result") or {}
        ticket_info = (support_result.get("ticket") or {}) if isinstance(support_result, dict) else {}

        # Fall back to query text if issue not specified
        issue = ticket_info.get("issue") or state.get("query") or "Customer issue"
        priority = ticket_info.get("priority") or "medium"

        customer = state.get("customer")
        customer_id = None

        if isinstance(customer, dict):
            customer_id = customer.get("id")

        if customer_id is None:
            # Fall back to state-level id or default
            customer_id = state.get("customer_id") or 1

        self.log(
            f"Creating ticket for customer_id={customer_id}, "
            f"priority={priority}, issue={issue!r}"
        )

        ticket = await self.data_agent.create_ticket(
            customer_id=customer_id,
            issue=issue,
            priority=priority,
        )

        state["created_ticket"] = ticket
        self.log(f"Ticket created with id={ticket.get('id')}, status={ticket.get('status')}.")

    async def finalize_node(self, state: Dict[str, Any]):
        """
        Node 4: Build the final human-facing response string.
        Combines SupportAgent text + ticket info if any.
        """

        self.log("Finalizing response...")

        support_result = state.get("support_result") or {}
        base_response = (
            support_result.get("response_text")
            if isinstance(support_result, dict)
            else None
        )

        ticket = state.get("created_ticket")

        if ticket:
            # If SupportAgent didn't provide a response, create a generic one
            if not base_response:
                base_response = (
                    "I've created a support ticket to help resolve your issue."
                )

            extra = (
                f"\n\nTicket details:\n"
                f"- ID: {ticket.get('id')}\n"
                f"- Status: {ticket.get('status')}\n"
                f"- Priority: {ticket.get('priority')}"
            )
            final = base_response + extra
            state["final_response"] = final
            self.log("Final response includes ticket details.")
            return

        if base_response:
            state["final_response"] = base_response
            self.log("Final response taken directly from Support Agent.")
            return

        # Fallback
        state["final_response"] = (
            "I'm sorry, I wasn't able to generate a detailed response for your request."
        )
        self.log("Final response fell back to generic message.")


    # -----------------------------
    # EXECUTION LOOP (skeleton)
    # -----------------------------
    async def execute(self, query: str, customer_id: Optional[int] = 1) -> str:
        """
        Main orchestration function.
        Runs the 'graph' until final_response is produced.
        """

        # Initialize state
        state = self.init_state(query, customer_id=customer_id)

        self.log(f"Received query: {query} (customer_id={customer_id})")

        # Start data agent session (spawns MCP server)
        await self.data_agent.start()

        steps = 0
        max_steps = 5  # safety to avoid infinite loops

        try:
            while steps < max_steps:
                steps += 1
                self.log(f"--- Routing step {steps} ---")

                # 1) Ask Support Agent what to do
                action = await self.support_reasoning_node(state)
                self.log(f"Router received action='{action}' from Support Agent")

                if action == "request_data":
                    # 2) Fetch data, then loop back to Support Agent
                    await self.data_fetch_node(state)
                    continue

                elif action == "create_ticket":
                    # Ensure we have customer context before ticket
                    if state.get("customer") is None:
                        await self.data_fetch_node(state)

                    await self.ticket_creation_node(state)
                    await self.finalize_node(state)
                    break

                elif action == "respond":
                    await self.finalize_node(state)
                    break

                else:
                    self.log(
                        f"Unknown or missing action '{action}', "
                        "finalizing with current support_result."
                    )
                    await self.finalize_node(state)
                    break

            if steps >= max_steps:
                self.log("Exceeded max routing steps; finalizing to avoid infinite loop.")
                await self.finalize_node(state)

            return state.get("final_response", "No response produced by Router.")

        finally:
            await self.data_agent.stop()


# -----------------------------
# Standalone test for skeleton
# -----------------------------
async def _test_router():
    router = RouterAgent()
    out = await router.execute("Hi, what's the status of my account?", customer_id=1)
    print("\n=== ROUTER OUTPUT ===")
    print(out)


if __name__ == "__main__":
    asyncio.run(_test_router())
