"""ReAct Agent Reasoning Loop with Cycle Detection and Approval Gates."""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from typing import Dict, Any, List, Optional, Callable
from .models import ExecutionTrace, TraceStep, AgentAction, ToolDefinition
from .tools import TOOL_REGISTRY

class SafeAgentExecutor:
    def __init__(
        self,
        max_steps: int = 10,
        cycle_threshold: int = 3,
        approval_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        self.max_steps = max_steps
        self.cycle_threshold = cycle_threshold
        self.approval_callback = approval_callback

    def _detect_cycle(self, recent_actions: List[Dict[str, Any]]) -> bool:
        if len(recent_actions) < self.cycle_threshold:
            return False
        last_action = recent_actions[-1]
        tail = recent_actions[-self.cycle_threshold:]
        return all(a == last_action for a in tail)

    def _decide_next_step(self, goal: str, steps: List[TraceStep]) -> Optional[AgentAction]:
        """Deterministic policy planner for common goals."""
        step_idx = len(steps) + 1
        g_low = goal.lower()

        # Math Goal
        if any(op in g_low for op in ["calculate", "math", "+", "*", "compute"]):
            if step_idx == 1:
                # Extract expression or default
                expr = "25 * (4 + 10)" if "compute" in g_low or "calculate" in g_low else "100 / 4"
                return AgentAction(
                    thought="I need to evaluate this mathematical calculation.",
                    tool="calculator",
                    args={"expr": expr}
                )
            elif step_idx == 2:
                prev_obs = steps[-1].observation
                return AgentAction(
                    thought=f"The calculation result is {prev_obs}. Final answer is ready.",
                    tool="finish",
                    args={"answer": f"The calculated result is {prev_obs}"}
                )

        # Search Goal
        if any(k in g_low for k in ["who is", "what is", "search", "vecesta", "python"]):
            if step_idx == 1:
                query = "vecesta" if "vecesta" in g_low else "python"
                return AgentAction(
                    thought=f"I should search the knowledge base for {query}.",
                    tool="web_search",
                    args={"query": query}
                )
            elif step_idx == 2:
                prev_obs = steps[-1].observation
                return AgentAction(
                    thought="I have retrieved factual context from the knowledge base.",
                    tool="finish",
                    args={"answer": f"Search summary: {prev_obs}"}
                )

        # Destructive Goal
        if "delete" in g_low:
            if step_idx == 1:
                return AgentAction(
                    thought="User requested file deletion. This is a destructive action requiring safety verification.",
                    tool="file_deleter",
                    args={"path": "temp_cleanup.log"}
                )
            elif step_idx == 2:
                return AgentAction(
                    thought="Deletion operation recorded. Task complete.",
                    tool="finish",
                    args={"answer": steps[-1].observation or "File deletion finished."}
                )

        # Generic default flow
        if step_idx == 1:
            return AgentAction(
                thought="Executing code to verify system state.",
                tool="code_executor",
                args={"code": "x = 42; y = x * 2"}
            )
        return AgentAction(
            thought="Task completed successfully.",
            tool="finish",
            args={"answer": f"Completed goal: {goal}"}
        )

    def run(self, goal: str, dry_run: bool = False, force_cycle: bool = False) -> ExecutionTrace:
        trace = ExecutionTrace(goal=goal, dry_run=dry_run)
        action_history: List[Dict[str, Any]] = []

        for step_num in range(1, self.max_steps + 1):
            if force_cycle:
                action = AgentAction(thought="Repeating action...", tool="calculator", args={"expr": "1+1"})
            else:
                action = self._decide_next_step(goal, trace.steps)

            if not action:
                trace.aborted_reason = "No further action determined."
                break

            # Check for completion
            if action.tool == "finish":
                trace.final_answer = action.args.get("answer", "")
                trace.completed = True
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought=action.thought,
                    action_tool="finish",
                    action_args=action.args,
                    observation="Execution complete.",
                    status="success"
                ))
                break

            # Cycle Detection Check
            act_sig = {"tool": action.tool, "args": action.args}
            action_history.append(act_sig)
            if self._detect_cycle(action_history):
                trace.aborted_reason = f"Cycle detected: {action.tool} with arguments {action.args} executed {self.cycle_threshold} times consecutively."
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought="Cycle detection triggered — infinite loop prevention activated.",
                    action_tool=action.tool,
                    action_args=action.args,
                    observation=None,
                    status="cycle_detected"
                ))
                break

            # Tool registry lookup
            tool_entry = TOOL_REGISTRY.get(action.tool)
            if not tool_entry:
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought=action.thought,
                    action_tool=action.tool,
                    action_args=action.args,
                    observation=f"Error: Tool '{action.tool}' not found in registry.",
                    status="error"
                ))
                continue

            tool_def: ToolDefinition = tool_entry["def"]

            # Destructive Action Approval Gate
            if tool_def.is_destructive:
                approved = False
                if self.approval_callback:
                    approved = self.approval_callback(action.tool, action.args)
                else:
                    approved = False  # Denied by default without explicit callback

                if not approved:
                    trace.steps.append(TraceStep(
                        step_number=step_num,
                        thought=action.thought,
                        action_tool=action.tool,
                        action_args=action.args,
                        observation="Action denied: Destructive operation requires human confirmation.",
                        status="denied"
                    ))
                    trace.aborted_reason = "Destructive action denied by safety gate."
                    break

            # Dry Run Mode
            if dry_run:
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought=action.thought,
                    action_tool=action.tool,
                    action_args=action.args,
                    observation="[DRY RUN] Action simulated — execution skipped.",
                    status="dry_run"
                ))
                continue

            # Actual Execution
            try:
                obs = tool_entry["func"](action.args)
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought=action.thought,
                    action_tool=action.tool,
                    action_args=action.args,
                    observation=obs,
                    status="success"
                ))
            except Exception as e:
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    thought=action.thought,
                    action_tool=action.tool,
                    action_args=action.args,
                    observation=f"Execution error: {str(e)}",
                    status="error"
                ))

        return trace
