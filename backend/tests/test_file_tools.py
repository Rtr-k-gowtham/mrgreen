"""
Tests for FileReadTool and FileWriteTool with path traversal security.
"""

import pytest
from app.sandbox.security import is_path_safe
from app.tools.builtins.file_read.tool import FileReadTool
from app.tools.builtins.file_write.tool import FileWriteTool


@pytest.mark.asyncio
async def test_file_write_and_read(tmp_path):
    """Test writing and reading a file in approved workspace."""
    write_tool = FileWriteTool()
    read_tool = FileReadTool()

    # Write file
    write_res = await write_tool.execute(
        path="test_note.txt",
        content="Hello MR.GREEN",
        mode="write",
    )
    assert write_res.success is True
    assert write_res.output["bytes_written"] > 0

    # Read file
    read_res = await read_tool.execute(path="test_note.txt")
    assert read_res.success is True
    assert "Hello MR.GREEN" in read_res.output["content"]


@pytest.mark.asyncio
async def test_path_traversal_blocked():
    """Test that ../ path traversal attempts are blocked."""
    read_tool = FileReadTool()
    res = await read_tool.execute(path="../../../etc/passwd")
    assert res.success is False
    assert "traversal" in res.error.lower() or "blocked" in res.error.lower()

    write_tool = FileWriteTool()
    res_w = await write_tool.execute(path="../escaped.txt", content="danger")
    assert res_w.success is False
    assert "traversal" in res_w.error.lower() or "blocked" in res_w.error.lower()


@pytest.mark.asyncio
async def test_forbidden_files_blocked():
    """Test accessing sensitive files (.env, keys) is blocked."""
    read_tool = FileReadTool()
    res = await read_tool.execute(path=".env")
    assert res.success is False
    assert "blocked" in res.error.lower()


@pytest.mark.asyncio
async def test_missing_file():
    """Test reading a non-existent file."""
    read_tool = FileReadTool()
    res = await read_tool.execute(path="non_existent_file_xyz_123.txt")
    assert res.success is False
    assert "not found" in res.error.lower()
