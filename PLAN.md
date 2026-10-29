# PLAN — safe-agent-executor

## Design & Architecture
1. Define tool schemas with explicit parameter validation and `is_destructive` safety flags.
2. Build ReAct loop driving Thought -> Action -> Observation -> Final Answer sequence.
3. Implement sliding-window cycle detector aborting consecutive identical actions.
4. Construct Human-in-the-Loop approval gate intercepting destructive calls.
5. Create CLI and HTTP REST server with complete trace logging.
6. Verify 20+ tests covering safe AST math, cycles, dry-run, and approvals.
