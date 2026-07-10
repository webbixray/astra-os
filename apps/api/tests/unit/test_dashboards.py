from uuid import uuid4

import pytest

from app.domain.entities.dashboards.dashboard import (
    WIDGET_TYPES,
    Dashboard,
    DashboardWidget,
)
from app.domain.exceptions.domain_exceptions import ValidationError


class TestDashboardWidget:
    def test_create_valid_widget(self):
        dash_id = uuid4()
        w = DashboardWidget.create(
            dashboard_id=dash_id,
            widget_type="kpi_card",
            title="Revenue",
            pos_x=0,
            pos_y=0,
            width=3,
            height=2,
            config={"metric": "revenue"},
        )
        assert w.dashboard_id == dash_id
        assert w.widget_type == "kpi_card"
        assert w.title == "Revenue"
        assert w.pos_x == 0
        assert w.width == 3
        assert w.height == 2
        assert w.config == {"metric": "revenue"}

    def test_invalid_widget_type_raises(self):
        with pytest.raises(ValidationError, match="Invalid widget type"):
            DashboardWidget.create(dashboard_id=uuid4(), widget_type="not_a_type", title="X")

    def test_invalid_width_raises(self):
        with pytest.raises(ValidationError, match="dimensions must be positive"):
            DashboardWidget.create(dashboard_id=uuid4(), widget_type="kpi_card", title="X", width=0)

    def test_invalid_height_raises(self):
        with pytest.raises(ValidationError, match="dimensions must be positive"):
            DashboardWidget.create(dashboard_id=uuid4(), widget_type="kpi_card", title="X", height=0)

    def test_default_config(self):
        w = DashboardWidget.create(dashboard_id=uuid4(), widget_type="kpi_card", title="X")
        assert w.config == {}


class TestDashboard:
    def test_create_valid_dashboard(self):
        org_id = uuid4()
        user_id = uuid4()
        d = Dashboard.create(
            organization_id=org_id,
            name="My Dashboard",
            created_by=user_id,
            description="desc",
            layout_columns=24,
        )
        assert d.organization_id == org_id
        assert d.name == "My Dashboard"
        assert d.description == "desc"
        assert d.layout_columns == 24
        assert d.created_by == user_id
        assert d.widgets == []
        assert d.is_default is False

    def test_create_blank_name_raises(self):
        with pytest.raises(ValidationError, match="Dashboard name is required"):
            Dashboard.create(organization_id=uuid4(), name="", created_by=uuid4())
        with pytest.raises(ValidationError, match="Dashboard name is required"):
            Dashboard.create(organization_id=uuid4(), name="   ", created_by=uuid4())

    def test_add_widget(self):
        d = Dashboard.create(organization_id=uuid4(), name="X", created_by=uuid4())
        w = DashboardWidget.create(dashboard_id=d.id, widget_type="line_chart", title="Chart")
        d.add_widget(w)
        assert len(d.widgets) == 1
        assert w in d.widgets

    def test_remove_widget(self):
        d = Dashboard.create(organization_id=uuid4(), name="X", created_by=uuid4())
        w = DashboardWidget.create(dashboard_id=d.id, widget_type="line_chart", title="Chart")
        d.add_widget(w)
        d.remove_widget(w.id)
        assert len(d.widgets) == 0


class TestWIDGET_TYPES:
    def test_known_types(self):
        assert "kpi_card" in WIDGET_TYPES
        assert "line_chart" in WIDGET_TYPES
        assert "bar_chart" in WIDGET_TYPES
        assert "pie_chart" in WIDGET_TYPES
        assert "data_table" in WIDGET_TYPES
        assert "trend_indicator" in WIDGET_TYPES
        assert len(WIDGET_TYPES) == 6
