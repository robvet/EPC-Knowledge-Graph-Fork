"""Mock LLM agent base class.

Simulates agent behaviour for the demo by matching user queries to tool calls
and generating structured responses. In production, this would be replaced by
the Microsoft Agent Framework with Azure OpenAI.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


# ── Activity Log ────────────────────────────────────────────────────────────

@dataclass
class AgentActivity:
    id: str
    agent_name: str
    agent_icon: str
    action: str
    detail: str
    timestamp: str
    entities: List[str] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "agent_icon": self.agent_icon,
            "action": self.action,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "entities": self.entities,
            "tool_calls": self.tool_calls,
        }


# Global activity log (agents append here; SSE streams from here)
_activity_log: List[AgentActivity] = []


def get_activity_log() -> List[AgentActivity]:
    return _activity_log


def log_activity(
    agent_name: str,
    agent_icon: str,
    action: str,
    detail: str,
    entities: List[str] | None = None,
    tool_calls: List[str] | None = None,
) -> AgentActivity:
    entry = AgentActivity(
        id=str(uuid.uuid4())[:8],
        agent_name=agent_name,
        agent_icon=agent_icon,
        action=action,
        detail=detail,
        timestamp=datetime.now().isoformat(),
        entities=entities or [],
        tool_calls=tool_calls or [],
    )
    _activity_log.append(entry)
    return entry


def clear_activity_log() -> None:
    _activity_log.clear()


# ── Base Agent ──────────────────────────────────────────────────────────────

class BaseAgent:
    """Lightweight agent that runs tool functions and logs activity.

    In the real Microsoft Agent Framework integration, this class would be
    replaced by the framework's agent class with Azure OpenAI chat completions
    driving tool selection. For the demo, tool selection is rule-based.
    """

    name: str = "Base Agent"
    icon: str = "🤖"
    system_prompt: str = ""
    tools: Dict[str, Callable] = {}

    def __init__(self) -> None:
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable) -> None:
        self.tools[name] = func

    def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Call a registered tool and log the activity."""
        func = self.tools.get(tool_name)
        if not func:
            return {"error": f"Tool '{tool_name}' not found on {self.name}"}
        result = func(**kwargs)
        log_activity(
            agent_name=self.name,
            agent_icon=self.icon,
            action=f"Called tool: {tool_name}",
            detail=f"Args: {kwargs}" if kwargs else "No arguments",
            tool_calls=[tool_name],
        )
        return result

    def respond(self, message: str) -> Dict[str, Any]:
        """Process a user/orchestrator message and produce a response.

        Override in subclasses for domain-specific behaviour.
        """
        log_activity(
            agent_name=self.name,
            agent_icon=self.icon,
            action="Received message",
            detail=message[:200],
        )
        return {"agent": self.name, "response": f"Acknowledged: {message}"}
