"""
Cloud Mode - Connect AgentSudo SDK to the hosted dashboard.

Usage:
    import agentsudo
    agentsudo.configure_cloud(api_key="as_your_api_key")
"""

import os
import threading
import queue
import time
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("agentsudo.cloud")

# Global cloud configuration
_cloud_config: Optional['CloudConfig'] = None


class CloudConfig:
    """Configuration for cloud telemetry."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://agentsudo.dev",
        async_send: bool = True,
        batch_size: int = 10,
        flush_interval: float = 5.0,
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.async_send = async_send
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Event queue for async sending
        self._event_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        if async_send:
            self._start_worker()
    
    def _start_worker(self):
        """Start background worker thread for sending events."""
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def _worker_loop(self):
        """Background worker that batches and sends events."""
        batch: List[Dict[str, Any]] = []
        last_flush = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Try to get an event with timeout
                event = self._event_queue.get(timeout=1.0)
                batch.append(event)
                
                # Flush if batch is full or interval elapsed
                if len(batch) >= self.batch_size or (time.time() - last_flush) >= self.flush_interval:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()
                    
            except queue.Empty:
                # Flush remaining events on timeout
                if batch and (time.time() - last_flush) >= self.flush_interval:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()
        
        # Final flush on shutdown
        if batch:
            self._send_batch(batch)
    
    def _send_batch(self, events: List[Dict[str, Any]]):
        """Send a batch of events to the cloud endpoint."""
        if not events:
            return
            
        try:
            import urllib.request
            import urllib.error
            import ssl
            
            # Try to use certifi for SSL certificates if available
            try:
                import certifi
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                # Fallback: create context that doesn't verify (for dev environments)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            url = f"{self.endpoint}/api/events"
            data = json.dumps(events).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.api_key,
                    'User-Agent': 'agentsudo-sdk/0.3.1',
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                if response.status != 200:
                    logger.warning(f"Cloud telemetry failed: {response.status}")
                else:
                    logger.debug(f"Cloud telemetry sent: {len(events)} events")
                    
        except urllib.error.URLError as e:
            logger.debug(f"Cloud telemetry error: {e}")
        except Exception as e:
            logger.debug(f"Cloud telemetry error: {e}")
    
    def send_event(self, event: Dict[str, Any]):
        """Queue an event for sending."""
        if self.async_send:
            self._event_queue.put(event)
        else:
            self._send_batch([event])
    
    def flush(self):
        """Flush all pending events immediately."""
        if self.async_send:
            # Drain the queue and send
            events = []
            while not self._event_queue.empty():
                try:
                    events.append(self._event_queue.get_nowait())
                except queue.Empty:
                    break
            if events:
                self._send_batch(events)
    
    def shutdown(self):
        """Shutdown the cloud connection gracefully."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        self.flush()


def configure_cloud(
    api_key: Optional[str] = None,
    endpoint: str = "https://agentsudo.dev",
    async_send: bool = True,
    batch_size: int = 10,
    flush_interval: float = 5.0,
) -> CloudConfig:
    """
    Configure cloud telemetry for AgentSudo.
    
    Args:
        api_key: Your project API key from the dashboard. 
                 Falls back to AGENTSUDO_API_KEY environment variable.
        endpoint: Cloud endpoint URL (default: https://agentsudo.dev)
        async_send: Send events in background thread (default: True)
        batch_size: Number of events to batch before sending (default: 10)
        flush_interval: Seconds between automatic flushes (default: 5.0)
    
    Returns:
        CloudConfig instance
    
    Example:
        import agentsudo
        agentsudo.configure_cloud(api_key="as_your_api_key")
    """
    global _cloud_config
    
    # Get API key from argument or environment
    key = api_key or os.environ.get('AGENTSUDO_API_KEY')
    
    if not key:
        raise ValueError(
            "API key required. Pass api_key argument or set AGENTSUDO_API_KEY environment variable. "
            "Get your API key from https://agentsudo.dev/dashboard"
        )
    
    # Shutdown existing config if any
    if _cloud_config:
        _cloud_config.shutdown()
    
    _cloud_config = CloudConfig(
        api_key=key,
        endpoint=endpoint,
        async_send=async_send,
        batch_size=batch_size,
        flush_interval=flush_interval,
    )
    
    logger.info(f"Cloud mode enabled: {endpoint}")
    return _cloud_config


def get_cloud_config() -> Optional[CloudConfig]:
    """Get the current cloud configuration."""
    return _cloud_config


def send_telemetry(
    agent_name: str,
    action: str,
    scope: Optional[str] = None,
    allowed: bool = True,
    function_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Send a telemetry event to the cloud dashboard.
    
    This is called automatically by the @sudo decorator when cloud mode is enabled.
    You can also call it manually for custom events.
    
    Args:
        agent_name: Name of the agent
        action: Action being performed (e.g., "permission_check", "session_start")
        scope: Permission scope being checked
        allowed: Whether the action was allowed
        function_name: Name of the function being called
        metadata: Additional metadata to include
    """
    config = get_cloud_config()
    if not config:
        return  # Cloud mode not enabled
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_name": agent_name,
        "action": action,
        "scope": scope,
        "allowed": allowed,
        "function_name": function_name,
        "metadata": metadata,
    }
    
    # Remove None values
    event = {k: v for k, v in event.items() if v is not None}
    
    config.send_event(event)


def disable_cloud():
    """Disable cloud telemetry."""
    global _cloud_config
    if _cloud_config:
        _cloud_config.shutdown()
        _cloud_config = None
        logger.info("Cloud mode disabled")
