# 🛠️ Creating New Tools for MR.GREEN

MR.GREEN is architected so that developers can add new tools and capabilities **without modifying the core agent code**.

---

## 📁 Standard Tool Directory Layout

Place new tools in `capabilities/<tool_name>/` or `backend/app/tools/builtins/<tool_name>/`:

```text
my_tool/
├── manifest.json       # Metadata, permissions, risk level, JSON schema
├── tool.py             # Implementation subclassing BaseTool
├── config.py           # Tool-specific configuration
├── tests/              # Automated unit tests
└── README.md           # Documentation and examples
```

---

## 1. Create `manifest.json`

```json
{
  "name": "currency_converter",
  "version": "1.0.0",
  "description": "Convert currency amounts between USD, EUR, and GBP",
  "category": "utility",
  "permissions": ["network.read"],
  "risk_level": "low",
  "requires_approval": false,
  "enabled": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "amount": { "type": "number", "description": "Amount to convert" },
      "from_currency": { "type": "string", "description": "Source currency (e.g. USD)" },
      "to_currency": { "type": "string", "description": "Target currency (e.g. EUR)" }
    },
    "required": ["amount", "from_currency", "to_currency"]
  }
}
```

---

## 2. Implement `tool.py`

```python
from typing import Any
from app.tools.base import BaseTool, ToolResult

class CurrencyConverterTool(BaseTool):
    @property
    def name(self) -> str:
        return "currency_converter"

    @property
    def description(self) -> str:
        return "Convert currency amounts between USD, EUR, and GBP."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
            },
            "required": ["amount", "from_currency", "to_currency"],
        }

    @property
    def permissions(self) -> list[str]:
        return ["network.read"]

    @property
    def risk_level(self) -> str:
        return "low"

    async def execute(self, **kwargs: Any) -> ToolResult:
        amount = kwargs.get("amount")
        from_curr = kwargs.get("from_currency", "USD").upper()
        to_curr = kwargs.get("to_currency", "EUR").upper()

        # Implementation logic...
        converted = float(amount) * 0.92  # Example rate
        return ToolResult(
            success=True,
            output={"converted_amount": converted, "rate": 0.92},
        )
```

---

## 3. Registering the Tool

Register programmatically in `app.tools.registry`:

```python
from app.tools.registry import tool_registry
from capabilities.currency_converter.tool import CurrencyConverterTool

tool_registry.register(CurrencyConverterTool())
```

Once registered:
- The tool appears in `GET /api/tools`.
- It can be tested directly with `POST /api/tools/currency_converter/execute`.
- MR.GREEN's planner can automatically choose and invoke the tool during conversation.
