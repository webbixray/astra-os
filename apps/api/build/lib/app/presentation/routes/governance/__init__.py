"""Governance API routes — approval, autonomy, and audit endpoints."""

from app.presentation.routes.governance.approval_routes import router as approval_router
from app.presentation.routes.governance.audit_routes import router as audit_router
from app.presentation.routes.governance.autonomy_routes import router as autonomy_router

__all__ = ["approval_router", "audit_router", "autonomy_router"]
