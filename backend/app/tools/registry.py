"""
MR.GREEN — Tool Registry

Central registry for discovering, registering, validating, enabling/disabling,
and querying tools dynamically.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from app.tools.base import BaseTool
from app.tools.manifest import ToolManifest
from app.tools.permissions import permission_engine

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all available tools in MR.GREEN.

    Manages tool lifecycle:
    - Discovery of built-in tools
    - Dynamic registration and unregistration
    - Enable/disable toggles
    - Manifest validation
    - Version tracking
    - Permission checks
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._enabled_overrides: dict[str, bool] = {}

    def validate_manifest(self, manifest_data: dict[str, Any]) -> ToolManifest:
        """Validate a tool manifest dictionary against the specification."""
        return ToolManifest(**manifest_data)

    def register(self, tool: BaseTool, overwrite: bool = True) -> None:
        """
        Register a tool in the registry with manifest and permission validation.
        """
        # 1. Validate manifest
        try:
            manifest = tool.manifest
        except Exception as e:
            raise ValueError(f"Invalid tool manifest for '{tool.name}': {str(e)}")

        # 2. Check for unknown permissions
        invalid_perms = permission_engine.validate_permissions(manifest.permissions)
        if invalid_perms:
            logger.warning(
                "Tool '%s' declares unrecognized permissions: %s",
                tool.name, invalid_perms,
            )

        # 3. Check duplicate prevention
        if tool.name in self._tools and not overwrite:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")

        self._tools[tool.name] = tool
        # Maintain default enabled state unless overridden
        if tool.name not in self._enabled_overrides:
            self._enabled_overrides[tool.name] = manifest.enabled

        logger.info(
            "Registered tool: %s (v%s, risk=%s, enabled=%s)",
            tool.name, manifest.version, manifest.risk_level.value, self.is_enabled(tool.name),
        )

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            self._enabled_overrides.pop(name, None)
            logger.info("Unregistered tool: %s", name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_enabled(self) -> list[BaseTool]:
        """List all currently active/enabled tools."""
        return [tool for tool in self._tools.values() if self.is_enabled(tool.name)]

    def is_enabled(self, name: str) -> bool:
        """Check if a tool is enabled."""
        if name not in self._tools:
            return False
        return self._enabled_overrides.get(name, self._tools[name].enabled)

    def enable(self, name: str) -> bool:
        """Enable a tool."""
        if name not in self._tools:
            return False
        self._enabled_overrides[name] = True
        tool = self._tools[name]
        if hasattr(tool, "set_enabled"):
            tool.set_enabled(True)
        logger.info("Enabled tool: %s", name)
        return True

    def disable(self, name: str) -> bool:
        """Disable a tool."""
        if name not in self._tools:
            return False
        self._enabled_overrides[name] = False
        tool = self._tools[name]
        if hasattr(tool, "set_enabled"):
            tool.set_enabled(False)
        logger.info("Disabled tool: %s", name)
        return True

    def get_tool_metadata(self, name: str) -> dict[str, Any] | None:
        """Return full metadata for a registered tool."""
        tool = self.get(name)
        if not tool:
            return None
        data = tool.to_dict()
        data["enabled"] = self.is_enabled(name)
        return data

    def get_tools_for_ai(self) -> list[dict[str, Any]]:
        """
        Get sanitized descriptions of only enabled tools formatted for AI prompt/context.
        """
        result = []
        for tool in self.list_enabled():
            result.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "risk_level": tool.risk_level,
            })
        return result

    def discover_builtins(self) -> None:
        """Automatically register all core built-in tools."""
        from app.tools.builtins import (
            CalculatorTool,
            FileReadTool,
            FileWriteTool,
            ShellTool,
            TimeTool,
            WebFetchTool,
        )

        builtins = [
            CalculatorTool(),
            TimeTool(),
            FileReadTool(),
            FileWriteTool(),
            WebFetchTool(),
            ShellTool(initially_enabled=False),
        ]

        for t in builtins:
            self.register(t, overwrite=True)

    async def sync_to_db(self, session: AsyncSession) -> None:
        """
        Synchronize registered tools, versions, and permissions into database tables.
        """
        from datetime import datetime, timezone
        from sqlalchemy import select
        from app.database.models import ToolPermissionRecord, ToolRecord, ToolVersion

        for tool in self.list_all():
            manifest = tool.manifest

            result = await session.execute(
                select(ToolRecord).where(ToolRecord.name == tool.name)
            )
            record = result.scalar_one_or_none()

            if record is None:
                record = ToolRecord(
                    id=str(ULID()),
                    name=tool.name,
                    description=tool.description,
                    category=tool.category,
                    version=tool.version,
                    input_schema=tool.input_schema,
                    permissions=tool.permissions,
                    risk_level=tool.risk_level,
                    requires_approval=tool.requires_approval,
                    is_builtin=True,
                    is_enabled=self.is_enabled(tool.name),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(record)
                await session.flush()

                # Add initial version
                version_record = ToolVersion(
                    id=str(ULID()),
                    tool_id=record.id,
                    version=tool.version,
                    manifest=manifest.to_dict(),
                    status="active",
                    created_at=datetime.now(timezone.utc),
                )
                session.add(version_record)
            else:
                # Update existing record
                record.description = tool.description
                record.category = tool.category
                record.version = tool.version
                record.input_schema = tool.input_schema
                record.permissions = tool.permissions
                record.risk_level = tool.risk_level
                record.requires_approval = tool.requires_approval
                record.is_enabled = self.is_enabled(tool.name)
                record.updated_at = datetime.now(timezone.utc)

            # Sync tool permissions
            for perm in tool.permissions:
                perm_res = await session.execute(
                    select(ToolPermissionRecord).where(
                        ToolPermissionRecord.tool_name == tool.name,
                        ToolPermissionRecord.permission == perm,
                    )
                )
                if not perm_res.scalar_one_or_none():
                    session.add(ToolPermissionRecord(
                        id=str(ULID()),
                        tool_name=tool.name,
                        permission=perm,
                        allowed=True,
                        requires_approval=tool.requires_approval,
                    ))

        await session.commit()

    def list(self) -> Any:
        """Alias for list_all."""
        return self.list_all()

    @property
    def count(self) -> int:
        return len(self._tools)


# Global tool registry instance
tool_registry = ToolRegistry()
tool_registry.discover_builtins()
