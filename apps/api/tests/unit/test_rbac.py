from app.domain.entities.organization import (
    ORG_ROLE_HIERARCHY,
    ORG_ROLES,
    PERMISSIONS,
    ROLE_DEFAULT_PERMISSIONS,
)
from app.presentation.middleware.rbac import RBAC_HIERARCHY


class TestRBACHierarchy:
    def test_roles_defined(self):
        assert "viewer" in ORG_ROLES
        assert "member" in ORG_ROLES
        assert "admin" in ORG_ROLES
        assert "owner" in ORG_ROLES

    def test_org_role_hierarchy_values(self):
        assert ORG_ROLE_HIERARCHY["viewer"] == 10
        assert ORG_ROLE_HIERARCHY["member"] == 20
        assert ORG_ROLE_HIERARCHY["admin"] == 30
        assert ORG_ROLE_HIERARCHY["owner"] == 40

    def test_rbac_middleware_hierarchy_matches_domain(self):
        """The RBAC middleware's hierarchy must match the domain's hierarchy."""
        assert RBAC_HIERARCHY == ORG_ROLE_HIERARCHY

    def test_role_permission_superset(self):
        """Each higher role should have all permissions of lower roles."""
        role_levels = ["viewer", "member", "admin", "owner"]
        for i, higher in enumerate(role_levels):
            for lower in role_levels[:i]:
                higher_perms = set(ROLE_DEFAULT_PERMISSIONS[higher])
                lower_perms = set(ROLE_DEFAULT_PERMISSIONS[lower])
                assert lower_perms.issubset(higher_perms), (
                    f"'{higher}' missing permissions from '{lower}': {lower_perms - higher_perms}"
                )

    def test_owner_has_all_permissions(self):
        assert set(ROLE_DEFAULT_PERMISSIONS["owner"]) == set(PERMISSIONS)

    def test_viewer_read_only(self):
        viewer_perms = ROLE_DEFAULT_PERMISSIONS["viewer"]
        for perm in viewer_perms:
            assert ":read" in perm or ":" not in perm

    def test_member_can_write_and_publish(self):
        member_perms = ROLE_DEFAULT_PERMISSIONS["member"]
        assert "campaign:write" in member_perms
        assert "content:write" in member_perms
        assert "content:publish" in member_perms
        assert "email:send" in member_perms

    def test_admin_can_delete_and_manage(self):
        admin_perms = ROLE_DEFAULT_PERMISSIONS["admin"]
        assert "org:write" in admin_perms
        assert "campaign:delete" in admin_perms
        assert "content:delete" in admin_perms
        assert "org:manage_members" in admin_perms
        assert "settings:write" in admin_perms

    def test_permissions_are_valid(self):
        all_granted = set()
        for perms in ROLE_DEFAULT_PERMISSIONS.values():
            all_granted.update(perms)
        for perm in all_granted:
            assert perm in PERMISSIONS, f"'{perm}' is not in the valid PERMISSIONS list"

    def test_no_extra_permissions_in_lists(self):
        for role, perms in ROLE_DEFAULT_PERMISSIONS.items():
            for perm in perms:
                assert perm in PERMISSIONS, (
                    f"Role '{role}' has permission '{perm}' which is not in PERMISSIONS"
                )
