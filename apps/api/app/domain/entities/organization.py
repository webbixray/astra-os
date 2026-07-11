import re
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.common import now
from app.domain.exceptions.domain_exceptions import ValidationError

VALID_PLANS = ["free", "starter", "professional", "business", "enterprise"]


@dataclass
class Organization:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    plan_tier: str = "free"
    parent_org_id: UUID | None = None
    settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, name: str, slug: str, parent_org_id: UUID | None = None) -> "Organization":
        if not name or not name.strip():
            raise ValidationError("Organization name is required")
        if not slug or not slug.strip():
            raise ValidationError("Slug is required")
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
            raise ValidationError("Slug must contain only lowercase alphanumeric characters and hyphens")
        return cls(
            name=name.strip(),
            slug=slug.strip(),
            parent_org_id=parent_org_id,
        )

    def update_settings(self, settings: dict) -> None:
        self.settings.update(settings)
        self.updated_at = now()

    def change_plan(self, plan_tier: str) -> None:
        if plan_tier not in VALID_PLANS:
            raise ValidationError(f"Invalid plan tier: {plan_tier}. Must be one of {VALID_PLANS}")
        self.plan_tier = plan_tier
        self.updated_at = now()

    def set_parent(self, parent_org_id: UUID | None) -> None:
        if parent_org_id == self.id:
            raise ValidationError("An organization cannot be its own parent")
        self.parent_org_id = parent_org_id
        self.updated_at = now()


# ── Roles & Permissions ──────────────────────────────────────────────────────

ORG_ROLES = ["owner", "admin", "member", "viewer"]
ORG_ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 10,
    "member": 20,
    "admin": 30,
    "owner": 40,
}

PERMISSIONS = [
    "org:read", "org:write", "org:delete",
    "org:manage_members", "org:manage_billing",
    "org:manage_features",
    "campaign:read", "campaign:write", "campaign:delete",
    "content:read", "content:write", "content:delete",
    "content:publish",
    "email:read", "email:write", "email:send",
    "analytics:read",
    "reports:read", "reports:export",
    "workflows:read", "workflows:write", "workflows:execute",
    "settings:read", "settings:write",
]

ROLE_DEFAULT_PERMISSIONS: dict[str, list[str]] = {
    "viewer": [
        "org:read", "campaign:read", "content:read",
        "email:read", "analytics:read", "reports:read",
        "workflows:read", "settings:read",
    ],
    "member": [
        "org:read", "campaign:read", "campaign:write",
        "content:read", "content:write", "content:publish",
        "email:read", "email:write", "email:send",
        "analytics:read", "reports:read", "reports:export",
        "workflows:read", "workflows:write", "workflows:execute",
        "settings:read",
    ],
    "admin": [
        "org:read", "org:write", "org:manage_members",
        "campaign:read", "campaign:write", "campaign:delete",
        "content:read", "content:write", "content:delete",
        "content:publish",
        "email:read", "email:write", "email:send",
        "analytics:read",
        "reports:read", "reports:export",
        "workflows:read", "workflows:write", "workflows:execute",
        "settings:read", "settings:write",
    ],
    "owner": PERMISSIONS,
}


@dataclass
class OrganizationMember:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    role: str = "member"
    permissions: list[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, user_id: UUID, role: str = "member") -> "OrganizationMember":
        if role not in ORG_ROLES:
            raise ValidationError(f"Invalid role: {role}. Must be one of {ORG_ROLES}")
        return cls(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            permissions=list(ROLE_DEFAULT_PERMISSIONS.get(role, [])),
        )

    def change_role(self, new_role: str) -> None:
        if new_role not in ORG_ROLES:
            raise ValidationError(f"Invalid role: {new_role}. Must be one of {ORG_ROLES}")
        self.role = new_role
        self.permissions = list(ROLE_DEFAULT_PERMISSIONS.get(new_role, []))

    def add_permission(self, permission: str) -> None:
        if permission not in PERMISSIONS:
            raise ValidationError(f"Invalid permission: {permission}")
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str) -> None:
        self.permissions = [p for p in self.permissions if p != permission]

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


# ── Invitations ──────────────────────────────────────────────────────────────

INVITATION_STATUSES = ["pending", "accepted", "rejected", "expired"]


@dataclass
class OrgInvitation:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    invited_by_user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    role: str = "member"
    status: str = "pending"
    expires_at: datetime = field(default_factory=now)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, invited_by: UUID,
               email: str, role: str = "member") -> "OrgInvitation":
        if role not in ORG_ROLES:
            raise ValidationError(f"Invalid role: {role}")
        if role == "owner":
            raise ValidationError("Cannot invite an owner")
        return cls(
            organization_id=organization_id,
            invited_by_user_id=invited_by,
            email=email,
            role=role,
            expires_at=now(),
        )

    def accept(self) -> None:
        if self.status != "pending":
            raise ValidationError(f"Cannot accept invitation with status '{self.status}'")
        self.status = "accepted"
        self.updated_at = now()

    def reject(self) -> None:
        if self.status != "pending":
            raise ValidationError(f"Cannot reject invitation with status '{self.status}'")
        self.status = "rejected"
        self.updated_at = now()

    def is_expired(self) -> bool:
        return now() > self.expires_at


# ── Feature Flags ────────────────────────────────────────────────────────────

@dataclass
class FeatureFlag:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    feature_key: str = ""
    enabled: bool = True
    config: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, feature_key: str,
                *, enabled: bool = True, config: dict | None = None) -> "FeatureFlag":
        if not feature_key or not feature_key.strip():
            raise ValidationError("Feature key is required")
        return cls(
            organization_id=organization_id,
            feature_key=feature_key.strip(),
            enabled=enabled,
            config=config or {},
        )

    def toggle(self, enabled: bool) -> None:
        self.enabled = enabled
        self.updated_at = now()

    def update_config(self, config: dict) -> None:
        self.config.update(config)
        self.updated_at = now()


# ── Usage Tracking ───────────────────────────────────────────────────────────

USAGE_METRICS = [
    "api_requests", "campaigns_created", "emails_sent",
    "content_published", "workflow_executions", "reports_generated",
    "storage_mb", "team_members",
]


@dataclass
class UsageRecord:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    metric: str = ""
    value: float = 0.0
    recorded_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, metric: str, value: float = 1.0) -> "UsageRecord":
        if metric not in USAGE_METRICS:
            raise ValidationError(f"Invalid usage metric: {metric}. Must be one of {USAGE_METRICS}")
        return cls(
            organization_id=organization_id,
            metric=metric,
            value=value,
        )


# ── Billing ──────────────────────────────────────────────────────────────────

PLAN_LIMITS: dict[str, dict[str, int | float]] = {
    "free": {
        "max_campaigns": 5, "max_team_members": 3,
        "max_emails_per_month": 1000, "max_storage_mb": 100,
        "max_api_requests_per_day": 1000,
    },
    "starter": {
        "max_campaigns": 20, "max_team_members": 10,
        "max_emails_per_month": 10000, "max_storage_mb": 500,
        "max_api_requests_per_day": 10000,
    },
    "professional": {
        "max_campaigns": 100, "max_team_members": 50,
        "max_emails_per_month": 100000, "max_storage_mb": 2000,
        "max_api_requests_per_day": 50000,
    },
    "business": {
        "max_campaigns": 500, "max_team_members": 200,
        "max_emails_per_month": 1000000, "max_storage_mb": 10000,
        "max_api_requests_per_day": 200000,
    },
    "enterprise": {
        "max_campaigns": -1, "max_team_members": -1,
        "max_emails_per_month": -1, "max_storage_mb": -1,
        "max_api_requests_per_day": -1,
    },
}


@dataclass
class BillingPlan:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    plan_tier: str = "free"
    billing_cycle: str = "monthly"
    subscription_status: str = "active"
    current_period_start: datetime = field(default_factory=now)
    current_period_end: datetime = field(default_factory=now)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, organization_id: UUID, plan_tier: str = "free") -> "BillingPlan":
        if plan_tier not in VALID_PLANS:
            raise ValidationError(f"Invalid plan tier: {plan_tier}")
        from datetime import timedelta
        current_time = now()
        return cls(
            organization_id=organization_id,
            plan_tier=plan_tier,
            current_period_start=current_time,
            current_period_end=current_time + timedelta(days=30),
        )

    def change_plan(self, new_tier: str) -> None:
        if new_tier not in VALID_PLANS:
            raise ValidationError(f"Invalid plan tier: {new_tier}")
        self.plan_tier = new_tier
        self.updated_at = now()

    def get_limits(self) -> dict[str, int | float]:
        return dict(PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS["free"]))

    def is_active(self) -> bool:
        return self.subscription_status == "active"
