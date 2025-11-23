import sys
import os

# Ensure src is in path so we can import from it if not installed
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Modified import to work with the sys.path hack above, or standard installation
# The user code had: from src.ai_sudo ...
# If we add 'src' to path, we should import ai_sudo directly.
# BUT if we want to follow the user's exact import 'from src.ai_sudo', then 'src' must be importable.
# I'll assume the user intends to run this from the root without installing, so I will NOT add 'src' to path yet
# and instead rely on the user's import structure if 'src' was a package.
# However, 'src' layouts usually mean 'ai_sudo' is the package.
# To make 'from src.ai_sudo' work, 'src' needs to be a python package (have __init__.py).
# Let's try to stick to valid python first. 

# If I just add the current directory to python path (default), `import src.ai_sudo` works if `src` has `__init__.py` or is a namespace package (Py3).
# I will stick to the user's code as much as possible.

from ai_sudo import Agent, sudo, PermissionDeniedError

# --- 1. Define your Safe Functions ---

@sudo(scope="read:database")
def fetch_user_data(user_id):
    print(f"   💾 [DB] Fetching data for user {user_id}...")
    return {"id": user_id, "name": "Alice"}

@sudo(scope="write:database")
def delete_user(user_id):
    print(f"   🔥 [DB] DELETING user {user_id}...")
    return True

# --- 2. Create Agents with Different Identities ---

# Only allowed to READ
analyst_agent = Agent(name="AnalystBot", scopes=["read:database"])

# Allowed to READ and DELETE
admin_agent = Agent(name="AdminBot", scopes=["read:database", "write:database"])

# --- 3. Run The Simulation ---

print("\n--- 🤖 SCENARIO 1: Analyst Bot tries to Read (Should Work) ---")
try:
    with analyst_agent.start_session():
        fetch_user_data(101)
except PermissionDeniedError as e:
    print(f"Caught Error: {e}")

print("\n--- 🤖 SCENARIO 2: Analyst Bot tries to Delete (Should FAIL) ---")
try:
    with analyst_agent.start_session():
        delete_user(101)
except PermissionDeniedError as e:
    print(f"🛑 BLOCKED: {e}")

print("\n--- 🤖 SCENARIO 3: Admin Bot tries to Delete (Should Work) ---")
try:
    with admin_agent.start_session():
        delete_user(101)
except PermissionDeniedError as e:
    print(f"Caught Error: {e}")
