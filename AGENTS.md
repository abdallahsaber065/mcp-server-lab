# Autonomous Agents Lab - Session 2 MCP Server Guidelines

This file (`AGENTS.md`) is the authoritative source of rules, instructions, environment setup, and grading knowledge for any AI coding assistant operating in this repository.

---

## 📌 Executive Summary & Workspace Context
- **Course**: Autonomous Agents & AI Systems Lab — Session 2 (MCP Server Lab)
- **Repository**: `abdallahsaber065/mcp-server-lab`
- **Primary Maintainer / Student**: Abdallah Saber (`abdallahsaber065`)
- **Team**: `Cornerstone Realty Group B`
- **Target Grade**: **100/100** on both Team Deliverable (70%) and Individual Attribution (30%).

---

## ⚙️ Environment & Compiler Constraints (PowerShell 5.1 / Windows)

```yaml
OS: Microsoft Windows 11 Pro (Build 26100)
Shell: Windows PowerShell 5.1
Python Path: "D:\Programming\Compilers\uv\python\bin\python.exe"
Package Managers: Use `uv` (Python) and `pnpm` (Node) exclusively. Do NOT use standard pip/npm unless requested.
Terminal Command Rule: Never use `&&` in commands. Use `;` to chain commands in PowerShell.
Path Separator Rule: Always use forward slashes (`/`) or `os.path.join()` / `Path` objects.
```

---

## 🏆 The 10 Commandments of MCP AI Coding for 100/100 Grading

### 1. Zero-Trust Tool Design & Error Boundaries
- **NEVER** let an uncaught model validation error or database exception crash the MCP server.
- Wrap EVERY tool execution in `try/except` blocks and return structured JSON error payloads.

### 2. Strictly Typed Input Schemas
- Every tool MUST specify typed fields and `extra='forbid'` (equivalent to `additionalProperties: false` in JSON Schema).
- Perform server-side validation using `pydantic` or `jsonschema` before executing tool handlers.

### 3. Capability Negotiation Handshake
- The MCP Client MUST execute `initialize` and verify server capabilities before calling risky tools.

### 4. Real Runtime Notifications
- When user role changes or tool availability changes, push `notifications/tools/list_changed` to client without forcing a reconnect.

### 5. Elicitation for Risky Actions
- Mid-call, risky write operations (e.g. lease signing, refund processing) MUST invoke `elicitation/create` to pause for human approval.

### 6. Sampling via Host Model
- Server reasoning MUST delegate to the host via `sampling/createMessage` rather than calling a direct separate API key.

### 7. Mandatory Executable Test Suites (`tests/`)
- Every tool and protocol concern MUST have runnable unit/integration tests in `tests/`.
- Running `uv run pytest` MUST pass 100% clean.

### 8. Evidence-Based Benchmarks (`benchmarks/`)
- Save raw execution logs and protocol latency metrics in `benchmarks/benchmark_results.json`.

### 9. GitHub Issue Rationale & PR Linking
- Open a GitHub Issue for every protocol concern with problem, constraint, and acceptance criteria.
- Link PRs (`Closes #X`) and assign single owners.

### 10. Definition of Done
A task is NOT complete until:
1. Code runs error-free using `uv`.
2. Executable tests in `tests/` pass 100% clean.
3. No secrets or credentials committed.
4. Git commit history shows attributable conventional commits.
