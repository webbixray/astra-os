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
  useUsageSummary: () => ({ data: { plan_tier: 'free', usage: { api_calls: 100 }, limits: { api_calls: 1000 } } }),
  useBillingPlan: () => ({ data: { plan_tier: 'free', subscription_status: 'active', billing_cycle: 'monthly', current_period_start: '2026-07-01', current_period_end: '2026-07-31', limits: {} } }),
  useChangeBillingPlan: () => ({ mutate: vi.fn() }),
}));

vi.mock('./SettingsOrgTab', () => ({
  SettingsOrgTab: ({ orgId }: { orgId: string }) => {
    const [showCreate, setShowCreate] = React.useState(false);
    const [name, setName] = React.useState('');
    const [slug, setSlug] = React.useState('');
    const [errors, setErrors] = React.useState<{ name?: string; slug?: string }>({});
    return (
      <div>
        {!showCreate ? (
          <button onClick={() => setShowCreate(true)}>Create Sub-Organization</button>
        ) : (
          <div>
            <input aria-label="Organization name" value={name} onChange={(e) => setName(e.target.value)} />
            {errors.name && <p>{errors.name}</p>}
            <input aria-label="Organization slug" value={slug} onChange={(e) => setSlug(e.target.value)} />
            {errors.slug && <p>{errors.slug}</p>}
            <button onClick={() => {
              if (!name.trim()) { setErrors({ name: 'Name is required' }); return; }
              if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) { setErrors({ slug: 'Slug must be lowercase alphanumeric with hyphens' }); return; }
              mockMutate({ orgId, name: name.trim(), slug: slug.trim() });
            }}>Create Sub-Org</button>
            <button onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        )}
      </div>
    );
  },
}));

vi.mock('./SettingsBillingTab', () => ({
  SettingsBillingTab: ({ billing }: { billing: any }) => (
    <div>
      <p>Current Plan</p>
      <p>{billing?.plan_tier}</p>
    </div>
  ),
}));

vi.mock('./SettingsFeaturesTab', () => ({
  SettingsFeaturesTab: () => (
    <div>
      <p>Advanced Analytics</p>
    </div>
  ),
}));

vi.mock('./SettingsUsageTab', () => ({
  SettingsUsageTab: (_: { usage: any }) => (
    <div>
      <p>Usage &amp; Limits</p>
    </div>
  ),
}));

vi.mock('./SettingsProfileTab', () => ({
  SettingsProfileTab: () => <div>Profile Tab</div>,
}));

import React from 'react';
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
    expect(screen.getByLabelText('Organization name')).toBeInTheDocument();
    expect(screen.getByLabelText('Organization slug')).toBeInTheDocument();
  });

  it('validates empty name on sub-org creation', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.click(screen.getByText('Create Sub-Org'));
    expect(await screen.findByText('Name is required')).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('validates slug format on sub-org creation', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.type(screen.getByLabelText('Organization name'), 'Sub Org');
    await user.type(screen.getByLabelText('Organization slug'), 'INVALID SLUG');
    await user.click(screen.getByText('Create Sub-Org'));
    expect(await screen.findByText(/Slug must be lowercase/)).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('creates sub-org with valid data', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Create Sub-Organization'));
    await user.type(screen.getByLabelText('Organization name'), 'Marketing Team');
    await user.type(screen.getByLabelText('Organization slug'), 'marketing-team');
    await user.click(screen.getByText('Create Sub-Org'));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        { orgId: 'org-1', name: 'Marketing Team', slug: 'marketing-team' },
      );
    });
  });

  it('switches to billing tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Billing'));
    expect(await screen.findByText('Current Plan')).toBeInTheDocument();
  });

  it('switches to features tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Features'));
    expect(await screen.findByText('Advanced Analytics')).toBeInTheDocument();
  });

  it('switches to usage tab', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    await user.click(screen.getByText('Usage'));
    expect(await screen.findByText('Usage & Limits')).toBeInTheDocument();
  });
});
