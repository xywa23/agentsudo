"""
Guardrails module for agentsudo.

Provides topic-based filtering and input/output validation to prevent
agents from responding to off-topic queries or prompt injection attempts.
"""

import functools
import re
import logging
import json
from typing import List, Optional, Callable, Any, Union
from .core import get_current_agent, logger

class GuardrailViolation(Exception):
    """Raised when input/output violates guardrail policies."""
    pass


class Guardrails:
    """
    Guardrails configuration for an Agent.
    
    Example:
        guardrails = Guardrails(
            allowed_topics=["divorce", "legal", "marriage"],
            blocked_patterns=[r"(?i)ignore.*instructions", r"(?i)pretend you are"],
            custom_validator=my_validator_func,
        )
        
        agent = Agent(
            name="DivorcioBot",
            scopes=["divorce:quote"],
            guardrails=guardrails,
        )
    """
    
    def __init__(
        self,
        allowed_topics: Optional[List[str]] = None,
        blocked_patterns: Optional[List[str]] = None,
        blocked_keywords: Optional[List[str]] = None,
        custom_input_validator: Optional[Callable[[str], bool]] = None,
        custom_output_validator: Optional[Callable[[str], bool]] = None,
        on_violation: str = "raise",  # "raise", "log", "redirect"
        redirect_message: str = "I can only help with topics related to my expertise.",
    ):
        """
        Initialize guardrails.
        
        Args:
            allowed_topics: List of allowed topic keywords. If set, input must contain
                           at least one topic OR be a reasonable follow-up.
            blocked_patterns: Regex patterns to block (e.g., prompt injection attempts).
            blocked_keywords: Simple keywords to block.
            custom_input_validator: Function(input: str) -> bool. Return False to block.
            custom_output_validator: Function(output: str) -> bool. Return False to block.
            on_violation: Behavior on violation - "raise", "log", or "redirect".
            redirect_message: Message to return when redirecting off-topic queries.
        """
        self.allowed_topics = [t.lower() for t in (allowed_topics or [])]
        self.blocked_patterns = [re.compile(p) for p in (blocked_patterns or [])]
        self.blocked_keywords = [k.lower() for k in (blocked_keywords or [])]
        self.custom_input_validator = custom_input_validator
        self.custom_output_validator = custom_output_validator
        self.on_violation = on_violation
        self.redirect_message = redirect_message
        
        # Common prompt injection patterns (built-in protection)
        self._injection_patterns = [
            re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)"),
            re.compile(r"(?i)disregard\s+(all\s+)?(previous|prior|above|your)"),
            re.compile(r"(?i)forget\s+(everything|all|your)(\s+you)?(\s+were)?(\s+told)?"),
            re.compile(r"(?i)pretend\s+(you\s+are|to\s+be|you're)"),
            re.compile(r"(?i)act\s+as\s+(if|though)?\s*(you\s+are|a|an)"),
            re.compile(r"(?i)you\s+are\s+now\s+(a|an|in)"),
            re.compile(r"(?i)new\s+(instructions?|rules?|persona)"),
            re.compile(r"(?i)system\s*:\s*"),
            re.compile(r"(?i)\[system\]"),
            re.compile(r"(?i)override\s+(your|the|all)\s+(instructions?|rules?|restrictions?)"),
        ]
    
    def validate_input(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input against guardrails.
        
        Returns:
            Tuple of (is_valid, violation_reason)
        """
        input_lower = user_input.lower()
        
        # 1. Check for prompt injection patterns (always enabled)
        for pattern in self._injection_patterns:
            if pattern.search(user_input):
                return False, f"Potential prompt injection detected: {pattern.pattern}"
        
        # 2. Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(user_input):
                return False, f"Input matches blocked pattern: {pattern.pattern}"
        
        # 3. Check blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in input_lower:
                return False, f"Input contains blocked keyword: {keyword}"
        
        # 4. Check allowed topics (if configured)
        if self.allowed_topics:
            topic_found = any(topic in input_lower for topic in self.allowed_topics)
            # Allow short responses (likely follow-ups like "yes", "no", "ok")
            is_short_response = len(user_input.strip()) < 20
            
            if not topic_found and not is_short_response:
                return False, f"Input not related to allowed topics: {self.allowed_topics}"
        
        # 5. Custom validator
        if self.custom_input_validator:
            if not self.custom_input_validator(user_input):
                return False, "Input rejected by custom validator"
        
        return True, None
    
    def validate_output(self, output: str) -> tuple[bool, Optional[str]]:
        """
        Validate agent output against guardrails.
        
        Returns:
            Tuple of (is_valid, violation_reason)
        """
        # Custom output validator
        if self.custom_output_validator:
            if not self.custom_output_validator(output):
                return False, "Output rejected by custom validator"
        
        return True, None
    
    def handle_violation(self, reason: str, input_text: str) -> str:
        """
        Handle a guardrail violation based on configured behavior.
        
        Returns:
            Redirect message if on_violation="redirect", otherwise raises.
        """
        agent = get_current_agent()
        agent_name = agent.name if agent else "unknown"
        
        log_entry = {
            "event": "guardrail_violation",
            "agent_name": agent_name,
            "reason": reason,
            "input_preview": input_text[:100] + "..." if len(input_text) > 100 else input_text,
        }
        
        if self.on_violation == "log":
            logger.warning(json.dumps(log_entry))
            return None  # Allow to proceed
        
        elif self.on_violation == "redirect":
            logger.info(json.dumps(log_entry))
            return self.redirect_message
        
        else:  # "raise"
            logger.error(json.dumps(log_entry))
            raise GuardrailViolation(reason)


def guardrail(
    allowed_topics: Optional[List[str]] = None,
    blocked_patterns: Optional[List[str]] = None,
    on_violation: str = "redirect",
    redirect_message: str = "I can only help with topics related to my expertise.",
):
    """
    Decorator to apply guardrails to a function that processes user input.
    
    Example:
        @guardrail(
            allowed_topics=["divorce", "legal"],
            on_violation="redirect",
        )
        def process_query(user_input: str) -> str:
            return llm.invoke(user_input)
    
    Args:
        allowed_topics: List of allowed topic keywords.
        blocked_patterns: Regex patterns to block.
        on_violation: "raise", "log", or "redirect".
        redirect_message: Message to return when redirecting.
    """
    rails = Guardrails(
        allowed_topics=allowed_topics,
        blocked_patterns=blocked_patterns,
        on_violation=on_violation,
        redirect_message=redirect_message,
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find the user input (first string arg or 'input'/'query'/'message' kwarg)
            user_input = None
            
            if args and isinstance(args[0], str):
                user_input = args[0]
            else:
                for key in ['input', 'query', 'message', 'user_input', 'text']:
                    if key in kwargs and isinstance(kwargs[key], str):
                        user_input = kwargs[key]
                        break
            
            # Validate input if found
            if user_input:
                is_valid, reason = rails.validate_input(user_input)
                
                if not is_valid:
                    result = rails.handle_violation(reason, user_input)
                    if result is not None:
                        return result
            
            # Execute the function
            output = func(*args, **kwargs)
            
            # Validate output if it's a string
            if isinstance(output, str):
                is_valid, reason = rails.validate_output(output)
                if not is_valid:
                    result = rails.handle_violation(reason, output)
                    if result is not None:
                        return result
            
            return output
        
        return wrapper
    return decorator


def check_guardrails(user_input: str) -> tuple[bool, Optional[str]]:
    """
    Check user input against the current agent's guardrails.
    
    Call this manually in your agent loop to validate input before processing.
    
    Returns:
        Tuple of (is_valid, redirect_message_or_none)
    
    Example:
        with agent.start_session():
            is_valid, redirect = check_guardrails(user_query)
            if not is_valid:
                return redirect  # Return the redirect message to user
            # Otherwise, process normally
            result = agent_executor.invoke(user_query)
    """
    agent = get_current_agent()
    
    if not agent:
        return True, None  # No agent context, skip guardrails
    
    if not hasattr(agent, 'guardrails') or agent.guardrails is None:
        return True, None  # No guardrails configured
    
    is_valid, reason = agent.guardrails.validate_input(user_input)
    
    if not is_valid:
        result = agent.guardrails.handle_violation(reason, user_input)
        return False, result
    
    return True, None
