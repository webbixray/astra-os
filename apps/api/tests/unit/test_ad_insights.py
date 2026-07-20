from uuid import uuid4

from app.domain.entities.advertising.ad_insights import AdInsight


class TestAdInsight:
    def test_create_ad_insight(self):
        insight = AdInsight(
            organization_id=uuid4(),
            ad_account_id=uuid4(),
            date="2025-01-01",
            impressions=1000,
            clicks=50,
            spend=250.00,
            conversions=10,
            revenue=1000.00,
            platform="google",
        )
        assert insight.impressions == 1000
        assert insight.clicks == 50
        assert insight.spend == 250.00
        assert insight.conversions == 10
        assert insight.revenue == 1000.00
        assert insight.platform == "google"

    def test_ctr(self):
        insight = AdInsight(impressions=1000, clicks=50)
        assert insight.ctr == 5.0

    def test_ctr_zero_impressions(self):
        insight = AdInsight(impressions=0, clicks=0)
        assert insight.ctr == 0

    def test_cpc(self):
        insight = AdInsight(clicks=50, spend=250.00)
        assert insight.cpc == 5.0

    def test_cpc_zero_clicks(self):
        insight = AdInsight(clicks=0, spend=100.00)
        assert insight.cpc == 0

    def test_conversion_rate(self):
        insight = AdInsight(clicks=200, conversions=20)
        assert insight.conversion_rate == 10.0

    def test_conversion_rate_zero_clicks(self):
        insight = AdInsight(clicks=0, conversions=5)
        assert insight.conversion_rate == 0

    def test_roas(self):
        insight = AdInsight(spend=250.00, revenue=1000.00)
        assert insight.roas == 4.0

    def test_roas_zero_spend(self):
        insight = AdInsight(spend=0, revenue=500.00)
        assert insight.roas == 0

    def test_all_edge_cases_zero_values(self):
        insight = AdInsight(impressions=0, clicks=0, spend=0, conversions=0, revenue=0)
        assert insight.ctr == 0
        assert insight.cpc == 0
        assert insight.conversion_rate == 0
        assert insight.roas == 0

    def test_computed_properties_rounded(self):
        insight = AdInsight(
            impressions=1000, clicks=33, spend=100.00, conversions=7, revenue=333.33
        )
        assert insight.ctr == 3.3
        assert insight.cpc == 3.03
        assert insight.conversion_rate == 21.21
        assert insight.roas == 3.33
