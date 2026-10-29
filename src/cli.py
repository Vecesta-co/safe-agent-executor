"""CLI for safe-agent-executor."""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
from .executor import SafeAgentExecutor
from .tools import TOOL_REGISTRY

def cmd_tools(args):
    print("Registered Agent Tools:")
    for name, entry in TOOL_REGISTRY.items():
        tdef = entry["def"]
        destr = " [DESTRUCTIVE]" if tdef.is_destructive else ""
        print(f"  • {name}{destr}: {tdef.description}")
        print(f"    Parameters: {tdef.parameters} -> Returns: {tdef.returns}")

def cmd_run(args):
    def cli_approver(tool: str, tool_args: dict) -> bool:
        if args.auto_approve:
            return True
        resp = input(f"\n[APPROVAL GATE] Approve destructive action '{tool}' with {tool_args}? (y/N): ")
        return resp.strip().lower() in ("y", "yes")

    executor = SafeAgentExecutor(approval_callback=cli_approver)
    trace = executor.run(args.goal, dry_run=args.dry_run)

    print(f"\n=== Execution Trace: {trace.trace_id[:8]} ===")
    print(f"Goal: {trace.goal}")
    print(f"Dry Run: {trace.dry_run}")
    print(f"Completed: {trace.completed}")
    if trace.aborted_reason:
        print(f"Aborted: {trace.aborted_reason}")

    print("\nSteps:")
    for s in trace.steps:
        print(f"  [{s.step_number}] Thought: {s.thought}")
        if s.action_tool:
            print(f"      Action: {s.action_tool}({s.action_args})")
        if s.observation:
            print(f"      Obs:    {s.observation}")
        print(f"      Status: {s.status}")

    if trace.final_answer:
        print(f"\nFinal Answer: {trace.final_answer}")

def main():
    parser = argparse.ArgumentParser(prog="safe-agent", description="Safe Agent Executor CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("tools", help="List registered tools")

    p_run = sub.add_parser("run", help="Execute an agent goal")
    p_run.add_argument("goal", help="Task / Goal to accomplish")
    p_run.add_argument("--dry-run", action="store_true", help="Simulate without executing")
    p_run.add_argument("--auto-approve", action="store_true", help="Auto-approve destructive operations")

    args = parser.parse_args()
    if args.command == "tools":
        cmd_tools(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
