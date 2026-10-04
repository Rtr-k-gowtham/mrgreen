"""
MR.GREEN — Security Engine & Sandbox Rules

Defines security policies, path traversal safeguards, and SSRF network validation.
MR.GREEN operates under strict boundaries with zero unauthorized host access.
"""

import ipaddress
import logging
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from app.config import get_settings

logger = logging.getLogger(__name__)

# Paths that must NEVER be accessed under any circumstances
FORBIDDEN_PATHS = frozenset({
    "/root",
    "/etc",
    "/proc",
    "/sys",
    "/var/run",
    "/boot",
    "C:\\Windows",
    "C:\\Program Files",
})

# Forbidden sensitive filenames & patterns
FORBIDDEN_FILES = frozenset({
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "authorized_keys",
    "known_hosts",
    "shadow",
    "passwd",
    "sudoers",
})

# Operations that ALWAYS require explicit approval
DANGEROUS_OPERATIONS = frozenset({
    "delete_file",
    "modify_system_config",
    "install_package",
    "change_firewall",
    "change_ssh",
    "manage_users",
    "access_secrets",
    "deploy_publicly",
    "send_email",
    "send_message",
    "financial_action",
    "destructive_db_operation",
    "execute_shell_command",
})

# Patterns forbidden in shell commands
BLOCKED_SHELL_COMMANDS = frozenset({
    "rm -rf",
    "sudo",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "chmod -R 777 /",
    "shutdown",
    "reboot",
    "init 0",
    "cat /etc/shadow",
    "cat /etc/passwd",
    "> /dev/sda",
    "wget http",
    "curl http",
})


def get_safe_workspace_root() -> Path:
    """Return the absolute Path to the approved workspace root."""
    settings = get_settings()
    workspace_path = Path(settings.workspace_dir)
    if not workspace_path.is_absolute():
        # Default workspace inside project directory or /opt/mrgreen
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        workspace_path = project_root / settings.workspace_dir
    workspace_path.mkdir(parents=True, exist_ok=True)
    return workspace_path.resolve()


def is_path_safe(requested_path: str | Path, base_dir: Path | None = None) -> tuple[bool, Path | None, str | None]:
    """
    Validate that requested_path is safely contained within base_dir.
    Prevents path traversal (e.g. ../../etc/passwd) and forbidden system access.

    Returns:
        (is_safe, resolved_path, error_message)
    """
    if base_dir is None:
        base_dir = get_safe_workspace_root()
    base_dir = base_dir.resolve()

    raw_path_str = str(requested_path).strip()
    if not raw_path_str:
        return False, None, "Path cannot be empty"

    # Check for null byte injection
    if "\0" in raw_path_str:
        return False, None, "Null bytes not permitted in path"

    try:
        path_obj = Path(raw_path_str)
        # If relative, anchor to base_dir
        if not path_obj.is_absolute():
            resolved = (base_dir / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        # 1. Enforce workspace containment
        try:
            resolved.relative_to(base_dir)
        except ValueError:
            return False, None, f"Path traversal attempt blocked: '{requested_path}' escapes workspace"

        # 2. Check forbidden system paths
        resolved_str = str(resolved)
        for forbidden in FORBIDDEN_PATHS:
            if resolved_str.startswith(forbidden):
                return False, None, f"Access to forbidden system path blocked: '{resolved_str}'"

        # 3. Check forbidden sensitive filenames
        if resolved.name in FORBIDDEN_FILES or resolved.name.startswith(".env"):
            return False, None, f"Access to sensitive file blocked: '{resolved.name}'"

        return True, resolved, None

    except Exception as e:
        return False, None, f"Invalid path resolution: {str(e)}"


def is_safe_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that a URL is safe to fetch (SSRF Protection).
    Blocks private IPs, loopback, link-local, cloud metadata, and non-http(s) schemes.

    Returns:
        (is_safe, error_reason)
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Scheme '{parsed.scheme}' not allowed. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL hostname is missing"

        # Check for localhost / loopback aliases
        lower_host = hostname.lower()
        if lower_host in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"):
            return False, f"Access to private/local host '{hostname}' is blocked."

        # Resolve IP addresses for hostname
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            return False, f"DNS resolution failed for '{hostname}': {str(e)}"

        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_loopback:
                return False, f"URL resolves to loopback IP '{ip_str}', which is blocked."
            if ip_obj.is_private:
                return False, f"URL resolves to private network IP '{ip_str}', which is blocked."
            if ip_obj.is_link_local:
                return False, f"URL resolves to link-local IP '{ip_str}', which is blocked."
            if ip_obj.is_reserved or ip_obj.is_multicast:
                return False, f"URL resolves to reserved/multicast IP '{ip_str}', which is blocked."

            # Specific cloud metadata IP (AWS, GCP, Azure, OpenStack)
            if str(ip_obj) == "169.254.169.254":
                return False, "Access to cloud instance metadata service (169.254.169.254) is strictly prohibited."

        return True, None

    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def is_command_safe(command: str) -> tuple[bool, str | None]:
    """
    Check if a shell command contains dangerous or destructive patterns.
    """
    clean_cmd = command.strip().lower()
    for blocked in BLOCKED_SHELL_COMMANDS:
        if blocked in clean_cmd:
            return False, f"Command contains forbidden pattern: '{blocked}'"

    return True, None


def requires_approval(operation: str, risk_level: str = "low") -> bool:
    """Determine whether an operation requires explicit human approval."""
    if risk_level in ("high", "critical"):
        return True
    return operation in DANGEROUS_OPERATIONS
