import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/analytics/api/useAnalytics', () => ({
  useAnalyticsOverview: () => ({
    data: {
      total_campaigns: 10, active_campaigns: 4, draft_campaigns: 3,
      total_content: 25, published_content: 15, total_budget: 50000,
      status_breakdown: { draft: 3, active: 4, completed: 2, archived: 1 },
    },
  }),
  useCampaignPerformance: () => ({
    data: [
      { id: 'c-1', name: 'Summer Sale', status: 'active', budget: 10000, spend: 4500,
        impressions: 50000, clicks: 1200, conversions: 85, revenue: 15000, roi: 233 },
    ],
  }),
  useAdPerformance: () => ({
    data: {
      total_impressions: 100000, total_clicks: 2500, ctr: 2.5,
      total_conversions: 150, conversion_rate: 6.0, roi: 180, total_spend: 20000,
      platforms: [
        { name: 'google', campaigns: [{ id: 'g-1', name: 'Google Ads', spend: 10000, impressions: 50000, clicks: 1200, conversions: 80, revenue: 12000 }] },
      ],
    },
  }),
}));

vi.mock('@/features/reports/api/useReports', () => ({
  useReportTrends: () => ({
    data: { total: 10000, average: 333, peak: 500, metric: 'spend', daily: [{ date: '2024-01-01', value: 300 }] },
  }),
}));

import AnalyticsPage from './page';

describe('AnalyticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('Analytics & Reports')).toBeInTheDocument();
  });

  it('shows overview tab by default with stat cards', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
    expect(screen.getByText('Active Campaigns')).toBeInTheDocument();
    expect(screen.getByText('Content Pieces')).toBeInTheDocument();
  });

  it('shows status breakdown chart', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('Campaign Status Breakdown')).toBeInTheDocument();
  });

  it('switches to campaigns tab', async () => {
    const user = userEvent.setup();
    render(<AnalyticsPage />);
    await user.click(screen.getByText('Campaigns'));
    expect(screen.getByText('Summer Sale')).toBeInTheDocument();
    expect(screen.getByText('233%')).toBeInTheDocument();
  });

  it('switches to platform ads tab', async () => {
    const user = userEvent.setup();
    render(<AnalyticsPage />);
    await user.click(screen.getByText('Platform Ads'));
    expect(screen.getByText('2.50%')).toBeInTheDocument();
    expect(screen.getByText('google')).toBeInTheDocument();
  });

  it('switches to trends tab', async () => {
    const user = userEvent.setup();
    render(<AnalyticsPage />);
    await user.click(screen.getByText('Trends'));
    expect(screen.getByText('spend')).toBeInTheDocument();
    expect(screen.getByText('$10,000')).toBeInTheDocument();
  });

  it('shows schedule reports link', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('Scheduled Reports')).toBeInTheDocument();
  });
});
