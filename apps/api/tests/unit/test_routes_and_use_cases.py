from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.domain.entities.organization import Organization
from app.domain.entities.user import User
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ForbiddenError
from app.main import create_app
from app.presentation.dependencies import (
    get_create_org_use_case,
    get_create_user_use_case,
    get_db,
    get_get_org_use_case,
    get_get_user_use_case,
    get_list_orgs_use_case,
    get_update_org_use_case,
    get_update_user_use_case,
)
from app.presentation.middleware.auth import require_user_id
from app.presentation.middleware.rbac import require_org_role
from app.presentation.routes.auth import get_auth_service


def make_mock_user(user_id=None, email="test@test.com", name="Test User", password_hash="hash"):
    return User(
        id=user_id or uuid4(),
        email=email,
        name=name,
        avatar_url=None,
        password_hash=password_hash,
        is_active=True,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )


def make_mock_org(org_id=None, name="Test Org", slug="test-org"):
    return Organization(
        id=org_id or uuid4(),
        name=name,
        slug=slug,
        plan_tier="free",
        settings={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def mock_user_id():
    return uuid4()


@pytest.fixture
def override_auth(app: FastAPI, mock_user_id):
    async def _override():
        return mock_user_id
    app.dependency_overrides[require_user_id] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_rbac(app: FastAPI):
    async def _override(org_id, minimum_role="viewer", user_id=None, db=None):
        return MagicMock()
    app.dependency_overrides[require_org_role] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_db(app: FastAPI):
    mock_db = AsyncMock()
    async def _override():
        yield mock_db
    app.dependency_overrides[get_db] = _override
    yield mock_db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _setup_csrf(client: AsyncClient) -> dict[str, str]:
    import hashlib
    import hmac
    import secrets
    import time

    from app.config import config
    secret = config.secret_key
    session_id = secrets.token_urlsafe(16)
    timestamp = int(time.time())
    msg = f"{session_id}:{timestamp}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    csrf_token = f"{timestamp}:{signature}"
    client.headers["Cookie"] = f"astra_csrf={csrf_token}; astra_session={session_id}"
    return {"X-CSRF-Token": csrf_token}


class TestAuthSignupSignin:
    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient, app: FastAPI):
        user = make_mock_user()
        mock_service = AsyncMock()
        mock_service.sign_up = AsyncMock(return_value={
            "access_token": "token123",
            "refresh_token": "refresh123",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        })

        async def _override():
            return mock_service
        app.dependency_overrides[get_auth_service] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/auth/signup", json={
            "email": "test@test.com",
            "password": "P@ssword123!",
            "name": "Test User",
        }, headers=csrf)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["access_token"] == "token123"
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["email"] == "test@test.com"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient, app: FastAPI):
        mock_service = AsyncMock()
        mock_service.sign_up = AsyncMock(side_effect=HTTPException(status_code=409, detail="Email already registered"))

        async def _override():
            return mock_service
        app.dependency_overrides[get_auth_service] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/auth/signup", json={
            "email": "existing@test.com",
            "password": "P@ssword123!",
            "name": "Test User",
        }, headers=csrf)
        assert response.status_code == 409
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_signin_success(self, client: AsyncClient, app: FastAPI):
        user = make_mock_user()
        mock_service = AsyncMock()
        mock_service.sign_in = AsyncMock(return_value={
            "access_token": "token123",
            "refresh_token": "refresh123",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        })

        async def _override():
            return mock_service
        app.dependency_overrides[get_auth_service] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/auth/signin", json={
            "email": "test@test.com",
            "password": "P@ssword123!",
        }, headers=csrf)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["access_token"] == "token123"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_signin_invalid_credentials(self, client: AsyncClient, app: FastAPI):
        mock_service = AsyncMock()
        mock_service.sign_in = AsyncMock(side_effect=HTTPException(status_code=401, detail="Invalid email or password"))

        async def _override():
            return mock_service
        app.dependency_overrides[get_auth_service] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/auth/signin", json={
            "email": "test@test.com",
            "password": "wrong",
        }, headers=csrf)
        assert response.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, app: FastAPI, mock_user_id):
        user = make_mock_user(user_id=mock_user_id)
        mock_service = AsyncMock()
        mock_service.get_current_user = AsyncMock(return_value=user)

        async def _override():
            return mock_user_id
        app.dependency_overrides[require_user_id] = _override

        async def _override_service():
            return mock_service
        app.dependency_overrides[get_auth_service] = _override_service

        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == user.email
        app.dependency_overrides.clear()


class TestUserRoutes:
    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth, override_db):
        user = make_mock_user(email="new@test.com", name="New User")
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=user)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_create_user_use_case] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/users", json={
            "email": "new@test.com",
            "name": "New User",
        }, headers=csrf)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["email"] == "new@test.com"
        app.dependency_overrides.clear()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_user(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        user = make_mock_user(user_id=mock_user_id)
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=user)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_get_user_use_case] = _override

        response = await client.get(f"/api/v1/users/{mock_user_id}")
        assert response.status_code == 200
        assert response.json()["data"]["email"] == user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=EntityNotFoundError("User", str(mock_user_id)))
        async def _override():
            return mock_uc
        app.dependency_overrides[get_get_user_use_case] = _override

        response = await client.get(f"/api/v1/users/{mock_user_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        user = make_mock_user(user_id=mock_user_id, name="Updated Name")
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=user)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_update_user_use_case] = _override

        csrf = _setup_csrf(client)
        response = await client.patch(f"/api/v1/users/{mock_user_id}", json={"name": "Updated Name"}, headers=csrf)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=EntityNotFoundError("User", str(mock_user_id)))
        async def _override():
            return mock_uc
        app.dependency_overrides[get_update_user_use_case] = _override

        csrf = _setup_csrf(client)
        response = await client.patch(f"/api/v1/users/{mock_user_id}", json={"name": "X"}, headers=csrf)
        assert response.status_code == 404


class TestOrganizationRoutes:
    @pytest.mark.asyncio
    async def test_create_organization(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        org = make_mock_org()
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=org)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_create_org_use_case] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/organizations", json={
            "name": "Test Org",
            "slug": "test-org",
        }, headers=csrf)
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Test Org"

    @pytest.mark.asyncio
    async def test_create_organization_duplicate_slug(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=HTTPException(status_code=409, detail="already exists"))
        async def _override():
            return mock_uc
        app.dependency_overrides[get_create_org_use_case] = _override

        csrf = _setup_csrf(client)
        response = await client.post("/api/v1/organizations", json={
            "name": "Test Org",
            "slug": "existing-slug",
        }, headers=csrf)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_list_my_organizations(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        org1 = make_mock_org(name="Org 1", slug="org-1")
        org2 = make_mock_org(name="Org 2", slug="org-2")
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=[org1, org2])
        async def _override():
            return mock_uc
        app.dependency_overrides[get_list_orgs_use_case] = _override

        response = await client.get("/api/v1/organizations/my")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_organization(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth, override_rbac, override_db):
        org = make_mock_org()
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=org)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_get_org_use_case] = _override

        member = MagicMock()
        member.role = "owner"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=member)
        override_db.execute = AsyncMock(return_value=mock_result)

        response = await client.get(f"/api/v1/organizations/{org.id}")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == org.name

    @pytest.mark.asyncio
    async def test_get_organization_not_found(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth, override_rbac, override_db):
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=EntityNotFoundError("Organization", str(uuid4())))
        async def _override():
            return mock_uc
        app.dependency_overrides[get_get_org_use_case] = _override

        member = MagicMock()
        member.role = "member"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=member)
        override_db.execute = AsyncMock(return_value=mock_result)

        response = await client.get(f"/api/v1/organizations/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_organization_forbidden(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth, override_rbac, override_db):
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=ForbiddenError("Access denied"))
        async def _override():
            return mock_uc
        app.dependency_overrides[get_get_org_use_case] = _override

        member = MagicMock()
        member.role = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=member)
        override_db.execute = AsyncMock(return_value=mock_result)

        response = await client.get(f"/api/v1/organizations/{uuid4()}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_organization(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth, override_rbac, override_db):
        org = make_mock_org(name="Updated Org")
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=org)
        async def _override():
            return mock_uc
        app.dependency_overrides[get_update_org_use_case] = _override

        member = MagicMock()
        member.role = "owner"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=member)
        override_db.execute = AsyncMock(return_value=mock_result)

        csrf = _setup_csrf(client)
        response = await client.patch(f"/api/v1/organizations/{org.id}", json={"name": "Updated Org"}, headers=csrf)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Org"

    @pytest.mark.asyncio
    async def test_list_organizations(self, client: AsyncClient, app: FastAPI, mock_user_id, override_auth):
        org1 = make_mock_org(name="Org 1", slug="org-1")
        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=[org1])
        async def _override():
            return mock_uc
        app.dependency_overrides[get_list_orgs_use_case] = _override

        response = await client.get("/api/v1/organizations/my")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1


class TestAuthUseCases:
    @pytest.mark.asyncio
    async def test_auth_service_sign_up(self):
        from app.application.use_cases.auth_use_cases import AuthService
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock(return_value=make_mock_user())
        svc = AuthService(mock_repo)
        result = await svc.sign_up("test@test.com", "P@ssword123!", "Test")
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result

    @pytest.mark.asyncio
    async def test_auth_service_sign_up_duplicate(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.domain.exceptions.domain_exceptions import ValidationError
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=make_mock_user())
        svc = AuthService(mock_repo)
        with pytest.raises(ValidationError, match="already registered"):
            await svc.sign_up("test@test.com", "P@ssword123!", "Test")

    @pytest.mark.asyncio
    async def test_auth_service_sign_in_success(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.infrastructure.auth.password import hash_password
        user = make_mock_user(password_hash=hash_password("P@ssword123!"))
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=user)
        svc = AuthService(mock_repo)
        result = await svc.sign_in("test@test.com", "P@ssword123!")
        assert "access_token" in result

    @pytest.mark.asyncio
    async def test_auth_service_sign_in_user_not_found(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.domain.exceptions.domain_exceptions import ValidationError
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        svc = AuthService(mock_repo)
        with pytest.raises(ValidationError, match="Invalid email or password"):
            await svc.sign_in("test@test.com", "P@ssword123!")

    @pytest.mark.asyncio
    async def test_auth_service_sign_in_wrong_password(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.domain.exceptions.domain_exceptions import ValidationError
        from app.infrastructure.auth.password import hash_password
        user = make_mock_user(password_hash=hash_password("correct_password"))
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=user)
        svc = AuthService(mock_repo)
        with pytest.raises(ValidationError, match="Invalid email or password"):
            await svc.sign_in("test@test.com", "wrong_password")

    @pytest.mark.asyncio
    async def test_auth_service_sign_in_not_active(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.domain.exceptions.domain_exceptions import ValidationError
        from app.infrastructure.auth.password import hash_password
        user = make_mock_user(password_hash=hash_password("P@ssword123!"))
        user.is_active = False
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=user)
        svc = AuthService(mock_repo)
        with pytest.raises(ValidationError, match="deactivated"):
            await svc.sign_in("test@test.com", "P@ssword123!")

    @pytest.mark.asyncio
    async def test_auth_service_get_current_user(self):
        from app.application.use_cases.auth_use_cases import AuthService
        user = make_mock_user()
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=user)
        svc = AuthService(mock_repo)
        result = await svc.get_current_user(user.id)
        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_auth_service_get_current_user_not_found(self):
        from app.application.use_cases.auth_use_cases import AuthService
        from app.domain.exceptions.domain_exceptions import EntityNotFoundError
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=None)
        svc = AuthService(mock_repo)
        with pytest.raises(EntityNotFoundError):
            await svc.get_current_user(uuid4())


class TestUserUseCases:
    @pytest.mark.asyncio
    async def test_create_user_new(self):
        from app.application.use_cases.users import CreateUserUseCase
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock(return_value=make_mock_user())
        uc = CreateUserUseCase(mock_repo)
        result = await uc.execute("test@test.com", "Test")
        assert result.email == "test@test.com"

    @pytest.mark.asyncio
    async def test_create_user_existing(self):
        from app.application.use_cases.users import CreateUserUseCase
        existing = make_mock_user()
        mock_repo = AsyncMock()
        mock_repo.find_by_email = AsyncMock(return_value=existing)
        uc = CreateUserUseCase(mock_repo)
        result = await uc.execute("test@test.com", "Test")
        assert result.id == existing.id

    @pytest.mark.asyncio
    async def test_get_user_found(self):
        from app.application.use_cases.users import GetUserUseCase
        user = make_mock_user()
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=user)
        uc = GetUserUseCase(mock_repo)
        result = await uc.execute(user.id)
        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        from app.application.use_cases.users import GetUserUseCase
        from app.domain.exceptions.domain_exceptions import EntityNotFoundError
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=None)
        uc = GetUserUseCase(mock_repo)
        with pytest.raises(EntityNotFoundError):
            await uc.execute(uuid4())

    @pytest.mark.asyncio
    async def test_update_user(self):
        from app.application.use_cases.users import UpdateUserUseCase
        user = make_mock_user()
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=user)
        mock_repo.save = AsyncMock(return_value=user)
        uc = UpdateUserUseCase(mock_repo)
        result = await uc.execute(user.id, name="New Name")
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        from app.application.use_cases.users import UpdateUserUseCase
        from app.domain.exceptions.domain_exceptions import EntityNotFoundError
        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=None)
        uc = UpdateUserUseCase(mock_repo)
        with pytest.raises(EntityNotFoundError):
            await uc.execute(uuid4(), name="X")


class TestOrganizationUseCases:
    @pytest.mark.asyncio
    async def test_create_org(self):
        from app.application.use_cases.organizations import CreateOrganizationUseCase
        org = make_mock_org()
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_slug = AsyncMock(return_value=None)
        mock_org_repo.save = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        uc = CreateOrganizationUseCase(mock_org_repo, mock_member_repo)
        result = await uc.execute("Test Org", "test-org", uuid4())
        assert result.name == "Test Org"

    @pytest.mark.asyncio
    async def test_create_org_duplicate_slug(self):
        from app.application.use_cases.organizations import CreateOrganizationUseCase
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_slug = AsyncMock(return_value=make_mock_org())
        mock_member_repo = AsyncMock()
        uc = CreateOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(ValueError, match="already exists"):
            await uc.execute("Test Org", "test-org", uuid4())

    @pytest.mark.asyncio
    async def test_get_org(self):
        from app.application.use_cases.organizations import GetOrganizationUseCase
        org = make_mock_org()
        member = MagicMock()
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=member)
        uc = GetOrganizationUseCase(mock_org_repo, mock_member_repo)
        result = await uc.execute(org.id, uuid4())
        assert result.name == org.name

    @pytest.mark.asyncio
    async def test_get_org_not_found(self):
        from app.application.use_cases.organizations import GetOrganizationUseCase
        from app.domain.exceptions.domain_exceptions import EntityNotFoundError
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=None)
        mock_member_repo = AsyncMock()
        uc = GetOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(EntityNotFoundError):
            await uc.execute(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_get_org_forbidden(self):
        from app.application.use_cases.organizations import GetOrganizationUseCase
        from app.domain.exceptions.domain_exceptions import ForbiddenError
        org = make_mock_org()
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=None)
        uc = GetOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(ForbiddenError):
            await uc.execute(org.id, uuid4())

    @pytest.mark.asyncio
    async def test_list_user_organizations(self):
        from app.application.use_cases.organizations import ListUserOrganizationsUseCase
        org = make_mock_org()
        member = MagicMock(organization_id=org.id)
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_ids = AsyncMock(return_value=[org])
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user = AsyncMock(return_value=[member])
        uc = ListUserOrganizationsUseCase(mock_org_repo, mock_member_repo)
        result = await uc.execute(uuid4())
        assert len(result) == 1
        assert result[0].name == org.name

    @pytest.mark.asyncio
    async def test_update_org(self):
        from app.application.use_cases.organizations import UpdateOrganizationUseCase
        org = make_mock_org()
        member = MagicMock(role="owner")
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=org)
        mock_org_repo.save = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=member)
        uc = UpdateOrganizationUseCase(mock_org_repo, mock_member_repo)
        result = await uc.execute(org.id, uuid4(), name="New Name")
        assert result.id == org.id

    @pytest.mark.asyncio
    async def test_update_org_not_found(self):
        from app.application.use_cases.organizations import UpdateOrganizationUseCase
        from app.domain.exceptions.domain_exceptions import EntityNotFoundError
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=None)
        mock_member_repo = AsyncMock()
        mock_member = MagicMock()
        mock_member.role = "owner"
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=mock_member)
        uc = UpdateOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(EntityNotFoundError):
            await uc.execute(uuid4(), uuid4(), name="X")

    @pytest.mark.asyncio
    async def test_update_org_forbidden_not_member(self):
        from app.application.use_cases.organizations import UpdateOrganizationUseCase
        from app.domain.exceptions.domain_exceptions import ForbiddenError
        org = make_mock_org()
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=None)
        uc = UpdateOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(ForbiddenError):
            await uc.execute(org.id, uuid4(), name="X")

    @pytest.mark.asyncio
    async def test_update_org_forbidden_low_role(self):
        from app.application.use_cases.organizations import UpdateOrganizationUseCase
        from app.domain.exceptions.domain_exceptions import ForbiddenError
        org = make_mock_org()
        member = MagicMock(role="viewer")
        mock_org_repo = AsyncMock()
        mock_org_repo.find_by_id = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.find_by_user_and_organization = AsyncMock(return_value=member)
        uc = UpdateOrganizationUseCase(mock_org_repo, mock_member_repo)
        with pytest.raises(ForbiddenError):
            await uc.execute(org.id, uuid4(), name="X")


class TestDependencies:
    @pytest.mark.asyncio
    async def test_pagination_params(self):
        from app.presentation.dependencies import pagination_params
        result = await pagination_params(page=2, limit=10)
        assert result == {"page": 2, "limit": 10}

    @pytest.mark.asyncio
    async def test_pagination_defaults(self):
        from app.presentation.dependencies import pagination_params
        result = await pagination_params()
        assert result["page"].default == 1
        assert result["limit"].default == 50
