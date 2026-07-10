import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockLogout = vi.fn();
const mockMutate = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/lib/auth', () => ({
  useAuth: () => ({ user: { email: 'admin@test.com' }, logout: mockLogout }),
}));

vi.mock('@/features/organizations/api/useOrganizations', () => ({
  useOrgTree: () => ({ data: null }),
  useCreateSubOrg: () => ({ mutate: mockMutate }),
  useFeatureFlags: () => ({ data: [] }),
  useSetFeatureFlag: () => vi.fn(),
  useUsageSummary: () => ({ data: null }),
  useBillingPlan: () => ({ data: null }),
  useChangeBillingPlan: () => vi.fn(),
}));

import SettingsPage from './page';

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page title and tabs', () => {
    render(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Organization')).toBeInTheDocument();
    expect(screen.getByText('Billing')).toBeInTheDocument();
    expect(screen.getByText('Features')).toBeInTheDocument();
    expect(screen.getByText('Usage')).toBeInTheDocument();
  });

  it('shows sub-org creation form when button is clicked', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    expect(screen.getByLabelText('Organization Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Slug')).toBeInTheDocument();
  });

  it('validates empty name on sub-org creation', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.click(screen.getByText('Create'));
    expect(await screen.findByText('Name is required')).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('validates slug format on sub-org creation', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.type(screen.getByLabelText('Organization Name'), 'Sub Org');
    await user.type(screen.getByLabelText('Slug'), 'INVALID SLUG');
    await user.click(screen.getByText('Create'));
    expect(await screen.findByText(/Slug must be lowercase/)).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('creates sub-org with valid data', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.type(screen.getByLabelText('Organization Name'), 'Marketing Team');
    await user.type(screen.getByLabelText('Slug'), 'marketing-team');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        { orgId: 'org-1', name: 'Marketing Team', slug: 'marketing-team' },
        expect.any(Object),
      );
    });
  });

  it('switches to billing tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Billing'));
    expect(screen.getByText('Current Plan')).toBeInTheDocument();
  });

  it('switches to features tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Features'));
    expect(screen.getByText('Advanced Analytics')).toBeInTheDocument();
  });

  it('switches to usage tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Usage'));
    expect(screen.getByText('API Usage Summary')).toBeInTheDocument();
  });
});
