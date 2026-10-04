"""
Tests for WebFetchTool and SSRF Protection.
"""

import pytest
from app.sandbox.security import is_safe_url
from app.tools.builtins.web_fetch.tool import WebFetchTool


def test_ssrf_protection_localhost_blocked():
    """Test localhost, 127.0.0.1, and private IPs are blocked."""
    assert is_safe_url("http://localhost:8000/api")[0] is False
    assert is_safe_url("http://127.0.0.1:11434")[0] is False
    assert is_safe_url("http://0.0.0.0:80")[0] is False
    assert is_safe_url("http://192.168.1.1/admin")[0] is False
    assert is_safe_url("http://10.0.0.1/secrets")[0] is False
    assert is_safe_url("http://172.16.0.1/internal")[0] is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/")[0] is False


def test_ssrf_scheme_validation():
    """Test non-http(s) schemes are rejected."""
    assert is_safe_url("file:///etc/passwd")[0] is False
    assert is_safe_url("ftp://ftp.example.com")[0] is False
    assert is_safe_url("gopher://example.com")[0] is False


@pytest.mark.asyncio
async def test_web_fetch_ssrf_rejection():
    """Test WebFetchTool rejects internal addresses."""
    tool = WebFetchTool()
    res = await tool.execute(url="http://127.0.0.1:8000/health")
    assert res.success is False
    assert "SSRF" in res.error or "blocked" in res.error.lower()


@pytest.mark.asyncio
async def test_web_fetch_missing_url():
    """Test WebFetchTool requires URL parameter."""
    tool = WebFetchTool()
    res = await tool.execute()
    assert res.success is False
    assert "url" in res.error.lower()
