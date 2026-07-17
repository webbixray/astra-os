import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateSchedule = vi.fn();

vi.mock('@/features/reports/api/useReports', () => ({
  useReportSchedules: () => ({ data: [], isLoading: false }),
  useCreateReportSchedule: () => ({ mutateAsync: mockCreateSchedule }),
  useDeleteReportSchedule: () => ({ mutate: vi.fn() }),
}));

import ScheduledReportsPage from './page';

describe('ScheduledReportsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<ScheduledReportsPage />);
    expect(screen.getByText('Scheduled Reports')).toBeInTheDocument();
  });

  it('opens create form', async () => {
    const user = userEvent.setup();
    render(<ScheduledReportsPage />);
    await user.click(screen.getByText('New Schedule'));
    expect(screen.getByPlaceholderText('Report Name')).toBeInTheDocument();
  });

  it('creates a schedule', async () => {
    const user = userEvent.setup();
    render(<ScheduledReportsPage />);
    await user.click(screen.getByText('New Schedule'));

    await user.type(screen.getByPlaceholderText('Report Name'), 'Weekly Overview');
    await user.type(screen.getByPlaceholderText(/Recipients/), 'team@test.com');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockCreateSchedule).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Weekly Overview',
        report_type: 'overview',
        frequency: 'weekly',
        recipients: ['team@test.com'],
      });
    });
  });
});
