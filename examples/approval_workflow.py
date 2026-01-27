"""
Approval Workflow Example

Demonstrates human-in-the-loop approval for high-risk actions.
"""

from agentsudo import Agent, sudo

# Simulated approval system
approval_responses = {
    "delete:customer": False,  # Deny by default
    "refund:large": True,      # Auto-approve for demo
}

def approval_callback(agent, scope, context):
    """
    Simulates a human approval workflow.
    
    In production, this would:
    - Send a Slack/Teams message to a manager
    - Wait for approval response
    - Return True/False based on response
    """
    print(f"\n📱 [Approval System] Request from {agent.name}")
    print(f"   Scope: {scope}")
    print(f"   Function: {context['function']}")
    
    # Simulate approval check
    approved = approval_responses.get(scope, False)
    
    if approved:
        print(f"   ✅ APPROVED by manager")
    else:
        print(f"   ❌ DENIED by manager")
    
    return approved

@sudo(scope="delete:customer", on_deny=approval_callback)
def delete_customer(customer_id: str):
    """Delete a customer - requires approval."""
    print(f"🗑️  Deleting customer {customer_id}")
    return {"success": True}

@sudo(scope="refund:large", on_deny=approval_callback)
def issue_large_refund(order_id: str, amount: float):
    """Issue a large refund - requires approval."""
    print(f"💰 Issuing ${amount} refund for order {order_id}")
    return {"success": True}

def main():
    print("=" * 60)
    print("AgentSudo - Approval Workflow Example")
    print("=" * 60)
    
    # Agent without dangerous permissions
    support_agent = Agent(
        name="SupportBot",
        scopes=["read:customers", "write:tickets"]
    )
    
    print("\n--- Support Agent attempting high-risk actions ---")
    
    with support_agent.start_session():
        # Try to delete customer (will be denied)
        try:
            delete_customer("cust_123")
        except Exception as e:
            print(f"\n❌ Action blocked: {type(e).__name__}")
        
        # Try to issue large refund (will be approved for demo)
        try:
            issue_large_refund("order_456", 5000.00)
        except Exception as e:
            print(f"\n❌ Action blocked: {type(e).__name__}")

if __name__ == "__main__":
    main()
