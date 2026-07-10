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

import MonitoringPage from './page';

describe('MonitoringPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<MonitoringPage />);
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
  });

  it('shows audit tab by default', () => {
    render(<MonitoringPage />);
    expect(screen.getByText('Audit Log')).toBeInTheDocument();
  });

  it('switches to jobs tab', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByText('Jobs'));
    expect(screen.getByText('New Job')).toBeInTheDocument();
  });

  it('creates a job', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByText('Jobs'));
    await user.click(screen.getByText('New Job'));

    await user.type(screen.getByPlaceholderText(/Job type/), 'data_sync');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockCreateJob).toHaveBeenCalled();
    });
  });

  it('switches to usage tab', async () => {
    const user = userEvent.setup();
    render(<MonitoringPage />);
    await user.click(screen.getByText('Usage'));
    expect(screen.getByText('API Usage')).toBeInTheDocument();
  });
});
