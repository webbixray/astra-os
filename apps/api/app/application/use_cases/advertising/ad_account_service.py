from uuid import UUID

from app.domain.common import now
from app.domain.entities.advertising.ad_account import AdAccount, ConnectionStatus, Platform
from app.infrastructure.db.repositories.advertising.advertising_repository import (
    AdAccountRepository,
)
from app.infrastructure.external_adapters.adplatforms.base_adapter import (
    AdPlatformFactory,
)


class AdAccountService:
    def __init__(self, repo: AdAccountRepository):
        self.repo = repo

    async def connect(
        self,
        organization_id: UUID,
        platform: str,
        account_name: str,
        platform_account_id: str,
        credentials: dict | None = None,
    ) -> dict:
        from app.infrastructure.db.models.advertising.advertising_models import AdAccountModel

        account = AdAccount.create(
            organization_id=organization_id,
            platform=Platform(platform),
            account_name=account_name,
            platform_account_id=platform_account_id,
        )

        model = AdAccountModel(
            id=account.id,
            organization_id=organization_id,
            platform=platform,
            account_name=account_name,
            platform_account_id=platform_account_id,
            status=ConnectionStatus.CONNECTED.value,
            credentials=credentials or {},
        )
        saved = await self.repo.save(model)

        return {
            "id": str(saved.id),
            "platform": saved.platform,
            "account_name": saved.account_name,
            "status": saved.status,
        }

    async def list_accounts(self, organization_id: UUID) -> list[dict]:
        models = await self.repo.find_by_organization(organization_id)
        return [
            {
                "id": str(m.id),
                "platform": m.platform,
                "account_name": m.account_name,
                "status": m.status,
                "last_synced_at": m.last_synced_at.isoformat() if m.last_synced_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in models
        ]

    async def disconnect(self, account_id: UUID) -> dict:
        model = await self.repo.find_by_id(account_id)
        if not model:
            return {"error": "Account not found"}
        model.status = ConnectionStatus.DISCONNECTED.value
        await self.repo.save(model)
        return {"id": str(model.id), "status": "disconnected"}

    async def sync(self, account_id: UUID) -> dict:
        model = await self.repo.find_by_id(account_id)
        if not model:
            return {"error": "Account not found"}

        adapter = AdPlatformFactory.create(
            Platform(model.platform),
            model.credentials,
        )
        campaigns = await adapter.get_campaigns(model.platform_account_id)

        model.last_synced_at = now()
        await self.repo.save(model)

        return {
            "id": str(model.id),
            "campaigns_synced": len(campaigns),
            "platform": model.platform,
        }
