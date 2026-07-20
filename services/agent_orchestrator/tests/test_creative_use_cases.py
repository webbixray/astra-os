"""Tests for Creative Management Use Cases — CRUD, approval workflow, campaign association.

All tests are pure unit tests with a mock repository — no DB required.
"""

import asyncio
from uuid import UUID, uuid4

import pytest
from app.application.use_cases.campaigns.creative_use_cases import (
    ApproveCreativeUseCase,
    AssociateCreativeToCampaignUseCase,
    CreateCreativeUseCase,
    DeleteCreativeUseCase,
    GetCreativeUseCase,
    ListCreativesUseCase,
    RejectCreativeUseCase,
    SubmitCreativeForReviewUseCase,
    UpdateCreativeUseCase,
)
from app.domain.entities.advertising.ad_creative import AdCreative, CreativeStatus, CreativeType
from app.domain.exceptions.domain_exceptions import EntityNotFoundError, ValidationError

# ── Helpers ──────────────────────────────────────────────────────────


class MockCreativeRepo:
    def __init__(self):
        self._creatives: dict = {}

    async def save(self, creative):
        self._creatives[creative.id] = creative
        return creative

    async def find_by_id(self, creative_id):
        return self._creatives.get(creative_id)

    async def find_by_organization(self, org_id, status=None):
        results = [c for c in self._creatives.values() if c.organization_id == org_id]
        if status is not None:
            results = [c for c in results if c.status == status]
        return results

    async def find_by_campaign(self, campaign_id):
        return [c for c in self._creatives.values() if c.ad_campaign_id == campaign_id]

    async def delete(self, creative_id):
        self._creatives.pop(creative_id, None)


def _make_creative(
    org_id: UUID | None = None,
    status: CreativeStatus = CreativeStatus.DRAFT,
    name: str = "Test Creative",
) -> AdCreative:
    return AdCreative.create(
        organization_id=org_id or uuid4(),
        name=name,
        type=CreativeType.IMAGE,
        created_by=uuid4(),
    )


# ── Create Tests ─────────────────────────────────────────────────────


class TestCreateCreative:
    def test_create_basic(self):
        repo = MockCreativeRepo()
        uc = CreateCreativeUseCase(repo)
        org_id = uuid4()

        result = asyncio.run(
            uc.execute(
                organization_id=org_id,
                name="Summer Sale Banner",
                created_by=uuid4(),
            )
        )

        assert result.name == "Summer Sale Banner"
        assert result.type == CreativeType.IMAGE
        assert result.status == CreativeStatus.DRAFT
        assert result.organization_id == org_id

    def test_create_with_type(self):
        repo = MockCreativeRepo()
        uc = CreateCreativeUseCase(repo)

        result = asyncio.run(
            uc.execute(
                organization_id=uuid4(),
                name="Video Ad",
                created_by=uuid4(),
                type=CreativeType.VIDEO,
            )
        )

        assert result.type == CreativeType.VIDEO

    def test_create_with_details(self):
        repo = MockCreativeRepo()
        uc = CreateCreativeUseCase(repo)

        result = asyncio.run(
            uc.execute(
                organization_id=uuid4(),
                name="Full Creative",
                created_by=uuid4(),
                headline="Buy Now!",
                body="Limited time offer",
                destination_url="https://example.com",
                asset_urls=["https://cdn.example.com/img1.jpg"],
            )
        )

        assert result.headline == "Buy Now!"
        assert result.body == "Limited time offer"
        assert result.destination_url == "https://example.com"
        assert len(result.asset_urls) == 1

    def test_create_empty_name_fails(self):
        repo = MockCreativeRepo()
        uc = CreateCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="name"):
            asyncio.run(
                uc.execute(
                    organization_id=uuid4(),
                    name="",
                    created_by=uuid4(),
                )
            )

    def test_create_whitespace_name_fails(self):
        repo = MockCreativeRepo()
        uc = CreateCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="name"):
            asyncio.run(
                uc.execute(
                    organization_id=uuid4(),
                    name="   ",
                    created_by=uuid4(),
                )
            )


# ── Get Tests ────────────────────────────────────────────────────────


class TestGetCreative:
    def test_get_existing(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = GetCreativeUseCase(repo)
        result = asyncio.run(uc.execute(creative.id))

        assert result.id == creative.id
        assert result.name == creative.name

    def test_get_not_found(self):
        repo = MockCreativeRepo()
        uc = GetCreativeUseCase(repo)

        with pytest.raises(EntityNotFoundError):
            asyncio.run(uc.execute(uuid4()))


# ── List Tests ───────────────────────────────────────────────────────


class TestListCreatives:
    def test_list_by_org(self):
        repo = MockCreativeRepo()
        org_id = uuid4()

        for i in range(3):
            c = _make_creative(org_id=org_id, name=f"Creative {i}")
            asyncio.run(repo.save(c))

        uc = ListCreativesUseCase(repo)
        results = asyncio.run(uc.execute(org_id))

        assert len(results) == 3

    def test_list_by_org_with_status_filter(self):
        repo = MockCreativeRepo()
        org_id = uuid4()

        c1 = _make_creative(org_id=org_id, name="Draft 1")
        c1.status = CreativeStatus.DRAFT
        asyncio.run(repo.save(c1))

        c2 = _make_creative(org_id=org_id, name="Approved 1")
        c2.status = CreativeStatus.APPROVED
        asyncio.run(repo.save(c2))

        uc = ListCreativesUseCase(repo)
        results = asyncio.run(uc.execute(org_id, status=CreativeStatus.APPROVED))

        assert len(results) == 1
        assert results[0].status == CreativeStatus.APPROVED


# ── Update Tests ─────────────────────────────────────────────────────


class TestUpdateCreative:
    def test_update_draft(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = UpdateCreativeUseCase(repo)
        result = asyncio.run(
            uc.execute(
                creative_id=creative.id,
                name="Updated Name",
                headline="New Headline",
            )
        )

        assert result.name == "Updated Name"
        assert result.headline == "New Headline"

    def test_update_not_found(self):
        repo = MockCreativeRepo()
        uc = UpdateCreativeUseCase(repo)

        with pytest.raises(EntityNotFoundError):
            asyncio.run(uc.execute(creative_id=uuid4(), name="X"))

    def test_update_active_fails(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.ACTIVE
        asyncio.run(repo.save(creative))

        uc = UpdateCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot edit"):
            asyncio.run(uc.execute(creative_id=creative.id, name="X"))

    def test_update_approved_fails(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.APPROVED
        asyncio.run(repo.save(creative))

        uc = UpdateCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot edit"):
            asyncio.run(uc.execute(creative_id=creative.id, name="X"))

    def test_update_rejected_allows_edit(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.REJECTED
        asyncio.run(repo.save(creative))

        uc = UpdateCreativeUseCase(repo)
        result = asyncio.run(uc.execute(creative_id=creative.id, name="Fixed"))

        assert result.name == "Fixed"


# ── Submit for Review Tests ──────────────────────────────────────────


class TestSubmitForReview:
    def test_submit_draft(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = SubmitCreativeForReviewUseCase(repo)
        result = asyncio.run(uc.execute(creative.id))

        assert result.status == CreativeStatus.PENDING_REVIEW

    def test_submit_wrong_status(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.ACTIVE
        asyncio.run(repo.save(creative))

        uc = SubmitCreativeForReviewUseCase(repo)

        with pytest.raises(ValidationError, match="Must be 'draft'"):
            asyncio.run(uc.execute(creative.id))


# ── Approve Tests ────────────────────────────────────────────────────


class TestApproveCreative:
    def test_approve_pending(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.PENDING_REVIEW
        asyncio.run(repo.save(creative))

        uc = ApproveCreativeUseCase(repo)
        result = asyncio.run(uc.execute(creative.id))

        assert result.status == CreativeStatus.APPROVED

    def test_approve_wrong_status(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = ApproveCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="Must be 'pending_review'"):
            asyncio.run(uc.execute(creative.id))


# ── Reject Tests ─────────────────────────────────────────────────────


class TestRejectCreative:
    def test_reject_pending(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.PENDING_REVIEW
        asyncio.run(repo.save(creative))

        uc = RejectCreativeUseCase(repo)
        result = asyncio.run(uc.execute(creative.id, reason="Off-brand"))

        assert result.status == CreativeStatus.REJECTED

    def test_reject_wrong_status(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = RejectCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="Must be 'pending_review'"):
            asyncio.run(uc.execute(creative.id))


# ── Associate Tests ──────────────────────────────────────────────────


class TestAssociateToCampaign:
    def test_associate(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        campaign_id = uuid4()
        uc = AssociateCreativeToCampaignUseCase(repo)
        result = asyncio.run(uc.execute(creative.id, campaign_id))

        assert result.ad_campaign_id == campaign_id

    def test_associate_not_found(self):
        repo = MockCreativeRepo()
        uc = AssociateCreativeToCampaignUseCase(repo)

        with pytest.raises(EntityNotFoundError):
            asyncio.run(uc.execute(uuid4(), uuid4()))


# ── Delete Tests ─────────────────────────────────────────────────────


class TestDeleteCreative:
    def test_delete_draft(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        asyncio.run(repo.save(creative))

        uc = DeleteCreativeUseCase(repo)
        asyncio.run(uc.execute(creative.id))

        assert asyncio.run(repo.find_by_id(creative.id)) is None

    def test_delete_active_fails(self):
        repo = MockCreativeRepo()
        creative = _make_creative()
        creative.status = CreativeStatus.ACTIVE
        asyncio.run(repo.save(creative))

        uc = DeleteCreativeUseCase(repo)

        with pytest.raises(ValidationError, match="Cannot delete"):
            asyncio.run(uc.execute(creative.id))

    def test_delete_not_found(self):
        repo = MockCreativeRepo()
        uc = DeleteCreativeUseCase(repo)

        with pytest.raises(EntityNotFoundError):
            asyncio.run(uc.execute(uuid4()))
