"""
MR.GREEN — Security Rules

Defines security policies and permission boundaries.
MR.GREEN must NEVER have unrestricted root access.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Paths that must NEVER be accessed
FORBIDDEN_PATHS = frozenset({
    "/root",
    "/etc/shadow",
    "/etc/passwd",
    "/etc/ssh",
    "/etc/sudoers",
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

# Secrets that must NEVER be exposed
PROTECTED_SECRETS = frozenset({
    "SSH_PRIVATE_KEY",
    "DATABASE_PASSWORD",
    "SECRET_KEY",
    "API_KEY",
    "API_SECRET",
})


@dataclass
class SecurityPolicy:
    """Security policy for MR.GREEN operations."""
    allowed_paths: list[str] = field(default_factory=list)
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_network_targets: list[str] = field(default_factory=list)
    requires_approval_for: set[str] = field(default_factory=lambda: set(DANGEROUS_OPERATIONS))


def is_path_allowed(path: str) -> bool:
    """Check if a file path is allowed."""
    for forbidden in FORBIDDEN_PATHS:
        if path.startswith(forbidden):
            logger.warning("Blocked access to forbidden path: %s", path)
            return False
    return True


def requires_approval(operation: str) -> bool:
    """Check if an operation requires explicit user approval."""
    return operation in DANGEROUS_OPERATIONS
