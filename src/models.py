"""Data models for safe agent execution, traces, and tool schemas."""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: str
    is_destructive: bool = False

class AgentAction(BaseModel):
    tool: str
    args: Dict[str, Any]
    thought: str = ""

class TraceStep(BaseModel):
    step_number: int
    thought: str
    action_tool: Optional[str] = None
    action_args: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    status: str = "success"  # success, error, approved, denied, cycle_detected
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ExecutionTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    dry_run: bool = False
    steps: List[TraceStep] = Field(default_factory=list)
    final_answer: Optional[str] = None
    aborted_reason: Optional[str] = None
    completed: bool = False
