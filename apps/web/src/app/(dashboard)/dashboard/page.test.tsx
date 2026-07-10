import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockMutateAsync = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/dashboards/api/useDashboards', () => ({
  useDashboards: () => ({ data: [{ id: 'db-1', name: 'Main Dashboard' }], isLoading: false }),
  useCreateDashboard: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
  useUpdateDashboard: () => ({ mutateAsync: vi.fn() }),
  useDeleteDashboard: () => ({ mutate: vi.fn() }),
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
