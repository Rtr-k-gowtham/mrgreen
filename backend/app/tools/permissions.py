"""
MR.GREEN — Permission Engine

Implements strict least-privilege security policies.
Default Policy: DENY.
A tool receives only the permissions explicitly granted in its manifest.
"""

import logging
from typing import Iterable

logger = logging.getLogger(__name__)

# Standard recognized system permissions
STANDARD_PERMISSIONS = frozenset({
    # Filesystem
    "filesystem.read",
    "filesystem.write",

    # Network
    "network.read",
    "network.write",

    # Shell & OS execution
    "shell.read",
    "shell.execute",

    # Database
    "database.read",
    "database.write",

    # Git
    "git.read",
    "git.write",

    # Process management
    "process.read",
    "process.start",
    "process.stop",

    # Container & Docker
    "docker.read",
    "docker.execute",

    # Secrets
    "secret.read",
})

# High-risk permissions that trigger approval or strict gating
CRITICAL_PERMISSIONS = frozenset({
    "shell.execute",
    "process.stop",
    "docker.execute",
    "secret.read",
    "database.write",
})


class PermissionEngine:
    """
    Evaluates and enforces permission policies across tool executions.
    """

    def __init__(self, allowed_permissions: Iterable[str] | None = None) -> None:
        # If allowed_permissions is provided, only those permissions can be granted system-wide
        self._allowed_permissions = (
            set(allowed_permissions) if allowed_permissions is not None else set(STANDARD_PERMISSIONS)
        )

    def validate_permissions(self, permissions: list[str]) -> list[str]:
        """
        Verify all requested permissions belong to the recognized set.
        Returns list of invalid permissions (empty if all valid).
        """
        return [p for p in permissions if p not in STANDARD_PERMISSIONS]

    def check_permissions(
        self,
        tool_name: str,
        declared_permissions: list[str],
        required_permissions: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Validate whether declared permissions allow the action.

        Args:
            tool_name: Name of tool.
            declared_permissions: Permissions declared in the tool's manifest.
            required_permissions: Specific permissions needed for this operation.

        Returns:
            Tuple of (is_allowed, denial_reason).
        """
        targets = required_permissions if required_permissions is not None else declared_permissions

        for perm in targets:
            # 1. Must be declared by tool
            if perm not in declared_permissions:
                msg = f"Permission denied for '{tool_name}': '{perm}' not declared in manifest."
                logger.warning(msg)
                return False, msg

            # 2. Must be permitted by system policy
            if perm not in self._allowed_permissions:
                msg = f"System policy denies permission '{perm}' for tool '{tool_name}'."
                logger.warning(msg)
                return False, msg

        return True, None

    def requires_approval(self, permissions: list[str], risk_level: str) -> bool:
        """
        Determine if operation warrants human approval based on permissions and risk level.
        """
        if risk_level in ("high", "critical"):
            return True
        if any(p in CRITICAL_PERMISSIONS for p in permissions):
            return True
        return False


# Global permission engine instance
permission_engine = PermissionEngine()
