# File Read Tool

Safely reads files contained strictly inside the designated MR.GREEN workspace.

- **Permission**: `filesystem.read`
- **Risk Level**: Low
- **Safety**: Prevents path traversal (`..`), denies root/system paths and secrets.
