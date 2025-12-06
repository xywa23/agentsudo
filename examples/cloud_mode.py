"""
Example: Cloud Mode - Send events to AgentSudo Dashboard

This example shows how to connect your SDK to the AgentSudo cloud dashboard
for real-time monitoring and analytics.

Setup:
1. Create a project in the AgentSudo dashboard
2. Copy your project's API key
3. Run this script with your API key
"""

from agentsudo import Agent, sudo, configure_cloud

# Configure cloud telemetry (get API key from dashboard)
# Replace with your actual API key from https://agentsudo.vercel.app/dashboard
configure_cloud(api_key="YOUR_API_KEY_HERE")

# Create an agent with specific scopes
support_bot = Agent(
    name="SupportBot",
    scopes=["read:customers", "read:orders", "write:tickets"]
)

# Define protected functions
@sudo(scope="read:customers")
def get_customer(customer_id: str):
    """Fetch customer details - requires read:customers scope"""
    return {"id": customer_id, "name": "John Doe", "email": "john@example.com"}

@sudo(scope="read:orders")
def get_orders(customer_id: str):
    """Fetch customer orders - requires read:orders scope"""
    return [{"id": "ORD-001", "total": 99.99}, {"id": "ORD-002", "total": 149.99}]

@sudo(scope="write:refunds")
def process_refund(order_id: str, amount: float):
    """Process a refund - requires write:refunds scope (agent doesn't have this!)"""
    return {"refund_id": "REF-001", "amount": amount}

# Run the agent
if __name__ == "__main__":
    print("🚀 Starting SupportBot with cloud telemetry...\n")
    
    with support_bot.start_session():
        # These will succeed and appear in dashboard as "Allowed"
        print("✅ Getting customer...")
        customer = get_customer("CUST-123")
        print(f"   Customer: {customer['name']}\n")
        
        print("✅ Getting orders...")
        orders = get_orders("CUST-123")
        print(f"   Found {len(orders)} orders\n")
        
        # This will fail and appear in dashboard as "Denied"
        print("❌ Attempting refund (should fail)...")
        try:
            process_refund("ORD-001", 50.00)
        except PermissionError as e:
            print(f"   Blocked: {e}\n")
    
    print("✨ Check your dashboard to see the events!")
    print("   https://agentsudo.vercel.app/dashboard")
