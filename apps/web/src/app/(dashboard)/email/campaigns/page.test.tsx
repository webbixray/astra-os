import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateCampaign = vi.fn();

vi.mock('@/features/email/api/useEmail', () => ({
  useEmailCampaigns: () => ({ data: [], isLoading: false }),
  useCreateEmailCampaign: () => ({ mutateAsync: mockCreateCampaign, isPending: false }),
  useSendEmailCampaign: () => ({ mutate: vi.fn() }),
  useDeleteEmailCampaign: () => ({ mutate: vi.fn() }),
  useEmailProviders: () => ({ data: [{ id: 'prov-1', name: 'SendGrid', provider_type: 'sendgrid', from_email: 'noreply@test.com' }] }),
  useEmailAnalytics: () => ({ data: null }),
}));

import EmailCampaignsPage from './page';

describe('EmailCampaignsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<EmailCampaignsPage />);
    expect(screen.getByText('Email Campaigns')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<EmailCampaignsPage />);
    expect(screen.getByText('No email campaigns yet')).toBeInTheDocument();
  });

  it('opens new campaign form', { timeout: 15000 }, async () => {
    const user = userEvent.setup();
    render(<EmailCampaignsPage />);
    await user.click(screen.getAllByText('New Campaign')[0]!);
    expect(screen.getByPlaceholderText('Campaign name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Subject')).toBeInTheDocument();
  });

  it('creates a campaign', { timeout: 15000 }, async () => {
    const user = userEvent.setup();
    render(<EmailCampaignsPage />);
    await user.click(screen.getAllByText('New Campaign')[0]!);

    await user.type(screen.getByPlaceholderText('Campaign name'), 'Weekly Newsletter');
    await user.type(screen.getByPlaceholderText('Subject'), 'Issue #42');
    await user.type(screen.getByPlaceholderText(/Email body/), 'Hello world!');
    await user.selectOptions(screen.getByLabelText('Provider'), 'prov-1');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockCreateCampaign).toHaveBeenCalledWith({
        organization_id: 'org-1',
        provider_id: 'prov-1',
        name: 'Weekly Newsletter',
        subject: 'Issue #42',
        body: 'Hello world!',
        from_email: 'noreply@test.com',
      });
    });
  });
});
