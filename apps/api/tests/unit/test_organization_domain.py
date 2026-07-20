from uuid import uuid4

from app.domain.entities.organization import (
    PERMISSIONS,
    PLAN_LIMITS,
    VALID_PLANS,
    BillingPlan,
    FeatureFlag,
    Organization,
    OrganizationMember,
    OrgInvitation,
    UsageRecord,
)
from app.domain.exceptions.domain_exceptions import ValidationError


class TestOrganization:
    def test_create_organization(self):
        org = Organization.create(name="My Agency", slug="my-agency")
        assert org.name == "My Agency"
        assert org.slug == "my-agency"
        assert org.plan_tier == "free"
        assert org.parent_org_id is None
        assert org.settings == {}

    def test_create_with_parent(self):
        parent_id = uuid4()
        org = Organization.create(name="Child", slug="child", parent_org_id=parent_id)
        assert org.parent_org_id == parent_id

    def test_update_settings(self):
        org = Organization.create(name="Org", slug="org")
        org.update_settings({"theme": "dark"})
        assert org.settings["theme"] == "dark"

    def test_change_plan_valid(self):
        org = Organization.create(name="Org", slug="org")
        for plan in VALID_PLANS:
            org.change_plan(plan)
            assert org.plan_tier == plan

    def test_change_plan_invalid(self):
        org = Organization.create(name="Org", slug="org")
        try:
            org.change_plan("nonexistent")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "Invalid plan" in str(e)

    def test_set_parent_valid(self):
        org = Organization.create(name="Org", slug="org")
        parent_id = uuid4()
        org.set_parent(parent_id)
        assert org.parent_org_id == parent_id

    def test_set_parent_self_reference(self):
        org = Organization.create(name="Org", slug="org")
        try:
            org.set_parent(org.id)
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "own parent" in str(e)


class TestOrganizationMember:
    def test_create_member(self):
        org_id = uuid4()
        user_id = uuid4()
        member = OrganizationMember.create(organization_id=org_id, user_id=user_id, role="admin")
        assert member.organization_id == org_id
        assert member.user_id == user_id
        assert member.role == "admin"
        assert "org:write" in member.permissions

    def test_create_member_default_role(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4())
        assert member.role == "member"
        assert "content:write" in member.permissions

    def test_create_member_invalid_role(self):
        try:
            OrganizationMember.create(organization_id=uuid4(), user_id=uuid4(), role="superadmin")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "Invalid role" in str(e)

    def test_change_role(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4(), role="member")
        member.change_role("admin")
        assert member.role == "admin"
        assert "org:write" in member.permissions
        assert "campaign:delete" in member.permissions
        assert "settings:write" in member.permissions

    def test_change_role_invalid(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4())
        try:
            member.change_role("god")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "Invalid role" in str(e)

    def test_add_permission(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4())
        assert not member.has_permission("org:delete")
        member.add_permission("org:delete")
        assert member.has_permission("org:delete")

    def test_add_permission_invalid(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4())
        try:
            member.add_permission("nonexistent")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "Invalid permission" in str(e)

    def test_add_permission_duplicate_noop(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4())
        member.add_permission("org:read")
        count = len(member.permissions)
        member.add_permission("org:read")
        assert len(member.permissions) == count

    def test_remove_permission(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4(), role="owner")
        assert member.has_permission("org:delete")
        member.remove_permission("org:delete")
        assert not member.has_permission("org:delete")

    def test_owner_has_all_permissions(self):
        member = OrganizationMember.create(organization_id=uuid4(), user_id=uuid4(), role="owner")
        for perm in PERMISSIONS:
            assert member.has_permission(perm), f"Owner missing permission: {perm}"


class TestOrgInvitation:
    def test_create_invitation(self):
        org_id = uuid4()
        inviter_id = uuid4()
        invitation = OrgInvitation.create(
            organization_id=org_id,
            invited_by=inviter_id,
            email="user@example.com",
            role="member",
        )
        assert invitation.organization_id == org_id
        assert invitation.invited_by_user_id == inviter_id
        assert invitation.email == "user@example.com"
        assert invitation.role == "member"
        assert invitation.status == "pending"

    def test_create_invitation_invalid_role(self):
        try:
            OrgInvitation.create(
                organization_id=uuid4(),
                invited_by=uuid4(),
                email="test@test.com",
                role="superadmin",
            )
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_create_invitation_cannot_invite_owner(self):
        try:
            OrgInvitation.create(
                organization_id=uuid4(),
                invited_by=uuid4(),
                email="test@test.com",
                role="owner",
            )
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "Cannot invite an owner" in str(e)

    def test_accept_invitation(self):
        inv = OrgInvitation.create(
            organization_id=uuid4(),
            invited_by=uuid4(),
            email="test@test.com",
            role="member",
        )
        inv.accept()
        assert inv.status == "accepted"

    def test_accept_non_pending_raises(self):
        inv = OrgInvitation.create(
            organization_id=uuid4(),
            invited_by=uuid4(),
            email="test@test.com",
            role="member",
        )
        inv.accept()
        try:
            inv.accept()
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_reject_invitation(self):
        inv = OrgInvitation.create(
            organization_id=uuid4(),
            invited_by=uuid4(),
            email="test@test.com",
            role="member",
        )
        inv.reject()
        assert inv.status == "rejected"

    def test_reject_non_pending_raises(self):
        inv = OrgInvitation.create(
            organization_id=uuid4(),
            invited_by=uuid4(),
            email="test@test.com",
            role="member",
        )
        inv.reject()
        try:
            inv.reject()
            assert False, "Expected ValidationError"
        except ValidationError:
            pass


class TestFeatureFlag:
    def test_create_feature_flag(self):
        flag = FeatureFlag.create(organization_id=uuid4(), feature_key="dark_mode")
        assert flag.feature_key == "dark_mode"
        assert flag.enabled is True
        assert flag.config == {}

    def test_create_with_config(self):
        flag = FeatureFlag.create(
            organization_id=uuid4(),
            feature_key="ai_content",
            enabled=False,
            config={"model": "gpt-4"},
        )
        assert flag.enabled is False
        assert flag.config["model"] == "gpt-4"

    def test_create_empty_key_raises(self):
        try:
            FeatureFlag.create(organization_id=uuid4(), feature_key="")
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_toggle(self):
        flag = FeatureFlag.create(organization_id=uuid4(), feature_key="x")
        flag.toggle(False)
        assert flag.enabled is False
        flag.toggle(True)
        assert flag.enabled is True

    def test_update_config(self):
        flag = FeatureFlag.create(organization_id=uuid4(), feature_key="x")
        flag.update_config({"new": "value"})
        assert flag.config["new"] == "value"


class TestUsageRecord:
    def test_create_usage_record(self):
        record = UsageRecord.create(organization_id=uuid4(), metric="campaigns_created", value=5.0)
        assert record.metric == "campaigns_created"
        assert record.value == 5.0

    def test_create_invalid_metric_raises(self):
        try:
            UsageRecord.create(organization_id=uuid4(), metric="invalid_metric")
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_default_value(self):
        record = UsageRecord.create(organization_id=uuid4(), metric="api_requests")
        assert record.value == 1.0


class TestBillingPlan:
    def test_create_billing_plan(self):
        plan = BillingPlan.create(organization_id=uuid4(), plan_tier="starter")
        assert plan.plan_tier == "starter"
        assert plan.subscription_status == "active"
        assert plan.billing_cycle == "monthly"

    def test_create_invalid_plan_raises(self):
        try:
            BillingPlan.create(organization_id=uuid4(), plan_tier="invalid")
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_change_plan(self):
        plan = BillingPlan.create(organization_id=uuid4(), plan_tier="free")
        plan.change_plan("professional")
        assert plan.plan_tier == "professional"

    def test_change_plan_invalid_raises(self):
        plan = BillingPlan.create(organization_id=uuid4())
        try:
            plan.change_plan("nope")
            assert False, "Expected ValidationError"
        except ValidationError:
            pass

    def test_get_limits_free(self):
        plan = BillingPlan.create(organization_id=uuid4(), plan_tier="free")
        limits = plan.get_limits()
        assert limits["max_campaigns"] == 5
        assert limits["max_team_members"] == 3

    def test_get_limits_enterprise_unlimited(self):
        plan = BillingPlan.create(organization_id=uuid4(), plan_tier="enterprise")
        limits = plan.get_limits()
        assert limits["max_campaigns"] == -1
        assert limits["max_emails_per_month"] == -1

    def test_is_active(self):
        plan = BillingPlan.create(organization_id=uuid4())
        assert plan.is_active() is True
        plan.subscription_status = "canceled"
        assert plan.is_active() is False

    def test_plan_limits_structure(self):
        for plan_tier in VALID_PLANS:
            assert plan_tier in PLAN_LIMITS
            limits = PLAN_LIMITS[plan_tier]
            assert "max_campaigns" in limits
            assert "max_team_members" in limits
            assert "max_emails_per_month" in limits
            assert "max_storage_mb" in limits
            assert "max_api_requests_per_day" in limits
