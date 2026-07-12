"""Audit API routes — tamper-evident audit log, export, verification.

Endpoints:
  POST   /governance/audit/verify       - Verify hash chain integrity
  POST   /governance/audit/export       - Export audit entries (GDPR/CCPA)
  GET    /governance/audit/summary       - Audit summary for org
  GET    /governance/audit/retention     - Check retention policy
"""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from app.domain.services.governance.audit_enhancement import (
    AuditEnhancementService,
    AuditEntry,
)

router = APIRouter(prefix="/governance/audit", tags=["governance", "audit"])


class VerifyChainRequest(BaseModel):
    entries: list[dict]


class ExportEntriesRequest(BaseModel):
    entries: list[dict]
    include_pii: bool = True


# ── Service (stateless, no DB needed) ──────────────────────────────────

_audit_service = AuditEnhancementService()


def _dict_to_audit_entry(d: dict) -> AuditEntry:
    """Convert a dict back to an AuditEntry for service methods."""
    from datetime import datetime
    return AuditEntry(
        id=d.get("id", ""),
        event_type=d.get("event_type", ""),
        entity_type=d.get("entity_type", ""),
        entity_id=d.get("entity_id", ""),
        user_id=d.get("user_id", ""),
        organization_id=d.get("organization_id", ""),
        action=d.get("action", ""),
        details=d.get("details", {}),
        ip_address=d.get("ip_address", ""),
        entry_hash=d.get("entry_hash", ""),
        previous_hash=d.get("previous_hash", ""),
        created_at=datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.now(),
    )


@router.post("/verify")
async def verify_chain(body: VerifyChainRequest):
    """Verify the integrity of an audit log hash chain."""
    entries = [_dict_to_audit_entry(e) for e in body.entries]
    is_valid = _audit_service.verify_chain(entries)
    return {
        "valid": is_valid,
        "entries_checked": len(entries),
    }


@router.post("/export")
async def export_entries(body: ExportEntriesRequest):
    """Export audit entries in a sanitized format (GDPR/CCPA compliant)."""
    entries = [_dict_to_audit_entry(e) for e in body.entries]
    exported = _audit_service.export_entries(entries, include_pii=body.include_pii)
    return {
        "entries": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "details": e.details,
                "created_at": e.created_at,
                "entry_hash": e.entry_hash,
            }
            for e in exported
        ],
        "total": len(exported),
        "include_pii": body.include_pii,
    }


@router.get("/retention")
async def check_retention():
    """Get retention policy information."""
    cutoff = _audit_service.get_retention_cutoff(retention_years=7)
    return {
        "retention_years": 7,
        "retention_cutoff_date": cutoff.isoformat(),
        "policy": "Immutable append-only log with 7-year retention. Archive, never delete.",
    }
