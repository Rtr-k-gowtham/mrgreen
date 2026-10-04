# 🔒 MR.GREEN — Security Architecture & Sandbox Rules

MR.GREEN enforces a strict least-privilege security policy. The AI agent operates within controlled boundaries with **zero direct root access** and **default-deny** permissions.

---

## 🛡️ Core Security Principles

1. **Deny by Default**: No tool has access to any system resource unless explicitly granted in its manifest.
2. **Never Execute Raw LLM Output**: LLM outputs are routed through Pydantic validators, permission engines, and approval checks before hitting executors.
3. **No Root Access**: The backend runs as a non-privileged process within Docker.
4. **Secrets Isolation**: Environment variables (`.env`), private SSH keys, and database passwords are blocked from tool reads and prompt exposures.

---

## 🗂️ Permission System

Permissions are granular and explicit:

```text
filesystem.read      filesystem.write
network.read         network.write
shell.read           shell.execute
database.read        database.write
git.read             git.write
process.read         process.start        process.stop
docker.read          docker.execute
secret.read
```

Tools only receive permissions declared in their `manifest.json`.

---

## 🚫 Path Traversal Protection

All filesystem tools (`file_read`, `file_write`) are jailed to the approved workspace root (`workspace/`):
- `../` and absolute paths outside the workspace are blocked.
- Null-byte injections are rejected.
- System directories (`/root`, `/etc`, `/proc`, `/sys`) are strictly forbidden.
- Sensitive files (`.env`, `id_rsa`, `authorized_keys`, `shadow`, `passwd`) cannot be accessed.

---

## 🌐 SSRF (Server-Side Request Forgery) Protection

The `web_fetch` tool validates every URL before sending network traffic:
- **Private Subnets Blocked**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Loopback Blocked**: `127.0.0.0/8`, `localhost`, `::1`.
- **Cloud Metadata Blocked**: `169.254.169.254` (AWS, GCP, Azure metadata services).
- **Protocol Enforced**: Only `http` and `https` allowed (`file://`, `gopher://`, `ftp://` blocked).
- **Redirect Validation**: Followed redirects are re-validated to block open-redirect SSRF bypasses.

---

## 🛑 Human Approval Gating

Risk levels dictate automation:
- **`LOW`**: Automated execution (e.g. calculator, time, read public file).
- **`MEDIUM`**: Automated according to workspace policies.
- **`HIGH` / `CRITICAL`**: **Mandatory human operator approval**.

When a high-risk tool is triggered:
1. Tool execution pauses immediately.
2. A pending record is written to the `approvals` table.
3. The operator approves or denies via `POST /api/approvals/{id}/approve` or `POST /api/approvals/{id}/reject`.
4. The LLM cannot forge approval flags.
