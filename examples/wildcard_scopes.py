"""
Wildcard Scopes Example

Demonstrates how to use wildcard patterns for flexible permissions.
"""

from agentsudo import Agent, sudo

@sudo(scope="read:users")
def read_users():
    print("📖 Reading users")

@sudo(scope="read:orders")
def read_orders():
    print("📖 Reading orders")

@sudo(scope="write:users")
def write_users():
    print("✏️  Writing users")

@sudo(scope="write:orders")
def write_orders():
    print("✏️  Writing orders")

def main():
    print("=" * 60)
    print("AgentSudo - Wildcard Scopes Example")
    print("=" * 60)
    
    # Agent with wildcard read permissions
    readonly_agent = Agent(
        name="ReadOnlyBot",
        scopes=["read:*"]  # Matches read:users, read:orders, etc.
    )
    
    print("\n--- ReadOnly Agent (read:*) ---")
    with readonly_agent.start_session():
        read_users()   # ✅ Matches read:*
        read_orders()  # ✅ Matches read:*
        
        try:
            write_users()  # ❌ Doesn't match read:*
        except Exception as e:
            print(f"❌ Blocked: {type(e).__name__}")
    
    # Agent with specific wildcard
    orders_agent = Agent(
        name="OrdersBot",
        scopes=["read:orders*", "write:orders*"]  # Matches orders, orders_archive, etc.
    )
    
    print("\n--- Orders Agent (read:orders*, write:orders*) ---")
    with orders_agent.start_session():
        read_orders()   # ✅ Matches read:orders*
        write_orders()  # ✅ Matches write:orders*
        
        try:
            read_users()  # ❌ Doesn't match orders*
        except Exception as e:
            print(f"❌ Blocked: {type(e).__name__}")
    
    # God mode agent
    admin_agent = Agent(
        name="AdminBot",
        scopes=["*"]  # Matches everything
    )
    
    print("\n--- Admin Agent (*) ---")
    with admin_agent.start_session():
        read_users()   # ✅ Matches *
        read_orders()  # ✅ Matches *
        write_users()  # ✅ Matches *
        write_orders() # ✅ Matches *

if __name__ == "__main__":
    main()
