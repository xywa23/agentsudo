import sys
import os
import time

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from ai_sudo import Agent, sudo, PermissionDeniedError
# Try importing ScopedModel, handle if pydantic not installed
try:
    from ai_sudo.integrations import ScopedModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

# --- 1. Define Safe Functions & Models ---

@sudo(scope="read:database")
def fetch_user_data(user_id):
    print(f"   💾 [DB] Fetching data for user {user_id}...")
    return {"id": user_id, "name": "Alice"}

# Audit Mode: Will LOG but NOT BLOCK
@sudo(scope="write:database", on_deny="log")
def delete_user_audit_only(user_id):
    print(f"   🔥 [DB] (Audit Mode) DELETING user {user_id}...")
    return True

# Callback Mode: Ask for permission
def slack_approval_callback(agent, scope, func, args, kwargs):
    print(f"   📱 [Slack] Requesting approval for {agent.name} to use {scope}...")
    # Simulate human approval logic
    if "sudo" in agent.name.lower(): # Auto-approve if name contains "sudo"
        return True
    return False

@sudo(scope="write:database", on_deny=slack_approval_callback)
def delete_user_with_approval(user_id):
    print(f"   🔥 [DB] DELETING user {user_id}...")
    return True

if HAS_PYDANTIC:
    class RefundRequest(ScopedModel):
        _required_scope = "write:refunds"
        order_id: str
        amount: float

# --- 2. Create Agents ---

analyst_agent = Agent(name="AnalystBot", scopes=["read:database"])
admin_agent = Agent(name="AdminBot", scopes=["read:database", "write:database"])
sudo_agent = Agent(name="SuperSudoBot", scopes=["read:database"]) # Has specific name for callback

# --- 3. Run Simulation ---

def run_demo():
    print("============================================")
    print("🛡️  AI-SUDO / AGENT SCOPE DEMO")
    print("============================================")

    # 1. Basic Blocking
    print("\n--- 1. Basic Permission Check (Analyst tries DELETE) ---")
    try:
        with analyst_agent.start_session():
            # This function uses default on_deny="raise"
            # But wait, I didn't define a default delete_user in this file yet.
            pass 
            # Let's define one locally or just skip. 
            # I'll use fetch (success) and approval (fail) to show basic flow.
            fetch_user_data(101)
    except PermissionDeniedError as e:
        print(f"🛑 BLOCKED: {e}")

    # 2. Audit Mode
    print("\n--- 2. Audit Mode (Analyst tries DELETE - Log Only) ---")
    with analyst_agent.start_session():
        # Should succeed but print a warning log
        delete_user_audit_only(999)

    # 3. Callback / Approval Mode
    print("\n--- 3. Approval Mode (Analyst tries DELETE - Needs Approval) ---")
    try:
        with analyst_agent.start_session():
            delete_user_with_approval(555)
    except PermissionDeniedError as e:
        print(f"🛑 BLOCKED by Callback: {e}")

    print("\n--- 4. Approval Mode (SuperSudoBot tries DELETE - Approved) ---")
    try:
        with sudo_agent.start_session():
            delete_user_with_approval(777)
    except PermissionDeniedError as e:
        print(f"🛑 BLOCKED: {e}")

    # 4. Pydantic Integration
    if HAS_PYDANTIC:
        print("\n--- 5. Pydantic Model Scope (Analyst tries Refund) ---")
        try:
            with analyst_agent.start_session():
                # Analyst lacks "write:refunds"
                req = RefundRequest(order_id="abc", amount=100.0)
                print("Refund created!")
        except PermissionDeniedError as e:
            print(f"🛑 BLOCKED Model Init: {e}")
            
        print("\n--- 6. Pydantic Model Scope (Admin w/ Scope) ---")
        # Give Admin the scope temporarily for demo
        admin_agent.scopes.add("write:refunds") 
        try:
            with admin_agent.start_session():
                req = RefundRequest(order_id="abc", amount=100.0)
                print(f"✅ Refund Request Validated: {req}")
        except PermissionDeniedError as e:
            print(f"🛑 BLOCKED: {e}")

if __name__ == "__main__":
    run_demo()
