import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/reports/api/useReports', () => ({
  useReportTemplates: () => ({ data: [] }),
  useCreateReportTemplate: () => ({ mutate: vi.fn() }),
  useDeleteReportTemplate: () => ({ mutate: vi.fn() }),
  useReportSchedules: () => ({ data: [] }),
  useCreateReportSchedule: () => ({ mutate: vi.fn() }),
  useDeleteReportSchedule: () => ({ mutate: vi.fn() }),
  useDeliveryLogs: () => ({ data: [] }),
  useDeliverReport: () => ({ mutate: vi.fn() }),
  useComparePeriods: () => ({ mutate: vi.fn() }),
  getReportExportUrl: () => '#',
}));

import ReportsPage from './page';

describe('ReportsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<ReportsPage />);
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('shows sidebar tabs', () => {
    render(<ReportsPage />);
    expect(screen.getByText('Templates')).toBeInTheDocument();
    expect(screen.getByText('Schedules')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByText('Deliver')).toBeInTheDocument();
    expect(screen.getByText('Compare')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('opens template creation form', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('New Template'));
    expect(screen.getByPlaceholderText('Template name')).toBeInTheDocument();
  });

  it('switches to schedules tab', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('Schedules'));
    expect(screen.getByText('Scheduled Reports')).toBeInTheDocument();
  });

  it('switches to export tab', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('Export'));
    expect(screen.getByText('Export Report')).toBeInTheDocument();
  });

  it('switches to deliver tab', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('Deliver'));
    expect(screen.getByText('Deliver Report')).toBeInTheDocument();
  });
});
