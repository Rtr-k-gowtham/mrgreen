# File Write Tool

Safely creates or appends text files inside the approved MR.GREEN workspace.

- **Permission**: `filesystem.write`
- **Risk Level**: Medium
- **Safety**: Prevents path traversal (`..`), workspace containment, 1MB per-write limit.
