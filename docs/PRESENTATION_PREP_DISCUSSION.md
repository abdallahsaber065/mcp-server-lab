# 🏢 Cornerstone Realty Group — MCP Server Project Presentation & Viva Defense Master Guide

---

## 🎯 Executive Overview & Presentation Strategy

This document is your complete preparation guide for presenting and defending the **Cornerstone Realty Group Model Context Protocol (MCP) Server** project. It is structured around the official lab rubric, the MCP specification, database architecture, and real-world production engineering decisions.

---

## 📖 Section 1: Presentation Story & Narrative Script

### 1.1 The Setup (Who We Are & The Problem We Faced)
> **Presenter Narrative**:
> *"Good morning/afternoon. We are engineers at **Cornerstone Realty Group**, a commercial and residential property management firm handling hundreds of apartments and lease agreements across major cities.
> 
> Before building this system, property managers and support staff had to manually query leasing records, search maintenance tickets, and calculate rent adjustments. When company leadership suggested connecting Large Language Models (LLMs) to automate these workflows, the naive approach was to give an LLM raw SQL access or a direct shell runner to query our production database.
> 
> **Why that naive version is dangerous in production:**
> 1. **Prompt Injection & Data Destruction**: A malicious user or malformed prompt could trick the LLM into generating `DROP TABLE leases;` or `UPDATE units SET monthly_rent = 0;`.
> 2. **Hallucinated SQL & Full-Table Scans**: LLMs frequently generate invalid SQL syntax, invent non-existent column names, or issue unindexed full-table scans that freeze the database.
> 3. **Lack of Authorization & Audit Trails**: Raw SQL bypassing business logic means there are zero audit logs, zero role-based access checks, and no way to require executive sign-off for sensitive operations like rent modifications."*

---

### 1.2 The Solution: Scoped MCP Business Operations
> **Presenter Narrative**:
> *"Instead of exposing raw database connections or command execution tools, we built a **Model Context Protocol (MCP) Server**.
> 
> MCP acts as a secure, standardized abstraction layer—much like **USB-C for AI tools**. The LLM never touches SQL or infrastructure directly. Instead, the MCP server exposes **strict business operations** (such as `lookup_available_units`, `get_tenant_lease`, `submit_maintenance_request`, `modify_lease_terms`).
> 
> Every tool enforces server-side argument validation, parameterized SQL queries, strict Pydantic schemas with `extra='forbid'`, and role authorization inside the handler."*

---

## 🗄️ Section 2: Database Schema & ERD Architecture

```
+------------------+       +------------------+       +-------------------------+
|    PROPERTIES    |       |      UNITS       |       |         LEASES          |
+------------------+       +------------------+       +-------------------------+
| property_id (PK) |<----->| unit_id (PK)     |<----->| lease_id (PK)           |
| name             | 1   N | property_id (FK) | 1   N | unit_id (FK)            |
| address          |       | unit_number      |       | tenant_id (FK)          |
| city             |       | bedrooms         |       | start_date, end_date    |
| total_units      |       | monthly_rent     |       | monthly_rent            |
+------------------+       | is_available     |       | status                  |
                           +------------------+       +-------------------------+
                                                                  ^
                                                                  | 1
                                                                  | N
+-------------------------+                           +-------------------------+
|  MAINTENANCE_REQUESTS   |                           |         TENANTS         |
+-------------------------+                           +-------------------------+
| request_id (PK)         |                           | tenant_id (PK)          |
| unit_id (FK)            |<--------------------------| full_name, email, phone |
| tenant_id (FK)          |                           | role (tenant/manager)   |
| priority, status        |                           +-------------------------+
+-------------------------+
```

### Table Structure Summary:
1. **`properties`**: Physical real estate buildings (`property_id`, `name`, `address`, `city`, `total_units`).
2. **`units`**: Individual apartments (`unit_id`, `property_id`, `unit_number`, `bedrooms`, `monthly_rent`, `is_available`).
3. **`tenants`**: Registered users and staff (`tenant_id`, `full_name`, `email`, `phone`, `role`).
4. **`leases`**: Active and historic lease agreements (`lease_id`, `unit_id`, `tenant_id`, `start_date`, `end_date`, `monthly_rent`, `status`).
5. **`maintenance_requests`**: Property maintenance tickets (`request_id`, `unit_id`, `tenant_id`, `description`, `priority`, `status`).
6. **`chat_sessions` & `chat_messages`**: Production persistent logging of agent chats, tool traces, and human elicitation responses in SQLite.

---

## 🔌 Section 3: Deep Dive into All 8 Protocol Concerns

### 1. Capability Negotiation (`initialize` exchange)
- **Concept**: The server and client perform a formal JSON-RPC 2.0 handshake (`initialize` -> `result` -> `notifications/initialized`).
- **Implementation**: The server explicitly advertises capabilities: `{"capabilities": {"tools": {"listChanged": True}, "resources": {}, "prompts": {}, "elicitation": {}}}`.
- **Why it matters**: Clients check capability support before attempting high-risk operations (e.g. falling back to read-only mode if the client cannot handle human elicitation).

### 2. Notifications (`notifications/tools/list_changed`)
- **Concept**: Tool availability is dynamic at runtime based on session authorization or role elevation without closing the connection.
- **Implementation**: When a user switches role (e.g., from `tenant` to `executive_admin`), the server pushes `notifications/tools/list_changed`.
- **Why it matters**: Prevents polling and guarantees immediate client tool registry updates when privileges change.

### 3. Human Elicitation (`elicitation/create`)
- **Concept**: Pauses tool execution mid-call to ask a human operator for explicit confirmation before mutating database state.
- **Implementation**: In `modify_lease_terms`, if the proposed rent change exceeds threshold or changes lease terms, execution returns `status: "elicitation_required"` with an interactive sign-off payload (`lease_id`, `proposed_rent`, `approved`).
- **Why it matters**: Prevents AI hallucination from making unauthorized monetary or contractual changes without human executive sign-off.

### 4. Resources (`resources/list` & `resources/read`)
- **Concept**: Static domain data (policy manuals, lease terms) exposed as read-only documents rather than wrapped inside tools.
- **Implementation**: Exposed via URI `realty://policies/lease_terms`.
- **Why it matters**: The LLM fetches the document once to inspect rules and constraints instead of invoking repetitive tool functions.

### 5. Parameterized Prompts (`prompts/list` & `prompts/get`)
- **Concept**: Pre-engineered server-side prompt templates for common user tasks.
- **Implementation**: `draft_maintenance_report` and `summarize_lease_agreement`.
- **Why it matters**: Standardizes AI outputs across teams and prevents prompt engineering duplication.

### 6. Progress Tracking (`progressToken`)
- **Concept**: Long-running background operations issue intermediate progress notifications.
- **Implementation**: Multi-property analytics or batch inspection lookups report progress percentages (`25%`, `50%`, `75%`, `100%`) back to the client host.
- **Why it matters**: Keeps the UI responsive and prevents timeout errors during intensive lookups.

### 7. Defensive Tool Design (`extra='forbid'`, Schema Validation, Authorization)
- **Concept**: Never trust model-generated arguments.
- **Implementation**: Server-side Pydantic validation with `extra='forbid'`, strict string/int typing, required fields, and handler-level role verification (`property_manager` vs `tenant`).
- **Why it matters**: Rejects malformed JSON, unexpected parameters, or privilege escalation attempts before touching SQL queries.

### 8. Transport Layer Transition (stdio -> Streamable HTTP)
- **Concept**: Transport abstraction separating data layer logic from transmission channels.
- **Implementation**: Developed locally using standard `stdio` transport, then transitioned to remote `Streamable HTTP` (FastAPI + Server-Sent Events SSE) for production multi-tenant web deployment.

---

## ❓ Section 4: 20 Expected Viva & Presentation Questions (with Master Answers)

### Q1: Why use MCP instead of direct function calling or raw SQL execution?
> **Answer**: Direct function calling or raw SQL forces the LLM to write arbitrary code or SQL queries, leading to SQL injection, table drops, unindexed scans, and zero role-based access control. MCP decouples data semantics from transport, exposing strict, pre-validated business operations (`lookup_available_units`, `modify_lease_terms`) protected by server-side Pydantic schemas, parameterized queries, and authorization checks.

### Q2: What is the difference between the Data Layer and the Transport Layer in MCP?
> **Answer**: The **Data Layer** defines message structure and semantics using JSON-RPC 2.0 (capabilities, `initialize`, `tools/call`, `elicitation`, `resources`). It is completely independent of how messages travel. The **Transport Layer** defines how messages are physically transmitted (`stdio` for local child processes vs `Streamable HTTP / SSE` for remote cloud services).

### Q3: How does Capability Negotiation work in your initialize handshake?
> **Answer**: During the initial connection, the client sends an `initialize` request with its supported features. The server responds with its declared capabilities (e.g. `listChanged: true`, `elicitation: {}`). The client must verify these capabilities before invoking tools that depend on them.

### Q4: How does `notifications/tools/list_changed` work when a user role changes?
> **Answer**: When a user changes roles from `tenant` to `executive_admin`, the tool authorization scope changes. Rather than making the client poll or disconnect, the server pushes `notifications/tools/list_changed`. The client catches this SSE notification and re-fetches `tools/list` to display newly authorized tools seamlessly.

### Q5: How does Elicitation (`elicitation/create`) protect the business from risky AI actions?
> **Answer**: Risky actions like updating monthly rent or modifying lease agreements pause execution mid-call when triggered. The server returns `elicitation_required` with an approval payload. The execution remains gated until a human executive explicitly clicks Approve or Deny.

### Q6: Why expose lease policy documents as Resources instead of Tools?
> **Answer**: Policy manuals are static, read-only reference data. Modeling them as a Resource (`realty://policies/lease_terms`) allows the LLM to fetch the text once and reason over it natively, avoiding repetitive tool function call overhead and state mutations.

### Q7: What defensive measures did you implement on tool input schemas?
> **Answer**: We used Pydantic models with `extra='forbid'`, explicit field types (`int`, `float`, `str`), required parameters, range limits, and server-side `jsonschema` verification. Even if an LLM sends extra unknown arguments, the server rejects them immediately.

### Q8: How are SQL queries safe from injection in your database helpers?
> **Answer**: All database interactions in `db_helpers.py` use parameterized SQL queries (`SELECT ... WHERE city = ?`). Arguments are passed separately from SQL command strings, preventing user input or LLM text from executing as SQL code.

### Q9: How do you handle multi-turn chat history without losing tool execution context?
> **Answer**: All chat events—including user messages, assistant tokens, tool call parameters, tool output results, and elicitation responses—are stored in SQLite table `chat_messages` under `session_id`. When a session is loaded, the backend reconstitutes the full conversation trace and tool cards in exact chronological order.

### Q10: How does Streamable HTTP (SSE) streaming work in your FastAPI backend?
> **Answer**: The client sends a POST request to `/api/chat/stream`. The server streams Server-Sent Events (`text/event-stream`). As LiteLLM generates response chunks, the backend yields SSE events (`type: "token"`, `type: "tool_call"`, `type: "done"`), allowing the frontend to render text and collapsible tool cards in real time.

### Q11: What happens if an external LLM API fails or times out during tool calling?
> **Answer**: The execution loop is wrapped in defensive `try/except` blocks. If an API call fails, the engine catches the exception, logs the error, and returns a structured fallback response (`status: "fallback_executed"`) to prevent server crashes.

### Q12: Why did you choose SQLite for chat history and property records?
> **Answer**: SQLite provides zero-config, embedded, ACID-compliant persistence suitable for standalone MCP deployments. To prevent test runs from wiping main production records, our pytest suite uses an isolated `tmp_path` database fixture (`MCP_DB_FILE`).

### Q13: What is the benefit of parameterized Prompts in MCP?
> **Answer**: Prompts like `draft_maintenance_report` provide standardized templates for host applications. Instead of users writing custom prompts, host applications fetch server-defined templates populated with parameters like `unit_id` or `issue_description`.

### Q14: How does Progress Tracking work for long operations?
> **Answer**: Long-running operations accept a `progressToken`. During execution, the server emits `notifications/progress` updates containing `progress` and `total` count.

### Q15: How do you enforce role-based access control (RBAC) at the tool handler level?
> **Answer**: When `list_tools(role)` or `call_tool(name, args, role)` is executed, the server checks the user's active role. If a `tenant` attempts to call `modify_lease_terms`, the handler rejects the request with a permission error.

### Q16: How did you optimize Docker builds in CI/CD?
> **Answer**: We configured GitHub Actions workflow (`.github/workflows/deploy.yml`) with Docker Buildx and GitHub Actions layer caching (`cache-from: type=gha`, `cache-to: type=gha,mode=max`). This caches OS packages and `uv` virtual environments across workflow runs.

### Q17: Why deploy the application via GitHub Container Registry (GHCR)?
> **Answer**: Building the Docker image on GitHub Actions runners and pushing to GHCR (`ghcr.io`) offloads CPU and memory compilation from the production VPS. The server simply executes `docker compose pull && docker compose up -d`.

### Q18: How does Caddy reverse-proxy SSL traffic to your Docker container?
> **Answer**: Caddy runs in a Docker container connected to `caddy_net`. It routes HTTPS requests for `mcp-server-lab.abdallahsaber.eu.cc` to container service `mcp_server_lab:8000` while automatically managing Let's Encrypt TLS certificates.

### Q19: What was the Uvicorn 0.0.0.0 binding issue and how was it resolved?
> **Answer**: Uvicorn was initially bound to `127.0.0.1` inside the container, restricting sockets to the internal container loopback. Updating `host="0.0.0.0"` in `web/app.py` allowed Uvicorn to listen on all container network interfaces and accept mapped Docker traffic.

### Q20: What are the main production risks if this system scales, and how would you mitigate them?
> **Answer**:
> 1. **SQLite Concurrency**: Replace SQLite with PostgreSQL for high concurrent write throughput.
> 2. **Authentication**: Implement OAuth2 / JWT bearer tokens for remote HTTP SSE transport instead of role dropdown selection.
> 3. **Rate Limiting**: Add Redis-based token bucket rate limiting on tool calls to prevent LLM loops from exhausting system resources.

---

## 📊 Section 5: Scorecard & Rubric Alignment (100/100 Verification)

| Rubric Category | Points | Implementation in Project |
|:---|:---:|:---|
| **Problem Framing & Suitability** | 10 | Real estate leasing domain at Cornerstone Realty Group B. Justifies all 8 protocol concerns. |
| **Database & ERD** | 10 | 5 relational tables (`properties`, `units`, `tenants`, `leases`, `maintenance_requests`) with foreign keys, seed data, and SQLite persistence. |
| **MCP Server & Tool Specs** | 15 | Typed Pydantic schemas, `extra='forbid'`, parameterized SQL queries, handler authorization. |
| **Capability Negotiation** | 5 | `initialize` exchange declaring support for `tools.listChanged`, `elicitation`, `resources`, `prompts`. |
| **Notifications** | 7 | Real-time `notifications/tools/list_changed` push on user role change without reconnecting. |
| **Elicitation** | 5 | Mid-call pause on `modify_lease_terms` requiring executive sign-off before DB mutation. |
| **Sampling / LLM Reasoning** | 8 | Multi-turn LiteLLM reasoning engine supporting LiteLLM models with tool call streaming. |
| **Resources & Prompts** | 5 | Policy resource `realty://policies/lease_terms` & parameterized prompt templates. |
| **Transport Choice** | 5 | Stdio local support + Streamable HTTP (FastAPI + SSE) production deployment behind Caddy SSL. |
| **Progress Tracking** | 5 | Progress token tracking for batch analytics and property reports. |
| **Agent / Client Integration** | 10 | Real-time web UI with persistent SQLite chat history, dynamic direction, and custom collapsible tool cards. |
| **Repository Safety & Usability** | 5 | Reproducible Docker setup, GHA layer caching, GHCR registry, unit test suite (45 passed), no hardcoded secrets. |
| **Total Score** | **100/100** | **Fully Verified** |

---
*Created for internal team presentation and project defense preparation.*
