from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.calendar.calendar_service import CalendarService


def make_campaign_model(**kw):
    m = MagicMock()
    m.id = kw.get("id", uuid4())
    m.name = kw.get("name", "Test Campaign")
    m.status = kw.get("status", "active")
    m.start_date = kw.get("start_date")
    m.end_date = kw.get("end_date")
    return m


def make_content_model(**kw):
    m = MagicMock()
    m.id = kw.get("id", uuid4())
    m.title = kw.get("title", "Test Content")
    m.status = kw.get("status", "draft")
    m.scheduled_at = kw.get("scheduled_at")
    m.published_at = kw.get("published_at")
    return m


def make_ad_campaign_model(**kw):
    m = MagicMock()
    m.id = kw.get("id", uuid4())
    m.name = kw.get("name", "Test Ad")
    m.status = kw.get("status", "active")
    m.start_date = kw.get("start_date")
    m.end_date = kw.get("end_date")
    m.ad_account_id = kw.get("ad_account_id", uuid4())
    return m


def _make_result(models: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


class TestCalendarService:
    @pytest.fixture
    def session(self):
        s = MagicMock()
        s.execute = AsyncMock()
        return s

    @pytest.fixture
    def service(self, session):
        return CalendarService(session=session)

    async def test_get_events_empty(self, service, session):
        empty = _make_result([])
        session.execute.side_effect = [empty, empty, empty]

        events = await service.get_events(uuid4(), "2025-01-01", "2025-01-31")

        assert events == []

    async def test_get_events_with_campaigns(self, service, session):
        org_id = uuid4()
        camp = make_campaign_model(
            name="Launch Campaign",
            start_date=MagicMock(isoformat=lambda: "2025-01-15"),
            end_date=MagicMock(isoformat=lambda: "2025-02-15"),
        )
        empty = _make_result([])
        session.execute.side_effect = [
            _make_result([camp]),
            empty,
            empty,
        ]

        events = await service.get_events(org_id, "2025-01-01", "2025-01-31")

        assert len(events) == 1
        assert events[0]["type"] == "campaign"
        assert events[0]["title"] == "Launch Campaign"
        assert events[0]["link"] == f"/campaigns/{camp.id}"

    async def test_get_events_sorts_by_date(self, service, session):
        org_id = uuid4()
        camp_a = make_campaign_model(
            name="A",
            start_date=MagicMock(isoformat=lambda: "2025-01-20"),
            end_date=None,
        )
        camp_b = make_campaign_model(
            name="B",
            start_date=MagicMock(isoformat=lambda: "2025-01-10"),
            end_date=None,
        )
        empty = _make_result([])
        session.execute.side_effect = [
            _make_result([camp_a, camp_b]),
            empty,
            empty,
        ]

        events = await service.get_events(org_id, "2025-01-01", "2025-01-31")

        assert len(events) == 2
        assert events[0]["title"] == "B"
        assert events[1]["title"] == "A"

    async def test_get_events_with_all_types(self, service, session):
        org_id = uuid4()
        camp = make_campaign_model(
            name="Campaign",
            start_date=MagicMock(isoformat=lambda: "2025-01-15"),
        )
        content = make_content_model(
            title="Blog Post",
            scheduled_at=MagicMock(isoformat=lambda: "2025-01-16"),
        )
        ad = make_ad_campaign_model(
            name="Ad Campaign",
            start_date="2025-01-10",
        )
        _make_result([])
        session.execute.side_effect = [
            _make_result([camp]),
            _make_result([content]),
            _make_result([ad]),
        ]

        events = await service.get_events(org_id, "2025-01-01", "2025-01-31")

        assert len(events) == 3
        types = {e["type"] for e in events}
        assert types == {"campaign", "content", "ad_campaign"}

    async def test_calendar_event_to_dict(self):
        from app.application.use_cases.calendar.calendar_service import CalendarEvent

        event = CalendarEvent(
            id="123", type="campaign", title="Test",
            start_date="2025-01-01", end_date="2025-01-31",
            status="active", link="/campaigns/123",
        )
        d = event.to_dict()
        assert d["id"] == "123"
        assert d["type"] == "campaign"
        assert d["title"] == "Test"
        assert d["start_date"] == "2025-01-01"
        assert d["end_date"] == "2025-01-31"
        assert d["status"] == "active"
        assert d["link"] == "/campaigns/123"

    async def test_get_events_invalid_date(self, service, session):
        with pytest.raises(ValueError):
            await service.get_events(uuid4(), "not-a-date", "2025-01-31")

    async def test_content_event_no_dates(self, service, session):
        content = make_content_model(title="Unscheduled", scheduled_at=None, published_at=None)
        empty = _make_result([])
        session.execute.side_effect = [
            empty,
            _make_result([content]),
            empty,
        ]

        events = await service.get_events(uuid4(), "2025-01-01", "2025-01-31")

        assert len(events) == 1
        assert events[0]["title"] == "Unscheduled"
        assert events[0]["start_date"] is None
        assert events[0]["end_date"] is None
