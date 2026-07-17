import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateJob = vi.fn();

vi.mock('@/features/monitoring/api/useMonitoring', () => ({
  useAuditLogs: () => ({ data: [] }),
  useAuditSummary: () => ({ data: null }),
  useJobs: () => ({ data: [] }),
  useCreateJob: () => ({ mutateAsync: mockCreateJob, isPending: false }),
  useRetryJob: () => ({ mutate: vi.fn() }),
  useJobSummary: () => ({ data: null }),
  useUsageRecords: () => ({ data: [] }),
  useUsageStats: () => ({ data: null }),
  useSystemHealth: () => ({ data: null }),
}));

vi.mock('./MonitoringAuditTab', () => ({
  MonitoringAuditTab: () => <div>Audit Content</div>,
}));

vi.mock('./MonitoringJobsTab', () => ({
  MonitoringJobsTab: () => (
    <div>
      <button onClick={() => mockCreateJob()}>New Job</button>
    </div>
  ),
}));

vi.mock('./MonitoringUsageTab', () => ({
  MonitoringUsageTab: () => <div>No usage records yet</div>,
}));

vi.mock('./MonitoringHealthTab', () => ({
  MonitoringHealthTab: () => <div>Health</div>,
}));

import MonitoringPage from './page';

describe('MonitoringPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<MonitoringPage />);
    expect(screen.getByText('System Monitoring')).toBeInTheDocument();
  });

  it('shows audit tab by default', async () => {
    render(<MonitoringPage />);
    expect(await screen.findByText('Audit Content')).toBeInTheDocument();
  });

  it('switches to jobs tab', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByText('Jobs'));
    expect(await screen.findByText('New Job')).toBeInTheDocument();
  });

  it('creates a job', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByText('Jobs'));
    await user.click(await screen.findByText('New Job'));

    await waitFor(() => {
      expect(mockCreateJob).toHaveBeenCalled();
    });
  });

  it('switches to usage tab', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByRole('button', { name: /API Usage/ }));
    expect(await screen.findByText('No usage records yet')).toBeInTheDocument();
  });
});
