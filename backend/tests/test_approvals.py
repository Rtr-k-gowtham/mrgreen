"""
Tests for Human Approvals API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_approvals_api_endpoints():
    """Test approvals listing and response formats."""
    from app.database.session import init_db
    try:
        await init_db()
    except Exception:
        pass

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # GET /api/approvals
        resp = await client.get("/api/approvals?status=pending")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # GET /api/approvals with invalid status
        bad_resp = await client.get("/api/approvals?status=invalid_status")
        assert bad_resp.status_code == 400
