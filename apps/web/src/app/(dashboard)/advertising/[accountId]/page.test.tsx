import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('next/navigation', () => ({
  useParams: () => ({ accountId: 'acc-1' }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateCampaign = vi.fn();

vi.mock('@/features/advertising/api/useAdvertising', () => ({
  useAdCampaigns: () => ({ data: [], isLoading: false }),
  useCreateAdCampaign: () => ({ mutateAsync: mockCreateCampaign, isPending: false }),
}));

import AccountCampaignsPage from './page';

describe('AccountCampaignsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<AccountCampaignsPage />);
    expect(screen.getByText('Campaigns')).toBeInTheDocument();
  });

  it('opens create form', async () => {
    const user = userEvent.setup();
    render(<AccountCampaignsPage />);
    await user.click(screen.getByText('New Campaign'));
    expect(screen.getByPlaceholderText('Campaign Name')).toBeInTheDocument();
  });

  it('creates an ad campaign', async () => {
    const user = userEvent.setup();
    render(<AccountCampaignsPage />);
    await user.click(screen.getByText('New Campaign'));

    await user.type(screen.getByPlaceholderText('Campaign Name'), 'Holiday Sale');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockCreateCampaign).toHaveBeenCalledWith({
        organization_id: 'org-1',
        ad_account_id: 'acc-1',
        name: 'Holiday Sale',
        objective: 'awareness',
      });
    });
  });
});
