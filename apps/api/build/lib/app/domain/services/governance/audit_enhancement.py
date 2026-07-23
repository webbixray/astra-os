"""Audit Enhancement — tamper-evident hashing, immutable audit log support.

Per M3 exit criteria:
  - Audit log: append-only, queryable, exportable, 7-year retention

This service provides:
1. SHA-256 hash chain for tamper evidence (each entry hashes the previous)
2. Audit entry serialization for consistent hashing
3. Verification of hash chain integrity
4. Export formatting (GDPR/CCPA compliant)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.domain.common import now


@dataclass
class AuditEntry:
    """A single audit log entry with tamper-evident hashing."""

    id: str = ""
    event_type: str = ""
    entity_type: str = ""
    entity_id: str = ""
    user_id: str = ""
    organization_id: str = ""

    # Action details
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""

    # Hash chain
    entry_hash: str = ""
    previous_hash: str = ""

    # Timing
    created_at: datetime = field(default_factory=now)

    def to_hash_payload(self) -> str:
        """Generate a deterministic payload for hashing."""
        payload = {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "previous_hash": self.previous_hash,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass
class AuditExportEntry:
    """Sanitized audit entry for export (GDPR/CCPA)."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    details: dict[str, Any]
    created_at: str
    entry_hash: str


class AuditEnhancementService:
    """Stateless service for tamper-evident audit logging.

    Usage:
        service = AuditEnhancementService()
        entry = service.create_entry(...)
        verified = service.verify_chain(entries)
        export_data = service.export_entries(entries, include_pii=False)
    """

    HASH_ALGORITHM = "sha256"

    def compute_hash(self, entry: AuditEntry) -> str:
        """Compute SHA-256 hash for an audit entry."""
        payload = entry.to_hash_payload()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_entry(
        self,
        *,
        id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: str = "",
        organization_id: str = "",
        action: str = "",
        details: dict[str, Any] | None = None,
        ip_address: str = "",
        previous_hash: str = "",
    ) -> AuditEntry:
        """Create and hash a new audit entry."""
        entry = AuditEntry(
            id=id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            previous_hash=previous_hash,
            created_at=now(),
        )
        entry.entry_hash = self.compute_hash(entry)
        return entry

    def verify_chain(self, entries: list[AuditEntry]) -> bool:
        """Verify the integrity of a hash chain.

        Returns True if all entries hash correctly and the chain is unbroken.
        """
        if not entries:
            return True

        for i, entry in enumerate(entries):
            # Verify the entry's own hash
            expected_hash = self.compute_hash(entry)
            if entry.entry_hash != expected_hash:
                return False

            # Verify chain linkage
            if i > 0:
                if entry.previous_hash != entries[i - 1].entry_hash:
                    return False

        return True

    def verify_single(self, entry: AuditEntry) -> bool:
        """Verify a single entry's hash is correct."""
        return entry.entry_hash == self.compute_hash(entry)

    def get_retention_cutoff(
        self,
        retention_years: int = 7,
        reference_date: datetime | None = None,
    ) -> datetime:
        """Get the cutoff date for audit log retention.

        Per M3 exit criteria: 7-year retention.
        Entries older than this should be archived, not deleted.
        """
        ref = reference_date or now()
        return ref - timedelta(days=retention_years * 365)

    def should_archive(
        self,
        entry: AuditEntry,
        retention_years: int = 7,
        reference_date: datetime | None = None,
    ) -> bool:
        """Check if an entry should be archived based on retention policy."""
        cutoff = self.get_retention_cutoff(retention_years, reference_date)
        return entry.created_at < cutoff

    def export_entries(
        self,
        entries: list[AuditEntry],
        include_pii: bool = True,
        format: str = "json",
    ) -> list[AuditExportEntry]:
        """Export audit entries in a compliant format.

        Args:
            entries: Audit entries to export.
            include_pii: If False, strips user_id and ip_address (GDPR).
            format: Export format ("json" or "csv" — CSV returned as list of dicts).

        Returns:
            List of sanitized AuditExportEntry objects.

        """
        exported: list[AuditExportEntry] = []

        for entry in entries:
            export_entry = AuditExportEntry(
                id=entry.id,
                event_type=entry.event_type,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                action=entry.action,
                details=entry.details,
                created_at=entry.created_at.isoformat(),
                entry_hash=entry.entry_hash,
            )

            # Strip PII if not included
            if not include_pii:
                export_entry.details = {
                    k: v
                    for k, v in entry.details.items()
                    if k.lower() not in ("email", "name", "ip_address", "phone")
                }

            exported.append(export_entry)

        return exported

    def generate_export_summary(
        self,
        entries: list[AuditEntry],
        organization_id: str = "",
    ) -> dict[str, Any]:
        """Generate a summary for export reporting."""
        total = len(entries)
        events_by_type: dict[str, int] = {}
        for e in entries:
            events_by_type[e.event_type] = events_by_type.get(e.event_type, 0) + 1

        date_range: dict[str, str] = {}
        if entries:
            sorted_entries = sorted(entries, key=lambda e: e.created_at)
            date_range["start"] = sorted_entries[0].created_at.isoformat()
            date_range["end"] = sorted_entries[-1].created_at.isoformat()

        chain_valid = self.verify_chain(entries)

        return {
            "organization_id": organization_id,
            "total_entries": total,
            "events_by_type": events_by_type,
            "date_range": date_range,
            "chain_valid": chain_valid,
            "retention_years": 7,
        }
