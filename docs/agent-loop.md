# 🔄 MR.GREEN — Agent Tool Loop

The MR.GREEN agent loop manages understanding, planning, tool selection, sandboxed execution, observation, and verification.

---

## 🔁 Complete Execution Flow

```text
USER REQUEST
     │
     ▼
UNDERSTAND (Memory context loaded from pgvector & short-term buffer)
     │
     ▼
PLAN (Planner evaluates user intent)
     │
     ├─ Simple query? ───────────────────► Direct AI Response
     │
     └─ Needs computation / tool?
              │
              ▼
         SELECT TOOL
              │
              ▼
         VALIDATE INPUT (JSON Schema & Pydantic)
              │
              ▼
         CHECK PERMISSIONS (PermissionEngine, default DENY)
              │
              ▼
         CHECK APPROVAL (Gated if High / Critical Risk)
              │
              ▼
         EXECUTE TOOL (Timeout & Sandbox Manager)
              │
              ▼
         OBSERVE & RECORD (Logged to PostgreSQL tool_calls & agent_steps)
              │
              ▼
         SYNTHESIZE / VERIFY (AI combines observation with answer)
              │
              ▼
         RETURN RESPONSE TO USER
```

---

## 📊 Run Tracking Tables

1. **`agent_runs`**:
   - `id`: ULID
   - `conversation_id`: Target conversation
   - `status`: `running`, `completed`, `failed`, `timeout`
   - `iterations`: Number of cycles executed
   - `started_at` / `completed_at`

2. **`agent_steps`**:
   - `id`: ULID
   - `agent_run_id`: Reference to run
   - `step_number`: Ordered sequence index
   - `action_type`: `plan`, `tool_call`, `respond`
   - `tool_name`: Invoked tool
   - `input_data` / `output_data`
   - `duration_ms`: Execution time
