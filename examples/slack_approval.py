"""
Slack Approval Workflow Example

Demonstrates human-in-the-loop approval via Slack for high-risk actions.

Setup:
1. Create a Slack app at https://api.slack.com/apps
2. Enable Interactive Components and set Request URL to your webhook
3. Set environment variables:
   - SLACK_BOT_TOKEN=xoxb-...
   - SLACK_APPROVAL_CHANNEL=#approvals
   
   OR for AgentSudo Cloud:
   - AGENTSUDO_API_KEY=as_...
"""

from agentsudo import Agent, sudo
from agentsudo.slack import SlackApproval, create_slack_approval

# Option 1: Full control with SlackApproval class
slack = SlackApproval(
    # Use bot token for direct Slack integration
    # bot_token="xoxb-...",  # Or set SLACK_BOT_TOKEN env var
    # channel="#approvals",
    
    # OR use AgentSudo Cloud for managed integration
    # cloud_api_key="as_...",  # Or set AGENTSUDO_API_KEY env var
    
    timeout=300,  # 5 minutes to respond
    auto_deny_on_timeout=True,  # Deny if no response
)

# Option 2: Quick setup with convenience function
# slack_approve = create_slack_approval(
#     bot_token="xoxb-...",
#     channel="#approvals",
#     timeout=300,
# )


@sudo(scope="delete:customer", on_deny=slack.request_approval)
def delete_customer(customer_id: str):
    """Delete a customer - requires Slack approval."""
    print(f"Deleting customer {customer_id}")
    return {"success": True, "customer_id": customer_id}


@sudo(scope="refund:large", on_deny=slack.request_approval)
def issue_large_refund(order_id: str, amount: float):
    """Issue a large refund - requires Slack approval."""
    print(f"Issuing ${amount:.2f} refund for order {order_id}")
    return {"success": True, "order_id": order_id, "amount": amount}


@sudo(scope="deploy:production", on_deny=slack.request_approval)
def deploy_to_production(version: str):
    """Deploy to production - requires Slack approval."""
    print(f"Deploying version {version} to production")
    return {"success": True, "version": version}


def main():
    print("=" * 60)
    print("AgentSudo - Slack Approval Workflow Example")
    print("=" * 60)
    
    # Agent without dangerous permissions (will trigger approval flow)
    support_agent = Agent(
        name="SupportBot",
        scopes=["read:customers", "write:tickets"]  # No delete/refund scopes
    )
    
    print("\n--- Support Agent attempting high-risk actions ---")
    print("(These will trigger Slack approval requests)")
    
    with support_agent.start_session():
        # Try to delete customer - will send Slack approval request
        print("\n1. Attempting to delete customer...")
        try:
            result = delete_customer("cust_123")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Blocked: {type(e).__name__}: {e}")
        
        # Try to issue large refund - will send Slack approval request
        print("\n2. Attempting to issue large refund...")
        try:
            result = issue_large_refund("order_456", 5000.00)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Blocked: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("Note: Without Slack credentials configured, requests are denied.")
    print("Set SLACK_BOT_TOKEN or AGENTSUDO_API_KEY to enable approvals.")
    print("=" * 60)


if __name__ == "__main__":
    main()
