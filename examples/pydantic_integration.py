"""
Pydantic Integration Example

Shows how to enforce permissions on Pydantic models.
Perfect for LangChain/LlamaIndex tool schemas.
"""

from agentsudo import Agent, PermissionDeniedError

try:
    from agentsudo.integrations import ScopedModel
except ImportError:
    print("❌ Pydantic not installed. Run: pip install pydantic")
    exit(1)

# Define scoped models
class RefundRequest(ScopedModel):
    """Refund request - requires write:refunds scope."""
    _required_scope = "write:refunds"
    
    order_id: str
    amount: float
    reason: str

class CustomerData(ScopedModel):
    """Customer data - requires read:customers scope."""
    _required_scope = "read:customers"
    
    customer_id: str
    name: str
    email: str

class AdminAction(ScopedModel):
    """Admin action - requires admin:* scope."""
    _required_scope = "admin:*"
    
    action: str
    target: str

def main():
    print("=" * 60)
    print("AgentSudo - Pydantic Integration Example")
    print("=" * 60)
    
    # Create agents
    support_agent = Agent(
        name="SupportBot",
        scopes=["read:customers", "write:refunds"]
    )
    
    readonly_agent = Agent(
        name="ReadOnlyBot",
        scopes=["read:*"]
    )
    
    admin_agent = Agent(
        name="AdminBot",
        scopes=["admin:*", "read:*", "write:*"]
    )
    
    # Scenario 1: Support agent can create refunds
    print("\n--- Support Agent creating RefundRequest ---")
    with support_agent.start_session():
        try:
            refund = RefundRequest(
                order_id="order_123",
                amount=50.00,
                reason="Product defect"
            )
            print(f"✅ Refund created: ${refund.amount}")
        except PermissionDeniedError as e:
            print(f"❌ Blocked: {e}")
    
    # Scenario 2: ReadOnly agent can read customer data
    print("\n--- ReadOnly Agent reading CustomerData ---")
    with readonly_agent.start_session():
        try:
            customer = CustomerData(
                customer_id="cust_456",
                name="Alice",
                email="alice@example.com"
            )
            print(f"✅ Customer loaded: {customer.name}")
        except PermissionDeniedError as e:
            print(f"❌ Blocked: {e}")
    
    # Scenario 3: ReadOnly agent cannot create refunds
    print("\n--- ReadOnly Agent trying to create RefundRequest ---")
    with readonly_agent.start_session():
        try:
            refund = RefundRequest(
                order_id="order_789",
                amount=100.00,
                reason="Test"
            )
            print(f"✅ Refund created: ${refund.amount}")
        except PermissionDeniedError as e:
            print(f"❌ Blocked: Agent lacks 'write:refunds' scope")
    
    # Scenario 4: Only admin can perform admin actions
    print("\n--- Admin Agent performing AdminAction ---")
    with admin_agent.start_session():
        try:
            action = AdminAction(
                action="reset_password",
                target="user_999"
            )
            print(f"✅ Admin action: {action.action}")
        except PermissionDeniedError as e:
            print(f"❌ Blocked: {e}")

if __name__ == "__main__":
    main()
