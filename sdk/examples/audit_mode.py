"""
Audit Mode Example

Shows how to use audit mode to log violations without blocking execution.
Perfect for rolling out AgentSudo to production systems.
"""

from agentsudo import Agent, sudo

@sudo(scope="write:database", on_deny="log")
def update_record(record_id: str):
    """Update database record - logs violations but doesn't block."""
    print(f"✏️  Updating record {record_id}")
    return {"success": True}

@sudo(scope="delete:database", on_deny="log")
def delete_record(record_id: str):
    """Delete database record - logs violations but doesn't block."""
    print(f"🗑️  Deleting record {record_id}")
    return {"success": True}

def main():
    print("=" * 60)
    print("AgentSudo - Audit Mode Example")
    print("=" * 60)
    print("\nAudit mode logs violations but ALLOWS execution.")
    print("Perfect for testing in production without breaking things.\n")
    
    # Agent with only read permissions
    readonly_agent = Agent(
        name="ReadOnlyBot",
        scopes=["read:database"]
    )
    
    print("--- ReadOnly Agent attempting write operations ---")
    with readonly_agent.start_session():
        # These will log WARNING but still execute
        update_record("record_123")
        delete_record("record_456")
    
    print("\n✅ All operations completed (violations logged)")
    print("Check logs for audit trail of unauthorized actions.")

if __name__ == "__main__":
    main()
