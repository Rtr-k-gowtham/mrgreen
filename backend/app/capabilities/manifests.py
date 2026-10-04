"""
MR.GREEN — Capability Manifests

Handles loading and parsing capability manifest files.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CapabilityManifest:
    """Parsed capability manifest."""
    name: str
    version: str
    description: str
    permissions: list[str] = field(default_factory=list)
    requires_approval: bool = True
    entry_point: str = "tool.py"
    dependencies: list[str] = field(default_factory=list)


def load_manifest(manifest_path: str | Path) -> CapabilityManifest | None:
    """Load a capability manifest from a JSON file."""
    path = Path(manifest_path)
    if not path.exists():
        logger.warning("Manifest not found: %s", path)
        return None

    try:
        with open(path) as f:
            data = json.load(f)

        return CapabilityManifest(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            permissions=data.get("permissions", []),
            requires_approval=data.get("requires_approval", True),
            entry_point=data.get("entry_point", "tool.py"),
            dependencies=data.get("dependencies", []),
        )
    except Exception as e:
        logger.error("Failed to load manifest %s: %s", path, str(e))
        return None
