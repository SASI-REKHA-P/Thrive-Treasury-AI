from typing import List, Optional
from app.models.audit import AuditEvent


class AuditService:
    """
    In-memory audit store providing decision traceability and lifecycle event tracking.
    Preserves chronological event ordering and filtering by order_id.
    """

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def append_event(self, event: AuditEvent) -> AuditEvent:
        """Append an authentic audit event to the chronological log."""
        self._events.append(event)
        return event

    def get_events(self, order_id: Optional[str] = None) -> List[AuditEvent]:
        """
        Retrieve audit events in deterministic chronological order (newest first).
        Optionally filter by order_id.
        """
        events = self._events
        if order_id:
            events = [e for e in events if e.order_id == order_id]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)

    def clear(self) -> int:
        """Reset in-memory audit store and return number of events removed."""
        count = len(self._events)
        self._events.clear()
        return count



# Global in-memory audit service singleton for the running Python process
audit_service = AuditService()
