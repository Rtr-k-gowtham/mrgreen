"""
Tests for PermissionEngine and security policies.
"""

from app.tools.permissions import PermissionEngine


def test_permission_validation():
    """Test validating recognized vs unrecognized permissions."""
    engine = PermissionEngine()
    invalid = engine.validate_permissions(["filesystem.read", "invalid.permission", "hack.system"])
    assert invalid == ["invalid.permission", "hack.system"]

    valid = engine.validate_permissions(["network.read", "filesystem.write"])
    assert len(valid) == 0


def test_permission_check_allowed():
    """Test permission checks when declared in manifest."""
    engine = PermissionEngine()
    allowed, err = engine.check_permissions("test_tool", ["filesystem.read"])
    assert allowed is True
    assert err is None


def test_permission_check_denied():
    """Test permission check fails when required permission is undeclared."""
    engine = PermissionEngine()
    # Tool only declared filesystem.read, but requires filesystem.write
    allowed, err = engine.check_permissions(
        tool_name="test_tool",
        declared_permissions=["filesystem.read"],
        required_permissions=["filesystem.write"],
    )
    assert allowed is False
    assert "filesystem.write" in err


def test_approval_requirement():
    """Test risk level and critical permission gating."""
    engine = PermissionEngine()
    # Low risk, standard read -> auto approve
    assert engine.requires_approval(["filesystem.read"], "low") is False

    # High / Critical risk -> requires approval
    assert engine.requires_approval(["filesystem.read"], "high") is True
    assert engine.requires_approval([], "critical") is True

    # Critical permission -> requires approval regardless of declared risk level
    assert engine.requires_approval(["shell.execute"], "low") is True
