import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
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

vi.mock('./ReportsTemplatesTab', () => ({
  ReportsTemplatesTab: () => (
    <div>
      <button>New Template</button>
      <input placeholder="Template name" />
    </div>
  ),
}));

vi.mock('./ReportsSchedulesTab', () => ({
  ReportsSchedulesTab: () => <div>Scheduled Reports</div>,
}));

vi.mock('./ReportsExportTab', () => ({
  ReportsExportTab: () => <div>Export Report</div>,
}));

vi.mock('./ReportsDeliverTab', () => ({
  ReportsDeliverTab: () => <div>Deliver Report</div>,
}));

vi.mock('./ReportsCompareTab', () => ({
  ReportsCompareTab: () => <div>Compare</div>,
}));

vi.mock('./ReportsLogsTab', () => ({
  ReportsLogsTab: () => <div>History</div>,
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
    expect(await screen.findByText('Scheduled Reports')).toBeInTheDocument();
  });

  it('switches to export tab', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('Export'));
    expect(await screen.findByText('Export Report')).toBeInTheDocument();
  });

  it('switches to deliver tab', async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);
    await user.click(screen.getByText('Deliver'));
    expect(await screen.findByText('Deliver Report')).toBeInTheDocument();
  });
});
