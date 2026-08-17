"""
Unit Tests for Authentication, JWT Tokens & Role Security (tests/test_auth.py)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from web.app import app
from services.auth_service import AuthService
from services.cache_service import cache_service


@pytest.mark.anyio
async def test_auth_login_and_me_flow():
    """Test login with seeded admin account and profile retrieval."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login with Executive Admin
        resp = await ac.post("/api/auth/login", json={
            "email": "admin@cornerstonerealty.eg",
            "password": "AdminPass123!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        assert data["user"]["role"] == "executive_admin"

        # 2. Access /api/auth/me with Bearer token
        me_resp = await ac.get("/api/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user"]["email"] == "admin@cornerstonerealty.eg"

        # 3. Refresh access token
        ref_resp = await ac.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert ref_resp.status_code == 200
        ref_data = ref_resp.json()
        assert "access_token" in ref_data
        assert ref_data["access_token"] != access_token


@pytest.mark.anyio
async def test_auth_role_protection():
    """Verify role restrictions work properly (e.g. Tenant cannot access Admin Tool Matrix toggle)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login as Tenant
        resp = await ac.post("/api/auth/login", json={
            "email": "tarek.mahdy@cairomed.org",
            "password": "TenantPass123!"
        })
        assert resp.status_code == 200
        tenant_token = resp.json()["access_token"]

        # Attempt to toggle admin tool with Tenant token -> 403 Forbidden
        toggle_resp = await ac.post(
            "/api/admin/agents/commercial_lease_agent/tools/toggle",
            json={"tool_name": "modify_lease_terms", "is_enabled": False},
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert toggle_resp.status_code == 403


@pytest.mark.anyio
async def test_redis_cache_service():
    """Verify cache service set/get/blacklist works in async environment."""
    await cache_service.set("test:key", "val123", expire_seconds=10)
    val = await cache_service.get("test:key")
    assert val == "val123"

    await cache_service.blacklist_token("jti-sample-999", expire_seconds=10)
    assert await cache_service.is_token_blacklisted("jti-sample-999") is True
    assert await cache_service.is_token_blacklisted("jti-sample-valid") is False
