import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.monitoring.dashboards.impact_dashboard import ImpactDashboardService


@pytest.mark.asyncio
async def test_get_live_impact_metrics():
    with patch("app.monitoring.dashboards.impact_dashboard.get_async_session") as mock_session:
        mock_session.return_value.__aiter__.return_value = [AsyncMock()]
        mock_session.return_value.__aenter__.return_value.execute.return_value.scalar_one.side_effect = [
            100,  # total users
            150,  # total plans
            47,  # evictions avoided
            200  # SMS sent
        ]
        mock_session.return_value.__aenter__.return_value.execute.return_value.all.side_effect = [
            [("CRITICAL", 50), ("HIGH", 75), ("MEDIUM", 25)],
            [("TX", 60), ("CA", 40), ("NY", 30), ("FL",20), ("IL",10)],
            [("EN", 130), ("ES",20)]
        ]

        metrics = await ImpactDashboardService.get_live_impact_metrics()
        assert metrics["total_users_helped"] == 100
        assert metrics["evictions_avoided"] ==47
        assert "urgency_breakdown" in metrics
        assert "top_states" in metrics


@pytest.mark.asyncio
async def test_get_daily_trend():
    with patch("app.monitoring.dashboards.impact_dashboard.get_async_session") as mock_session:
        mock_session.return_value.__aiter__.return_value = [AsyncMock()]
        from datetime import date
        mock_session.return_value.__aenter__.return_value.execute.return_value.all.return_value = [
            (date(2026,6,15), 20,8),
            (date(2026,6,16), 25,10),
            (date(2026,6,17), 30,15),
        ]

        trend = await ImpactDashboardService.get_daily_trend(days=7)
        assert len(trend) ==3
        assert trend[0]["date"] == "2026-06-15"
