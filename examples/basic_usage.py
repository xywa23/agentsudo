"""
Basic Usage Example for AgentSudo

This example demonstrates the core concepts:
1. Creating agents with different permission levels
2. Protecting functions with @sudo decorator
3. Running code in agent sessions
"""

from agentsudo import Agent, sudo, PermissionDeniedError

# Define protected functions
@sudo(scope="read:users")
def get_user(user_id: str):
    """Fetch user data from database."""
    print(f"📖 Reading user {user_id}")
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}

@sudo(scope="write:users")
def update_user(user_id: str, data: dict):
    """Update user data in database."""
    print(f"✏️  Updating user {user_id} with {data}")
    return {"success": True}

@sudo(scope="delete:users")
def delete_user(user_id: str):
    """Delete a user from the database."""
    print(f"🗑️  Deleting user {user_id}")
    return {"success": True}

# Create agents with different permission levels
readonly_agent = Agent(
    name="ReadOnlyBot",
    scopes=["read:users"]
)

support_agent = Agent(
    name="SupportBot",
    scopes=["read:users", "write:users"]
)

admin_agent = Agent(
    name="AdminBot",
    scopes=["read:users", "write:users", "delete:users"]
)

def main():
    print("=" * 60)
    print("AgentSudo - Basic Usage Example")
    print("=" * 60)
    
    # Scenario 1: ReadOnly agent can only read
    print("\n--- Scenario 1: ReadOnly Agent ---")
    with readonly_agent.start_session():
        get_user("user_123")  # ✅ Allowed
        
        try:
            update_user("user_123", {"name": "Bob"})  # ❌ Denied
        except PermissionDeniedError as e:
            print(f"❌ Blocked: {e}")
    
    # Scenario 2: Support agent can read and write
    print("\n--- Scenario 2: Support Agent ---")
    with support_agent.start_session():
        get_user("user_456")  # ✅ Allowed
        update_user("user_456", {"email": "newemail@example.com"})  # ✅ Allowed
        
        try:
            delete_user("user_456")  # ❌ Denied
        except PermissionDeniedError as e:
            print(f"❌ Blocked: {e}")
    
    # Scenario 3: Admin agent can do everything
    print("\n--- Scenario 3: Admin Agent ---")
    with admin_agent.start_session():
        get_user("user_789")  # ✅ Allowed
        update_user("user_789", {"status": "inactive"})  # ✅ Allowed
        delete_user("user_789")  # ✅ Allowed

if __name__ == "__main__":
    main()
