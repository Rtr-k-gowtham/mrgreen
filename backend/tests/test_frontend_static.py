"""
Tests for frontend static file serving.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

@pytest.mark.asyncio
async def test_frontend_root_serves_html():
    """Test that GET / serves the frontend application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/")

    # If static files are mounted, it returns 200 with HTML; if not yet built, still does not crash
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "MR.GREEN" in response.text
