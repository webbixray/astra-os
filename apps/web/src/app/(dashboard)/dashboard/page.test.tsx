import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockPush = vi.fn();
const mockMutateAsync = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/analytics/api/useDashboards', () => ({
  useDashboards: () => ({ data: [{ id: 'db-1', name: 'Main Dashboard' }], isLoading: false }),
  useDashboardDetail: () => ({ data: null }),
  useCreateDashboard: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
  useDeleteDashboard: () => ({ mutate: vi.fn(), isPending: false }),
  useAddWidget: () => ({ mutate: vi.fn() }),
  useDeleteWidget: () => ({ mutate: vi.fn() }),
  useDashboardData: () => ({ data: null }),
  useAnomalies: () => ({ data: [] }),
  usePredictions: () => ({ data: [] }),
}));

import DashboardPage from './page';

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<DashboardPage />);
    expect(screen.getByText('Dashboards')).toBeInTheDocument();
  });

  it('shows existing dashboards', () => {
    render(<DashboardPage />);
    expect(screen.getByText('Main Dashboard')).toBeInTheDocument();
  });
});
