# 🛠️ MR.GREEN — Universal Tool Engine & Registry

MR.GREEN Milestone 2 transforms the platform from a conversational chatbot into an autonomous **AI Agent** equipped with a universal, pluggable Tool Engine.

---

## 🏗️ Architecture

```text
                     MR.GREEN
                         │
                         ▼
                  ┌─────────────┐
                  │ AI Planner  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │Tool Registry│
                  └──────┬──────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   Calculator        File Tools        Web Fetch
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  ┌─────────────┐
                  │  Executor   │
                  └──────┬──────┘
                         │
                         ▼
                 Permission Engine
                         │
                         ▼
                  Security Sandbox
                         │
                         ▼
                    Tool Result
                         │
                         ▼
                      Agent
```

---

## 📦 Built-in Tools (Milestone 2)

| Tool Name | Category | Permissions | Risk Level | Default State | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`calculator`** | `math` | *None* | `low` | Enabled | Safe AST-based mathematical evaluation (No `eval()`). |
| **`time`** | `system` | *None* | `low` | Enabled | Current server, UTC, and localized date/time. |
| **`file_read`** | `filesystem` | `filesystem.read` | `low` | Enabled | Read files safely inside the designated workspace. |
| **`file_write`** | `filesystem` | `filesystem.write` | `medium` | Enabled | Write or append files inside workspace with traversal prevention. |
| **`web_fetch`** | `network` | `network.read` | `medium` | Enabled | Fetch public webpages with full SSRF protection. |
| **`shell`** | `shell` | `shell.execute` | `critical` | **Disabled** | Sandboxed shell command execution with strict approval. |

---

## 🔌 Tool Specification

Every tool conforms to `app.tools.base.BaseTool`:

```python
from app.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something useful"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"arg": {"type": "string"}},
            "required": ["arg"]
        }

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output={"status": "done"})
```

---

## 🌐 API Reference

### 1. List Available Tools
```http
GET /api/tools
```
Returns metadata for all registered tools, their schemas, permissions, risk levels, and enabled states.

### 2. Get Single Tool
```http
GET /api/tools/{tool_name}
```

### 3. Execute Tool Directly
```http
POST /api/tools/{tool_name}/execute
Content-Type: application/json

{
  "arguments": {
    "expression": "25 * 4"
  }
}
```

### 4. Enable / Disable Tools
```http
POST /api/tools/{tool_name}/enable
POST /api/tools/{tool_name}/disable
```

### 5. Audit History
```http
GET /api/tool-calls?limit=50
```
Returns persistent execution records from PostgreSQL including inputs, outputs, execution status, and duration.
