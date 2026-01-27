"""
AgentSudo + FastAPI Integration Example

This example shows how to protect FastAPI endpoints with AgentSudo.

Requirements:
    pip install agentsudo fastapi uvicorn

Run:
    uvicorn fastapi_example:app --reload
    
Test:
    # Without agent header (blocked)
    curl http://localhost:8000/weather/tokyo
    
    # With reader agent (allowed for weather, blocked for refunds)
    curl -H "X-Agent-ID: reader-001" http://localhost:8000/weather/tokyo
    curl -H "X-Agent-ID: reader-001" -X POST http://localhost:8000/refunds
    
    # With admin agent (allowed for everything)
    curl -H "X-Agent-ID: admin-001" -X POST http://localhost:8000/refunds
"""

from fastapi import FastAPI, Depends, Request, HTTPException
from pydantic import BaseModel

from agentsudo import Agent
from agentsudo.adapters.fastapi import (
    AgentSudoMiddleware,
    require_scope,
    register_agent,
    get_current_agent_dependency,
    AgentContext,
    sudo_endpoint,
)

# =============================================================================
# Setup
# =============================================================================

app = FastAPI(
    title="AgentSudo FastAPI Demo",
    description="Demonstrating AI agent permission control with FastAPI"
)

# Register some agents (in production, you'd load from database)
reader_agent = Agent(name="ReaderBot", scopes=["read:weather", "read:data"])
writer_agent = Agent(name="WriterBot", scopes=["read:*", "write:email"])
admin_agent = Agent(name="AdminBot", scopes=["read:*", "write:*"])

register_agent(reader_agent, "reader-001")
register_agent(writer_agent, "writer-001")
register_agent(admin_agent, "admin-001")

# Add middleware to extract agent from headers
app.add_middleware(
    AgentSudoMiddleware,
    agent_header="X-Agent-ID",
    on_missing_agent="error"  # Require agent for all requests
)


# =============================================================================
# Request/Response Models
# =============================================================================

class RefundRequest(BaseModel):
    order_id: str
    amount: float
    reason: str = "Customer request"


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


# =============================================================================
# Option 1: Using Depends(require_scope(...))
# =============================================================================

@app.get("/weather/{city}")
async def get_weather(
    city: str,
    agent: Agent = Depends(require_scope("read:weather"))
):
    """Get weather for a city. Requires read:weather scope."""
    return {
        "city": city,
        "weather": "Sunny",
        "temperature": 72,
        "agent": agent.name
    }


@app.post("/refunds")
async def process_refund(
    refund: RefundRequest,
    agent: Agent = Depends(require_scope("write:refunds"))
):
    """Process a refund. Requires write:refunds scope."""
    return {
        "status": "processed",
        "order_id": refund.order_id,
        "amount": refund.amount,
        "agent": agent.name
    }


@app.post("/emails")
async def send_email(
    email: EmailRequest,
    agent: Agent = Depends(require_scope("write:email"))
):
    """Send an email. Requires write:email scope."""
    return {
        "status": "sent",
        "to": email.to,
        "subject": email.subject,
        "agent": agent.name
    }


# =============================================================================
# Option 2: Using @sudo_endpoint decorator
# =============================================================================

@app.delete("/data/{record_id}")
@sudo_endpoint(scope="delete:data")
async def delete_record(record_id: str, request: Request):
    """Delete a record. Requires delete:data scope."""
    return {
        "status": "deleted",
        "record_id": record_id
    }


# =============================================================================
# Option 3: Using AgentContext for fine-grained control
# =============================================================================

@app.post("/multi-action")
async def multi_action(request: Request):
    """
    Endpoint that requires multiple scopes for different operations.
    Uses AgentContext for fine-grained permission checks.
    """
    ctx = AgentContext(request)
    results = {}
    
    # Check read permission
    with ctx.require("read:data"):
        results["data"] = {"fetched": True, "count": 42}
    
    # Check write permission
    with ctx.require("write:logs"):
        results["logged"] = True
    
    return {
        "status": "success",
        "results": results,
        "agent": ctx.agent.name if ctx.agent else None
    }


# =============================================================================
# Option 4: Manual scope checking
# =============================================================================

@app.get("/whoami")
async def whoami(agent: Agent = Depends(get_current_agent_dependency())):
    """Get current agent info. No scope required."""
    if not agent:
        raise HTTPException(status_code=401, detail="No agent context")
    
    return {
        "name": agent.name,
        "id": agent.id,
        "scopes": list(agent.scopes),
        "role": agent.role
    }


@app.get("/data")
async def get_data(request: Request):
    """Manual scope checking example."""
    ctx = AgentContext(request)
    
    if not ctx.agent:
        raise HTTPException(status_code=401, detail="No agent context")
    
    # Manual check
    if ctx.has_scope("read:sensitive"):
        return {"data": "sensitive information", "level": "full"}
    elif ctx.has_scope("read:data"):
        return {"data": "public information", "level": "limited"}
    else:
        raise HTTPException(status_code=403, detail="No read permissions")


# =============================================================================
# Health check (no auth required - for demo purposes)
# =============================================================================

# Override middleware for health check
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy"}


# =============================================================================
# Demo script
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("AgentSudo + FastAPI Demo Server")
    print("=" * 60)
    print("\nRegistered agents:")
    print(f"  - reader-001: {reader_agent.scopes}")
    print(f"  - writer-001: {writer_agent.scopes}")
    print(f"  - admin-001:  {admin_agent.scopes}")
    print("\nTest commands:")
    print('  curl -H "X-Agent-ID: reader-001" http://localhost:8000/weather/tokyo')
    print('  curl -H "X-Agent-ID: admin-001" -X POST -H "Content-Type: application/json" \\')
    print('       -d \'{"order_id": "123", "amount": 50.0}\' http://localhost:8000/refunds')
    print("\n" + "=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
