"""Tool registry and built-in safe execution tools."""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")

import ast
import operator
import os
from typing import Dict, Any, Callable
from .models import ToolDefinition

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

def safe_eval_expr(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = safe_eval_expr(node.left)
        right = safe_eval_expr(node.right)
        return SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = safe_eval_expr(node.operand)
        return SAFE_OPERATORS[op_type](operand)
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")

def tool_calculator(expr: str) -> str:
    parsed = ast.parse(expr, mode='eval')
    val = safe_eval_expr(parsed.body)
    return str(val)

def tool_web_search(query: str) -> str:
    # Deterministic knowledge base for safe simulated retrieval
    kb = {
        "python": "Python is a high-level interpreted programming language created by Guido van Rossum.",
        "vecesta": "Vecesta.co builds open-source AI developer tools, diffusers studios, and autonomous agents.",
        "react": "ReAct combines Reasoning (Thought) and Action in language model agents.",
        "quantum": "Quantum computing uses superposition and entanglement to execute parallel calculations."
    }
    q_low = query.lower()
    matches = [val for key, val in kb.items() if key in q_low]
    if matches:
        return " | ".join(matches)
    return f"Simulated search results for '{query}': No critical anomalies detected."

def tool_file_reader(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(2048)

def tool_code_executor(code: str) -> str:
    # Restricted sandboxed execution
    safe_globals = {"__builtins__": {"print": print, "range": range, "len": len, "int": int, "float": float, "str": str}}
    local_vars: Dict[str, Any] = {}
    try:
        compiled = compile(code, "<agent_exec>", "exec")
        exec(compiled, safe_globals, local_vars)
        return f"Executed cleanly. Variables produced: {list(local_vars.keys())}"
    except Exception as e:
        return f"Execution error: {str(e)}"

def tool_file_deleter(path: str) -> str:
    # Destructive action
    if os.path.exists(path):
        os.remove(path)
        return f"Deleted file: {path}"
    return f"File does not exist: {path}"

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "calculator": {
        "def": ToolDefinition(
            name="calculator",
            description="Safely evaluate basic mathematical expressions (e.g. '12 * (4 + 6)')",
            parameters={"expr": "string"},
            returns="string",
            is_destructive=False
        ),
        "func": lambda args: tool_calculator(args.get("expr", "0"))
    },
    "web_search": {
        "def": ToolDefinition(
            name="web_search",
            description="Search knowledge base for verified factual facts",
            parameters={"query": "string"},
            returns="string",
            is_destructive=False
        ),
        "func": lambda args: tool_web_search(args.get("query", ""))
    },
    "file_reader": {
        "def": ToolDefinition(
            name="file_reader",
            description="Read content from a local file",
            parameters={"path": "string"},
            returns="string",
            is_destructive=False
        ),
        "func": lambda args: tool_file_reader(args.get("path", ""))
    },
    "code_executor": {
        "def": ToolDefinition(
            name="code_executor",
            description="Execute simple sandboxed Python snippets",
            parameters={"code": "string"},
            returns="string",
            is_destructive=False
        ),
        "func": lambda args: tool_code_executor(args.get("code", ""))
    },
    "file_deleter": {
        "def": ToolDefinition(
            name="file_deleter",
            description="Permanently delete a specified file",
            parameters={"path": "string"},
            returns="string",
            is_destructive=True
        ),
        "func": lambda args: tool_file_deleter(args.get("path", ""))
    }
}
