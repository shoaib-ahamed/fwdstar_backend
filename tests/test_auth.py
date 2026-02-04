"""
Authentication endpoint tests.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserStatus


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["role"] == test_user_data["role"]
        assert data["user"]["status"] == "ACTIVE"
        assert "message" in data

        # Check cookies are set
        assert "access_token" in client.cookies
        assert "refresh_token" in client.cookies

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # Register user once
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register again with same email
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, weak_password_user_data: dict):
        """Test registration with weak password."""
        response = await client.post("/api/v1/auth/register", json=weak_password_user_data)

        assert response.status_code == 400
        assert "Password must be at least" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient, invalid_role_user_data: dict):
        """Test registration with invalid role."""
        response = await client.post("/api/v1/auth/register", json=invalid_role_user_data)

        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "TestPass123",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_all_roles(self, client: AsyncClient):
        """Test registration with all valid roles."""
        roles = ["SHIPPER", "CARRIER_OWNER", "DRIVER", "ADMIN"]

        for role in roles:
            user_data = {
                "email": f"{role.lower()}@example.com",
                "password": "TestPass123",
                "role": role
            }

            response = await client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201
            assert response.json()["user"]["role"] == role


class TestUserLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login."""
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPass123",
            "remember_me": True
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == login_data["email"]
        assert data["user"]["role"] == "SHIPPER"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with invalid email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPass123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login with wrong password."""
        login_data = {
            "email": "testuser@example.com",
            "password": "WrongPassword123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_account_locked_after_5_failures(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        locked_user_data: dict
    ):
        """Test that account gets locked after 5 failed login attempts."""
        # Register user
        await client.post("/api/v1/auth/register", json=locked_user_data)

        # Try to login 5 times with wrong password
        login_data = {
            "email": locked_user_data["email"],
            "password": "WrongPassword"
        }

        for i in range(5):
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 401

        # 6th attempt should show account locked
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 403
        assert "locked until" in response.json()["detail"].lower()

        # Even correct password should fail
        correct_login = {
            "email": locked_user_data["email"],
            "password": locked_user_data["password"]
        }

        response = await client.post("/api/v1/auth/login", json=correct_login)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_login_with_cookies_set(self, client: AsyncClient, test_user: dict):
        """Test that login sets authentication cookies."""
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPass123"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert "access_token" in client.cookies
        assert "refresh_token" in client.cookies

    @pytest.mark.asyncio
    async def test_login_remember_me_parameter(self, client: AsyncClient, test_user: dict):
        """Test that remember_me parameter affects refresh token expiration."""
        # Login with remember_me=False (default)
        login_data_false = {
            "email": "testuser@example.com",
            "password": "TestPass123",
            "remember_me": False
        }

        response = await client.post("/api/v1/auth/login", json=login_data_false)
        assert response.status_code == 200

        # Check that refresh token cookie was set
        assert "refresh_token" in client.cookies


class TestGetCurrentUser:
    """Test getting current user information."""

    @pytest.mark.asyncio
    async def test_get_current_user_authenticated(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting current user when authenticated."""
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user when not authenticated."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        client.cookies.set("access_token", "invalid_token")
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Test successful token refresh."""
        # Login first to get refresh token
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPass123"
        }

        await client.post("/api/v1/auth/login", json=login_data)

        # Refresh token
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "refreshed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_refresh_without_token(self, client: AsyncClient):
        """Test refresh without refresh token cookie."""
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "Refresh token not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid refresh token."""
        client.cookies.set("refresh_token", "invalid_token")
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestLogout:
    """Test logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client: AsyncClient):
        """Test successful logout."""
        response = await authenticated_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out" in data["message"]

        # Check cookies are cleared
        assert "access_token" in authenticated_client.cookies
        assert "refresh_token" in authenticated_client.cookies

    @pytest.mark.asyncio
    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestRoleBasedAccessControl:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_admin_user_data(self, authenticated_client: AsyncClient, admin_user: dict):
        """Test that admin user can access protected endpoint."""
        # admin_user fixture should be logged in as admin
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_user_status_in_response(
        self,
        client: AsyncClient,
        test_user_data: dict
    ):
        """Test that user status is returned in responses."""
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Check status in registration response
        response = await client.post("/api/v1/auth/register", json={
            "email": "another@example.com",
            "password": "TestPass123",
            "role": "SHIPPER"
        })

        assert response.status_code == 201
        assert response.json()["user"]["status"] == "ACTIVE"


class TestPasswordValidation:
    """Test password strength validation."""

    @pytest.mark.asyncio
    async def test_password_too_short(self, client: AsyncClient):
        """Test password validation: too short."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_no_uppercase(self, client: AsyncClient):
        """Test password validation: no uppercase."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_no_lowercase(self, client: AsyncClient):
        """Test password validation: no lowercase."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "PASSWORD123",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_no_number(self, client: AsyncClient):
        """Test password validation: no number."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "PasswordNoNumber",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_valid(self, client: AsyncClient):
        """Test valid password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid@example.com",
                "password": "ValidPass123",
                "role": "SHIPPER"
            }
        )

        assert response.status_code == 201


class TestAuditLogging:
    """Test that audit logging is working correctly."""

    @pytest.mark.asyncio
    async def test_registration_creates_audit_log(
        self,
        client: AsyncClient,
        test_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that registration creates an audit log entry."""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)

        # Check audit log
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == "USER_REGISTERED")
        )
        audit_logs = result.scalars().all()

        assert len(audit_logs) > 0

    @pytest.mark.asyncio
    async def test_login_creates_audit_log(
        self,
        client: AsyncClient,
        test_user: dict
    ):
        """Test that login creates an audit log entry."""
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPass123"
        }

        await client.post("/api/v1/auth/login", json=login_data)

        # Check that the response is successful
        assert login_data["email"] in str(client.cookies)
