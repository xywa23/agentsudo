"""
Slack Integration for AgentSudo

Provides human-in-the-loop approval workflows via Slack.
"""

import os
import time
import json
import threading
import logging
from typing import Optional, Dict, Any, Callable
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("agentsudo.slack")


class SlackApprovalTimeout(Exception):
    """Raised when an approval request times out."""
    pass


class SlackApproval:
    """
    Slack-based approval workflow for AgentSudo.
    
    Usage:
        from agentsudo import Agent, sudo
        from agentsudo.slack import SlackApproval
        
        slack = SlackApproval(
            webhook_url="https://hooks.slack.com/services/...",
            # OR use bot token for interactive messages:
            bot_token="xoxb-...",
            channel="#approvals",
        )
        
        @sudo(scope="delete:customer", on_deny=slack.request_approval)
        def delete_customer(customer_id: str):
            ...
    
    For interactive approvals (buttons), you need:
    1. A Slack app with Interactive Components enabled
    2. AgentSudo Cloud or your own webhook endpoint
    """
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        channel: Optional[str] = None,
        timeout: int = 300,  # 5 minutes default
        poll_interval: int = 2,
        cloud_api_key: Optional[str] = None,
        cloud_url: str = "https://agentsudo.dev/api/slack",
        auto_deny_on_timeout: bool = True,
    ):
        """
        Initialize Slack approval integration.
        
        Args:
            webhook_url: Slack Incoming Webhook URL (for simple notifications)
            bot_token: Slack Bot Token (xoxb-...) for interactive messages
            channel: Channel to post approval requests (required with bot_token)
            timeout: Seconds to wait for approval (default: 300)
            poll_interval: Seconds between polling for response (default: 2)
            cloud_api_key: AgentSudo Cloud API key for managed approvals
            cloud_url: AgentSudo Cloud API URL
            auto_deny_on_timeout: If True, deny on timeout. If False, raise exception.
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        self.channel = channel or os.environ.get("SLACK_APPROVAL_CHANNEL", "#approvals")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.cloud_api_key = cloud_api_key or os.environ.get("AGENTSUDO_API_KEY")
        self.cloud_url = cloud_url
        self.auto_deny_on_timeout = auto_deny_on_timeout
        
        # In-memory store for local approvals (for testing/simple use cases)
        self._pending_approvals: Dict[str, Optional[bool]] = {}
        self._approval_lock = threading.Lock()
        
        if not self.webhook_url and not self.bot_token and not self.cloud_api_key:
            logger.warning(
                "SlackApproval initialized without credentials. "
                "Set SLACK_WEBHOOK_URL, SLACK_BOT_TOKEN, or AGENTSUDO_API_KEY."
            )
    
    def request_approval(self, agent, scope: str, context: Dict[str, Any]) -> bool:
        """
        Request approval via Slack. This is the callback for @sudo(on_deny=...).
        
        Args:
            agent: The Agent requesting approval
            scope: The scope being requested
            context: Context dict with function name, args, kwargs
            
        Returns:
            True if approved, False if denied
        """
        # Generate unique approval ID
        import uuid
        approval_id = str(uuid.uuid4())[:8]
        
        function_name = context.get("function", "unknown")
        
        # Build the approval message
        message = self._build_approval_message(
            approval_id=approval_id,
            agent_name=agent.name,
            scope=scope,
            function_name=function_name,
            context=context,
        )
        
        # Use Cloud API if available (supports interactive buttons)
        if self.cloud_api_key:
            return self._request_cloud_approval(approval_id, agent, scope, context, message)
        
        # Use Bot Token for interactive messages
        if self.bot_token:
            return self._request_interactive_approval(approval_id, agent, scope, context, message)
        
        # Fallback to webhook (notification only, no interactive response)
        if self.webhook_url:
            return self._request_webhook_approval(approval_id, agent, scope, context, message)
        
        # No Slack configured - deny by default
        logger.error("Slack not configured. Denying approval request.")
        return False
    
    def _build_approval_message(
        self,
        approval_id: str,
        agent_name: str,
        scope: str,
        function_name: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build Slack Block Kit message for approval request."""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔐 AgentSudo Approval Request",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Agent:*\n{agent_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Scope:*\n`{scope}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Function:*\n`{function_name}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Request ID:*\n`{approval_id}`"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"⏱️ Expires in {self.timeout} seconds"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "actions",
                    "block_id": f"approval_{approval_id}",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "action_id": "approve",
                            "value": approval_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Deny",
                                "emoji": True
                            },
                            "style": "danger",
                            "action_id": "deny",
                            "value": approval_id
                        }
                    ]
                }
            ]
        }
    
    def _request_cloud_approval(
        self,
        approval_id: str,
        agent,
        scope: str,
        context: Dict[str, Any],
        message: Dict[str, Any],
    ) -> bool:
        """Request approval via AgentSudo Cloud (managed Slack integration)."""
        try:
            payload = {
                "approval_id": approval_id,
                "agent_name": agent.name,
                "agent_id": agent.id,
                "scope": scope,
                "function": context.get("function", "unknown"),
                "timeout": self.timeout,
                "channel": self.channel,
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.cloud_api_key}",
            }
            
            # Send approval request to cloud
            req = Request(
                f"{self.cloud_url}/approvals",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            
            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                cloud_approval_id = result.get("id")
            
            # Poll for response
            return self._poll_cloud_approval(cloud_approval_id)
            
        except Exception as e:
            logger.error(f"Cloud approval request failed: {e}")
            return False
    
    def _poll_cloud_approval(self, cloud_approval_id: str) -> bool:
        """Poll AgentSudo Cloud for approval response."""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                headers = {
                    "Authorization": f"Bearer {self.cloud_api_key}",
                }
                
                req = Request(
                    f"{self.cloud_url}/approvals/{cloud_approval_id}",
                    headers=headers,
                    method="GET",
                )
                
                with urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    status = result.get("status")
                    
                    if status == "approved":
                        logger.info(f"Approval {cloud_approval_id} approved via Slack")
                        return True
                    elif status == "denied":
                        logger.info(f"Approval {cloud_approval_id} denied via Slack")
                        return False
                    # status == "pending" - continue polling
                    
            except Exception as e:
                logger.warning(f"Error polling approval status: {e}")
            
            time.sleep(self.poll_interval)
        
        # Timeout
        logger.warning(f"Approval {cloud_approval_id} timed out after {self.timeout}s")
        if self.auto_deny_on_timeout:
            return False
        raise SlackApprovalTimeout(f"Approval request timed out after {self.timeout} seconds")
    
    def _request_interactive_approval(
        self,
        approval_id: str,
        agent,
        scope: str,
        context: Dict[str, Any],
        message: Dict[str, Any],
    ) -> bool:
        """Request approval using Slack Bot Token with interactive buttons."""
        try:
            # Post message to Slack
            payload = {
                "channel": self.channel,
                **message,
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot_token}",
            }
            
            req = Request(
                "https://slack.com/api/chat.postMessage",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            
            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("ok"):
                    logger.error(f"Slack API error: {result.get('error')}")
                    return False
            
            # Initialize pending approval
            with self._approval_lock:
                self._pending_approvals[approval_id] = None
            
            # Wait for response (set via handle_interaction)
            return self._wait_for_local_approval(approval_id)
            
        except Exception as e:
            logger.error(f"Interactive approval request failed: {e}")
            return False
    
    def _request_webhook_approval(
        self,
        approval_id: str,
        agent,
        scope: str,
        context: Dict[str, Any],
        message: Dict[str, Any],
    ) -> bool:
        """
        Send notification via webhook (no interactive response).
        
        Note: Webhooks don't support interactive buttons. This sends a notification
        and immediately returns False. Use bot_token or cloud_api_key for
        interactive approvals.
        """
        try:
            # Modify message to remove buttons (webhooks don't support them)
            notification = {
                "text": (
                    f"🔐 *AgentSudo Approval Request*\n"
                    f"Agent `{agent.name}` is requesting scope `{scope}` "
                    f"for function `{context.get('function', 'unknown')}`.\n"
                    f"_Approval ID: {approval_id}_\n\n"
                    f"⚠️ Interactive approvals require AgentSudo Cloud or a Slack Bot Token."
                ),
                "blocks": message["blocks"][:-1],  # Remove actions block
            }
            
            req = Request(
                self.webhook_url,
                data=json.dumps(notification).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            with urlopen(req, timeout=10):
                pass
            
            logger.warning(
                f"Approval request {approval_id} sent via webhook. "
                "Interactive approvals not available - denying by default."
            )
            return False
            
        except Exception as e:
            logger.error(f"Webhook approval request failed: {e}")
            return False
    
    def _wait_for_local_approval(self, approval_id: str) -> bool:
        """Wait for approval response (for local/testing scenarios)."""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            with self._approval_lock:
                result = self._pending_approvals.get(approval_id)
                if result is not None:
                    del self._pending_approvals[approval_id]
                    return result
            
            time.sleep(self.poll_interval)
        
        # Timeout - clean up
        with self._approval_lock:
            self._pending_approvals.pop(approval_id, None)
        
        logger.warning(f"Approval {approval_id} timed out after {self.timeout}s")
        if self.auto_deny_on_timeout:
            return False
        raise SlackApprovalTimeout(f"Approval request timed out after {self.timeout} seconds")
    
    def handle_interaction(self, approval_id: str, approved: bool, user: str = "unknown") -> bool:
        """
        Handle an approval/denial from Slack interactive component.
        
        This should be called from your webhook endpoint that receives
        Slack interactive payloads.
        
        Args:
            approval_id: The approval request ID
            approved: True if approved, False if denied
            user: Slack user who responded
            
        Returns:
            True if the approval was found and updated, False otherwise
        """
        with self._approval_lock:
            if approval_id in self._pending_approvals:
                self._pending_approvals[approval_id] = approved
                action = "approved" if approved else "denied"
                logger.info(f"Approval {approval_id} {action} by {user}")
                return True
        
        logger.warning(f"Approval {approval_id} not found (may have expired)")
        return False
    
    def approve(self, approval_id: str, user: str = "unknown") -> bool:
        """Approve a pending request."""
        return self.handle_interaction(approval_id, True, user)
    
    def deny(self, approval_id: str, user: str = "unknown") -> bool:
        """Deny a pending request."""
        return self.handle_interaction(approval_id, False, user)


# Convenience function for simple setup
def create_slack_approval(
    webhook_url: Optional[str] = None,
    bot_token: Optional[str] = None,
    channel: str = "#approvals",
    timeout: int = 300,
) -> Callable:
    """
    Create a Slack approval callback for use with @sudo decorator.
    
    Usage:
        from agentsudo import sudo
        from agentsudo.slack import create_slack_approval
        
        slack_approve = create_slack_approval(
            bot_token="xoxb-...",
            channel="#approvals"
        )
        
        @sudo(scope="delete:*", on_deny=slack_approve)
        def delete_record(id: str):
            ...
    """
    slack = SlackApproval(
        webhook_url=webhook_url,
        bot_token=bot_token,
        channel=channel,
        timeout=timeout,
    )
    return slack.request_approval
