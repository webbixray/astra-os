from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.organization import (
    ORG_ROLE_HIERARCHY,
    PLAN_LIMITS,
    BillingPlan,
    FeatureFlag,
    Organization,
    OrganizationMember,
    OrgInvitation,
    UsageRecord,
)
from app.domain.entities.organization import Organization as OrgEntity
from app.domain.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenError,
    ValidationError,
)
from app.infrastructure.db.repositories.billing_plan_repository import BillingPlanRepository
from app.infrastructure.db.repositories.feature_flag_repository import FeatureFlagRepository
from app.infrastructure.db.repositories.org_invitation_repository import OrgInvitationRepository
from app.infrastructure.db.repositories.organization_repository import OrganizationRepositoryImpl
from app.infrastructure.db.repositories.team_member_repository import TeamMemberRepositoryImpl
from app.infrastructure.db.repositories.usage_record_repository import UsageRecordRepository
from app.infrastructure.db.repositories.user_repository import UserRepositoryImpl


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_repo = OrganizationRepositoryImpl(db)
        self.member_repo = TeamMemberRepositoryImpl(db)
        self.invitation_repo = OrgInvitationRepository(db)
        self.feature_repo = FeatureFlagRepository(db)
        self.usage_repo = UsageRecordRepository(db)
        self.billing_repo = BillingPlanRepository(db)
        self.user_repo = UserRepositoryImpl(db)

    # ── Org Hierarchy ────────────────────────────────────────────────────────

    async def get_org_tree(self, org_id: UUID) -> dict:
        org = await self._get_org(org_id)
        children = await self.org_repo.find_by_parent(org_id)
        return {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "plan_tier": org.plan_tier,
            "children": [
                {"id": str(c.id), "name": c.name, "slug": c.slug, "plan_tier": c.plan_tier}
                for c in children
            ],
        }

    async def set_parent_org(
        self, org_id: UUID, parent_org_id: UUID, user_id: UUID
    ) -> Organization:
        org = await self._get_org(org_id)
        await self._require_role(org_id, user_id, "admin")
        parent = await self.org_repo.find_by_id(parent_org_id)
        if parent is None:
            raise EntityNotFoundError("Organization", str(parent_org_id))
        org.set_parent(parent_org_id)
        return await self.org_repo.save(org)

    async def get_user_orgs(self, user_id: UUID) -> list[dict]:
        memberships = await self.member_repo.find_by_user(user_id)
        org_ids = [m.organization_id for m in memberships]
        orgs_list = await self.org_repo.find_by_ids(org_ids)
        orgs_by_id = {o.id: o for o in orgs_list}
        result = []
        for m in memberships:
            org = orgs_by_id.get(m.organization_id)
            if org:
                result.append(
                    {
                        "id": str(org.id),
                        "name": org.name,
                        "slug": org.slug,
                        "plan_tier": org.plan_tier,
                        "role": m.role,
                    }
                )
        return result

    async def create_sub_org(
        self, parent_org_id: UUID, name: str, slug: str, user_id: UUID
    ) -> Organization:
        await self._require_role(parent_org_id, user_id, "admin")
        existing = await self.org_repo.find_by_slug(slug)
        if existing is not None:
            raise ValidationError(f"Organization with slug '{slug}' already exists")
        org = Organization.create(name=name, slug=slug, parent_org_id=parent_org_id)
        saved = await self.org_repo.save(org)
        owner = OrganizationMember.create(organization_id=saved.id, user_id=user_id, role="owner")
        await self.member_repo.save(owner)
        return saved

    # ── Invitations ──────────────────────────────────────────────────────────

    async def invite_member(
        self, org_id: UUID, invited_by: UUID, email: str, role: str = "member"
    ) -> OrgInvitation:
        await self._require_role(org_id, invited_by, "admin")
        if role == "owner":
            raise ValidationError("Cannot invite an owner")

        user = await self.user_repo.find_by_email(email)
        if user is not None:
            existing = await self.member_repo.find_by_user_and_organization(user.id, org_id)
            if existing is not None:
                raise ValidationError("User is already a member")

        existing_inv = await self.invitation_repo.find_pending_by_email(email)
        for inv in existing_inv:
            if inv.organization_id == org_id:
                raise ValidationError("A pending invitation already exists for this email")

        invitation = OrgInvitation.create(
            organization_id=org_id,
            invited_by=invited_by,
            email=email,
            role=role,
        )
        return await self.invitation_repo.save(invitation)

    async def list_invitations(self, org_id: UUID, user_id: UUID) -> list[OrgInvitation]:
        await self._require_role(org_id, user_id, "member")
        return await self.invitation_repo.find_by_organization(org_id)

    async def accept_invitation(self, invitation_id: UUID, user_id: UUID) -> OrganizationMember:
        invitation = await self.invitation_repo.find_by_id(invitation_id)
        if invitation is None:
            raise EntityNotFoundError("Invitation", str(invitation_id))
        if invitation.status != "pending":
            raise ValidationError(f"Invitation is '{invitation.status}', not pending")

        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", str(user_id))
        if user.email != invitation.email:
            raise ForbiddenError("This invitation was sent to a different email")

        invitation.accept()
        await self.invitation_repo.save(invitation)

        member = OrganizationMember.create(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role=invitation.role,
        )
        return await self.member_repo.save(member)

    async def reject_invitation(self, invitation_id: UUID, user_id: UUID) -> OrgInvitation:
        invitation = await self.invitation_repo.find_by_id(invitation_id)
        if invitation is None:
            raise EntityNotFoundError("Invitation", str(invitation_id))

        user = await self.user_repo.find_by_id(user_id)
        if user is None or user.email != invitation.email:
            raise ForbiddenError("This invitation was not sent to you")

        invitation.reject()
        return await self.invitation_repo.save(invitation)

    async def cancel_invitation(self, invitation_id: UUID, org_id: UUID, user_id: UUID) -> None:
        await self._require_role(org_id, user_id, "admin")
        await self.invitation_repo.delete(invitation_id)

    # ── Members ──────────────────────────────────────────────────────────────

    async def list_members(self, org_id: UUID, user_id: UUID) -> list[dict]:
        await self._require_role(org_id, user_id, "viewer")
        members = await self.member_repo.find_by_organization(org_id)
        user_ids = [m.user_id for m in members]
        users_list = await self.user_repo.find_by_ids(user_ids)
        users_by_id = {u.id: u for u in users_list}
        result = []
        for m in members:
            u = users_by_id.get(m.user_id)
            result.append(
                {
                    "id": str(m.id),
                    "user_id": str(m.user_id),
                    "email": u.email if u else "unknown",
                    "name": u.name if u else "Unknown",
                    "role": m.role,
                    "permissions": m.permissions,
                    "joined_at": m.joined_at.isoformat(),
                }
            )
        return result

    async def change_member_role(
        self, member_id: UUID, new_role: str, org_id: UUID, user_id: UUID
    ) -> OrganizationMember:
        await self._require_role(org_id, user_id, "admin")
        member = await self.member_repo.find_by_id(member_id)
        if member is None:
            raise EntityNotFoundError("Member", str(member_id))
        if new_role == "owner":
            raise ValidationError("Cannot assign owner role via this endpoint")
        if member.user_id == user_id:
            raise ValidationError("Cannot change your own role")
        member.change_role(new_role)
        return await self.member_repo.save(member)

    async def remove_member(self, member_id: UUID, org_id: UUID, user_id: UUID) -> None:
        await self._require_role(org_id, user_id, "admin")
        member = await self.member_repo.find_by_id(member_id)
        if member is None:
            raise EntityNotFoundError("Member", str(member_id))
        if member.user_id == user_id:
            raise ValidationError("Cannot remove yourself")
        await self.member_repo.delete(member_id)

    # ── Feature Flags ────────────────────────────────────────────────────────

    async def list_feature_flags(self, org_id: UUID) -> list[FeatureFlag]:
        return await self.feature_repo.find_by_organization(org_id)

    async def set_feature_flag(
        self, org_id: UUID, feature_key: str, *, enabled: bool = True, config: dict | None = None
    ) -> FeatureFlag:
        existing = await self.feature_repo.find_by_key(org_id, feature_key)
        if existing is not None:
            existing.toggle(enabled)
            if config:
                existing.update_config(config)
            return await self.feature_repo.save(existing)
        return await self.feature_repo.save(
            FeatureFlag.create(org_id, feature_key, enabled=enabled, config=config)
        )

    async def delete_feature_flag(self, org_id: UUID, flag_id: UUID) -> None:
        await self.feature_repo.delete(flag_id)

    # ── Usage Tracking ───────────────────────────────────────────────────────

    async def record_usage(self, org_id: UUID, metric: str, value: float = 1.0) -> UsageRecord:
        record = UsageRecord.create(org_id, metric, value)
        return await self.usage_repo.save(record)

    async def get_usage_summary(self, org_id: UUID) -> dict:
        plan = await self.billing_repo.find_by_organization(org_id)
        limits = plan.get_limits() if plan else PLAN_LIMITS["free"]

        now = datetime.now(UTC).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        usage = {}
        for metric in [
            "api_requests",
            "campaigns_created",
            "emails_sent",
            "content_published",
            "workflow_executions",
            "reports_generated",
            "storage_mb",
            "team_members",
        ]:
            if metric == "team_members":
                members = await self.member_repo.find_by_organization(org_id)
                usage[metric] = len(members)
            else:
                usage[metric] = await self.usage_repo.sum_by_metric(
                    org_id, metric, since=month_start
                )

        return {
            "usage": usage,
            "limits": limits,
            "plan_tier": plan.plan_tier if plan else "free",
            "period_start": month_start.isoformat(),
        }

    async def get_usage_trend(
        self, org_id: UUID, metric: str = "api_requests", days: int = 30
    ) -> list[dict]:
        return await self.usage_repo.aggregate_by_period(org_id, metric, days=days)

    # ── Billing ──────────────────────────────────────────────────────────────

    async def get_billing_plan(self, org_id: UUID) -> BillingPlan:
        plan = await self.billing_repo.find_by_organization(org_id)
        if plan is None:
            plan = BillingPlan.create(org_id)
            plan = await self.billing_repo.save(plan)
        return plan

    async def change_billing_plan(self, org_id: UUID, plan_tier: str, user_id: UUID) -> BillingPlan:
        await self._require_role(org_id, user_id, "admin")
        plan = await self.get_billing_plan(org_id)
        plan.change_plan(plan_tier)
        return await self.billing_repo.upsert(plan)

    # ── Permissions ──────────────────────────────────────────────────────────

    async def check_permission(self, org_id: UUID, user_id: UUID, permission: str) -> bool:
        member = await self.member_repo.find_by_user_and_organization(user_id, org_id)
        if member is None:
            return False
        return member.has_permission(permission)

    async def add_member_permission(
        self, member_id: UUID, permission: str, org_id: UUID, user_id: UUID
    ) -> OrganizationMember:
        await self._require_role(org_id, user_id, "admin")
        member = await self.member_repo.find_by_id(member_id)
        if member is None:
            raise EntityNotFoundError("Member", str(member_id))
        member.add_permission(permission)
        return await self.member_repo.save(member)

    async def remove_member_permission(
        self, member_id: UUID, permission: str, org_id: UUID, user_id: UUID
    ) -> OrganizationMember:
        await self._require_role(org_id, user_id, "admin")
        member = await self.member_repo.find_by_id(member_id)
        if member is None:
            raise EntityNotFoundError("Member", str(member_id))
        member.remove_permission(permission)
        return await self.member_repo.save(member)

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _get_org(self, org_id: UUID) -> Organization:
        org = await self.org_repo.find_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", str(org_id))
        return org

    async def _require_role(
        self, org_id: UUID, user_id: UUID, minimum_role: str
    ) -> OrganizationMember:
        member = await self.member_repo.find_by_user_and_organization(user_id, org_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        min_level = ORG_ROLE_HIERARCHY.get(minimum_role, 0)
        user_level = ORG_ROLE_HIERARCHY.get(member.role, 0)
        if user_level < min_level:
            raise ForbiddenError(
                f"Requires role '{minimum_role}' or higher (current: '{member.role}')"
            )
        return member


class CreateOrganizationUseCase:
    def __init__(
        self, org_repo: OrganizationRepositoryImpl, member_repo: TeamMemberRepositoryImpl
    ) -> None:
        self.org_repo = org_repo
        self.member_repo = member_repo

    async def execute(self, name: str, slug: str, owner_id: UUID) -> OrgEntity:
        existing = await self.org_repo.find_by_slug(slug)
        if existing is not None:
            raise ValueError(f"Organization with slug '{slug}' already exists")
        org = OrgEntity.create(name=name, slug=slug)
        saved = await self.org_repo.save(org)
        owner = OrganizationMember.create(
            organization_id=saved.id,
            user_id=owner_id,
            role="owner",
        )
        await self.member_repo.save(owner)
        return saved


class GetOrganizationUseCase:
    def __init__(
        self, org_repo: OrganizationRepositoryImpl, member_repo: TeamMemberRepositoryImpl
    ) -> None:
        self.org_repo = org_repo
        self.member_repo = member_repo

    async def execute(self, org_id: UUID, user_id: UUID) -> OrgEntity:
        member = await self.member_repo.find_by_user_and_organization(user_id, org_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        org = await self.org_repo.find_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", str(org_id))
        return org


class UpdateOrganizationUseCase:
    def __init__(
        self, org_repo: OrganizationRepositoryImpl, member_repo: TeamMemberRepositoryImpl
    ) -> None:
        self.org_repo = org_repo
        self.member_repo = member_repo

    async def execute(
        self,
        org_id: UUID,
        user_id: UUID,
        name: str | None = None,
        settings: dict | None = None,
    ) -> OrgEntity:
        member = await self.member_repo.find_by_user_and_organization(user_id, org_id)
        if member is None:
            raise ForbiddenError("Not a member of this organization")
        if member.role not in ("admin", "owner"):
            raise ForbiddenError("Requires admin or owner role")
        org = await self.org_repo.find_by_id(org_id)
        if org is None:
            raise EntityNotFoundError("Organization", str(org_id))
        if name is not None:
            org.name = name
        if settings is not None:
            org.settings = settings
        return await self.org_repo.save(org)


class ListUserOrganizationsUseCase:
    def __init__(
        self, org_repo: OrganizationRepositoryImpl, member_repo: TeamMemberRepositoryImpl
    ) -> None:
        self.org_repo = org_repo
        self.member_repo = member_repo

    async def execute(self, user_id: UUID) -> list[OrgEntity]:
        memberships = await self.member_repo.find_by_user(user_id)
        org_ids = [m.organization_id for m in memberships]
        orgs_list = await self.org_repo.find_by_ids(org_ids)
        orgs_by_id = {o.id: o for o in orgs_list}
        return [
            orgs_by_id[m.organization_id] for m in memberships if m.organization_id in orgs_by_id
        ]
