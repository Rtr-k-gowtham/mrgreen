"""
Tests for Human Approvals API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_approvals_api_endpoints():
    """Test approvals listing and response formats using mocked database session."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
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
    finally:
        app.dependency_overrides.pop(get_db_session, None)
