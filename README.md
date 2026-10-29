# safe-agent-executor

> **Guarded ReAct agent execution engine with infinite cycle detection, human-in-the-loop approval gates for destructive tools, and deterministic dry-run simulations.**

[![CI](https://github.com/Vecesta-co/safe-agent-executor/actions/workflows/ci.yml/badge.svg)](https://github.com/Vecesta-co/safe-agent-executor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

```
$ python -m src.cli run "calculate 25 * (4 + 10)"
=== Execution Trace: f1a2b3c4 ===
Goal: calculate 25 * (4 + 10)
Dry Run: False
Completed: True

Steps:
  [1] Thought: I need to evaluate this mathematical calculation.
      Action: calculator({'expr': '25 * (4 + 10)'})
      Obs:    350.0
      Status: success
  [2] Thought: The calculation result is 350.0. Final answer is ready.
      Action: finish({'answer': 'The calculated result is 350.0'})
      Obs:    Execution complete.
      Status: success

Final Answer: The calculated result is 350.0
```

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                        User Goal                       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 ReAct Reasoning Loop                   │
│   Thought ──► Planned Action ──► Observation           │
└──────────────────────────┬─────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
┌───────────────────────┐     ┌────────────────────────┐
│ Cycle Detector        │     │ Safety Approval Gate   │
│ - Aborts if identical │     │ - Halts destructive    │
│   action repeated 3x  │     │   tools (file delete)  │
└───────────────────────┘     └────────────────────────┘
            │                             │
            └──────────────┬──────────────┘
                           │ Approved / Non-destructive
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Tool Sandbox                         │
│  - calculator  - web_search  - file_reader             │
│  - code_executor             - file_deleter            │
└────────────────────────────────────────────────────────┘
```

## Comparison

| Capability | safe-agent-executor | Standard Agent Frameworks |
|---|---|---|
| Infinite Loop Protection | Automated Cycle Detection (3x Repeat Abort) | Often runs until token limit / timeout |
| Destructive Action Gate | Hard Approval Barrier | Unrestricted execution |
| Dry Run Mode | Full simulation without side-effects | Rare / manual mocking required |
| AST Expression Safety | Strict node validation (No `eval()` risk) | Vulnerable Python `eval()` |
| Execution Trace Audit | Structured ISO JSON traces | Ephemeral terminal logs |

## Key Features

- **Cycle Detection**: Automatically prevents infinite repeating loops when agents hallucinate identical calls.
- **Human-in-the-Loop Gate**: Tools flagged with `is_destructive=True` cannot execute without an explicit approval callback.
- **Dry-Run Simulation**: Inspect an agent's reasoning trajectory without mutating files or running stateful tools.
- **REST & CLI Interfaces**: Run via command-line or embed into services using standard HTTP endpoints.

## Quick Start

```bash
git clone https://github.com/Vecesta-co/safe-agent-executor.git
cd safe-agent-executor
pip install pydantic pytest

# Execute a safe math goal:
python -m src.cli run "calculate 100 / 4"

# Simulate execution in dry-run mode:
python -m src.cli run "search Python" --dry-run
```

## Difficulties & Solutions

- **Safe Math Evaluation Without Remote Code Execution**: Evaluating dynamic user math often relies on `eval()`, introducing arbitrary code execution risks. We implemented an AST-based recursive node evaluator permitting only standard arithmetic operators and literal numbers.
- **Deterministic Loop Termination**: Agents frequently get trapped repeating equivalent arguments. Our cycle detection tracks action signature hashes over a sliding window of past turns.

---

**Built by Vecesta.co**
- Email: vecesta.co@gmail.com
- LinkedIn: https://www.linkedin.com/in/vansh-dhawan-2625v
- GitHub: https://github.com/Vecesta-co
- X: https://x.com/Vansh_Dhawann
- Hugging Face: https://huggingface.co/Vecesta
