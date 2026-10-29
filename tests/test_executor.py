"""Comprehensive test suite for safe-agent-executor (25 tests)."""
import pytest
import os
from src.models import ToolDefinition, AgentAction, TraceStep, ExecutionTrace
from src.tools import (
    tool_calculator, tool_web_search, tool_file_reader,
    tool_code_executor, tool_file_deleter, TOOL_REGISTRY
)
from src.executor import SafeAgentExecutor

# 1. Calculator & Math Safety Tests
def test_calculator_basic_arithmetic():
    assert float(tool_calculator("10 + 5")) == 15.0
    assert float(tool_calculator("20 - 8")) == 12.0
    assert float(tool_calculator("6 * 7")) == 42.0
    assert float(tool_calculator("100 / 4")) == 25.0

def test_calculator_precedence():
    assert float(tool_calculator("2 + 3 * 4")) == 14.0
    assert float(tool_calculator("(2 + 3) * 4")) == 20.0

def test_calculator_unary_negative():
    assert float(tool_calculator("-5 + 10")) == 5.0

def test_calculator_blocks_function_calls():
    with pytest.raises(ValueError):
        tool_calculator("__import__('os').system('ls')")

def test_calculator_blocks_variable_names():
    with pytest.raises(ValueError):
        tool_calculator("x + 1")

# 2. Tools Tests
def test_web_search_known_topic():
    res = tool_web_search("What is Python?")
    assert "interpreted programming language" in res

def test_web_search_vecesta():
    res = tool_web_search("Vecesta")
    assert "diffusers studios" in res or "open-source" in res

def test_web_search_fallback():
    res = tool_web_search("astronomy mars rover")
    assert "Simulated search results" in res

def test_file_reader_existing(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("Hello from sandbox", encoding="utf-8")
    assert tool_file_reader(str(f)) == "Hello from sandbox"

def test_file_reader_missing():
    with pytest.raises(FileNotFoundError):
        tool_file_reader("missing_9999.txt")

def test_code_executor_safe():
    res = tool_code_executor("a = 10; b = 20; c = a + b")
    assert "Executed cleanly" in res
    assert "'c'" in res

def test_code_executor_syntax_error():
    res = tool_code_executor("def invalid syntax")
    assert "Execution error" in res

def test_file_deleter(tmp_path):
    f = tmp_path / "delete_me.txt"
    f.write_text("temp", encoding="utf-8")
    assert f.exists()
    res = tool_file_deleter(str(f))
    assert "Deleted file" in res
    assert not f.exists()

def test_tool_registry_definitions():
    assert "calculator" in TOOL_REGISTRY
    assert "web_search" in TOOL_REGISTRY
    assert "file_deleter" in TOOL_REGISTRY
    assert TOOL_REGISTRY["file_deleter"]["def"].is_destructive is True
    assert TOOL_REGISTRY["calculator"]["def"].is_destructive is False

# 3. SafeAgentExecutor ReAct Execution Tests
def test_executor_math_goal():
    executor = SafeAgentExecutor()
    trace = executor.run("Please calculate 25 * (4 + 10)")
    assert trace.completed is True
    assert len(trace.steps) >= 2
    assert "350" in trace.final_answer

def test_executor_search_goal():
    executor = SafeAgentExecutor()
    trace = executor.run("Who is Vecesta?")
    assert trace.completed is True
    assert any(s.action_tool == "web_search" for s in trace.steps)
    assert trace.final_answer is not None

def test_executor_dry_run_mode():
    executor = SafeAgentExecutor()
    trace = executor.run("calculate 10 + 10", dry_run=True)
    assert trace.dry_run is True
    assert any(s.status == "dry_run" for s in trace.steps)

def test_executor_approval_gate_denied():
    # Without approval callback, destructive actions are denied
    executor = SafeAgentExecutor(approval_callback=None)
    trace = executor.run("delete the temporary log files")
    assert trace.completed is False
    assert trace.aborted_reason == "Destructive action denied by safety gate."
    assert any(s.status == "denied" for s in trace.steps)

def test_executor_approval_gate_approved(tmp_path):
    f = tmp_path / "temp_cleanup.log"
    f.write_text("dummy", encoding="utf-8")
    
    executor = SafeAgentExecutor(approval_callback=lambda tool, args: True)
    trace = executor.run("delete the temporary log files")
    assert trace.completed is True
    assert any(s.action_tool == "file_deleter" for s in trace.steps)

def test_executor_cycle_detection():
    executor = SafeAgentExecutor(cycle_threshold=3)
    trace = executor.run("infinite loop test", force_cycle=True)
    assert trace.completed is False
    assert "Cycle detected" in trace.aborted_reason
    assert any(s.status == "cycle_detected" for s in trace.steps)

def test_executor_max_steps_boundary():
    executor = SafeAgentExecutor(max_steps=1)
    trace = executor.run("calculate 5 + 5")
    assert len(trace.steps) <= 1

def test_execution_trace_serialization():
    executor = SafeAgentExecutor()
    trace = executor.run("search Python")
    data = trace.model_dump()
    assert "trace_id" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
