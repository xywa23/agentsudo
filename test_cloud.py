#!/usr/bin/env python3
"""
AgentSudo Cloud Mode Demo

This script demonstrates the SDK → Dashboard integration.
Run this to see events appear in your dashboard in real-time.
"""

import sys
import os

# Add src to path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agentsudo import Agent, sudo, configure_cloud

# Get API key from environment
API_KEY = os.environ.get("AGENTSUDO_API_KEY", "YOUR_API_KEY_HERE")

if API_KEY == "YOUR_API_KEY_HERE":
    print("⚠️  Set AGENTSUDO_API_KEY environment variable")
    print("   export AGENTSUDO_API_KEY=your-key-here")
    print("   Get your API key from: https://agentsudo.vercel.app/dashboard")
    sys.exit(1)

# Connect to AgentSudo Cloud (sync mode to ensure events are sent before script exits)
configure_cloud(api_key=API_KEY, async_send=False)

# =============================================================================
# AGENT 1: Customer Support Bot
# =============================================================================
support_bot = Agent(
    name="SupportBot",
    scopes=["read:customers", "read:orders", "write:tickets"]
)

@sudo(scope="read:customers")
def get_customer(customer_id: str):
    return {"id": customer_id, "name": "John Doe", "email": "john@example.com"}

@sudo(scope="read:orders")
def get_orders(customer_id: str):
    return [{"id": "ORD-001", "total": 99.99}, {"id": "ORD-002", "total": 149.99}]

@sudo(scope="write:tickets")
def create_ticket(customer_id: str, issue: str):
    return {"ticket_id": "TKT-001", "status": "open"}

@sudo(scope="write:refunds")
def process_refund(order_id: str):
    return {"refund_id": "REF-001"}

# =============================================================================
# AGENT 2: Data Analyst
# =============================================================================
analyst = Agent(
    name="DataAnalyst", 
    scopes=["read:analytics", "read:reports"]
)

@sudo(scope="read:analytics")
def get_analytics():
    return {"visitors": 1000, "conversions": 50}

@sudo(scope="read:reports")
def generate_report(report_type: str):
    return {"report": report_type, "data": [1, 2, 3]}

@sudo(scope="admin:database")
def drop_database():
    return "DANGER: Database dropped!"

# =============================================================================
# DEMO SCRIPT
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AgentSudo Cloud Demo")
    print("=" * 60)
    print()

    # Demo 1: Support Bot - Allowed Actions
    print("📞 SUPPORT BOT - Customer Service Scenario")
    print("-" * 40)
    with support_bot.start_session():
        print("✅ Getting customer info...")
        customer = get_customer("CUST-123")
        print(f"   → {customer['name']}")
        
        print("✅ Fetching orders...")
        orders = get_orders("CUST-123")
        print(f"   → Found {len(orders)} orders")
        
        print("✅ Creating support ticket...")
        ticket = create_ticket("CUST-123", "Shipping delay")
        print(f"   → Ticket {ticket['ticket_id']} created")
        
        print("❌ Attempting refund (not authorized)...")
        try:
            process_refund("ORD-001")
            print("   → Refund processed (unexpected!)")
        except PermissionError:
            print("   → BLOCKED: Missing write:refunds scope")
    
    print()
    
    # Demo 2: Data Analyst - Mixed Permissions
    print("📊 DATA ANALYST - Analytics Scenario")
    print("-" * 40)
    with analyst.start_session():
        print("✅ Reading analytics...")
        stats = get_analytics()
        print(f"   → {stats['visitors']} visitors, {stats['conversions']} conversions")
        
        print("✅ Generating report...")
        report = generate_report("weekly")
        print(f"   → Report ready")
        
        print("❌ Attempting database admin (not authorized)...")
        try:
            drop_database()
            print("   → Database dropped (VERY BAD!)")
        except PermissionError:
            print("   → BLOCKED: Missing admin:database scope")
    
    print()
    print("=" * 60)
    print("✨ Check your dashboard to see all events!")
    print("   https://agentsudo.vercel.app/dashboard")
    print("=" * 60)
