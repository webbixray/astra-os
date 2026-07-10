import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockConnectAccount = vi.fn();

vi.mock('@/features/advertising/api/useAdvertising', () => ({
  useAdAccounts: () => ({ data: [], isLoading: false }),
  useConnectAccount: () => ({ mutateAsync: mockConnectAccount, isPending: false }),
  useSyncAccount: () => ({ mutate: vi.fn(), isPending: false }),
  useDisconnectAccount: () => ({ mutate: vi.fn() }),
}));

import AdvertisingPage from './page';

describe('AdvertisingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<AdvertisingPage />);
    expect(screen.getByText('Ad Accounts')).toBeInTheDocument();
  });

  it('opens connect form', async () => {
    const user = userEvent.setup();
    render(<AdvertisingPage />);
    await user.click(screen.getByText('Connect Account'));
    expect(screen.getByPlaceholderText('Account Name')).toBeInTheDocument();
  });

  it('connects an account', async () => {
    const user = userEvent.setup();
    render(<AdvertisingPage />);
    await user.click(screen.getByText('Connect Account'));

    await user.type(screen.getByPlaceholderText('Account Name'), 'Google Ads Prod');
    await user.type(screen.getByPlaceholderText('Platform Account ID'), '123-456');
    await user.click(screen.getByText('Connect'));

    await waitFor(() => {
      expect(mockConnectAccount).toHaveBeenCalledWith({
        organization_id: 'org-1',
        platform: 'google',
        account_name: 'Google Ads Prod',
        platform_account_id: '123-456',
      });
    });
  });
});
