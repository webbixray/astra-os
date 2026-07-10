import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockBack = vi.fn();
const mockMutateAsync = vi.fn().mockResolvedValue({ id: 'camp-1' });

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/campaigns/api/useCampaigns', () => ({
  useCreateCampaign: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

import NewCampaignPage from './page';

describe('NewCampaignPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with all fields', () => {
    render(<NewCampaignPage />);
    expect(screen.getByText('New Campaign')).toBeInTheDocument();
    expect(screen.getByLabelText('Campaign Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Budget')).toBeInTheDocument();
    expect(screen.getByLabelText('Currency')).toBeInTheDocument();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    expect(screen.getByText('Channels')).toBeInTheDocument();
    expect(screen.getByLabelText('Objective')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Campaign' })).toBeInTheDocument();
  });

  it('shows validation error when name is empty', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);
    await user.click(screen.getByRole('button', { name: 'Create Campaign' }));
    expect(await screen.findByText('Campaign name is required')).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('shows validation error when no channels selected', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);

    await user.type(screen.getByLabelText('Campaign Name'), 'Summer Sale');
    await user.click(screen.getByRole('button', { name: 'Create Campaign' }));

    expect(await screen.findByText('Select at least one channel')).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('submits with valid data', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);

    await user.type(screen.getByLabelText('Campaign Name'), 'Summer Sale');
    await user.click(screen.getByText('email'));
    await user.click(screen.getByText('social'));
    await user.click(screen.getByRole('button', { name: 'Create Campaign' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Summer Sale',
        description: undefined,
        budget_amount: undefined,
        budget_currency: 'USD',
        start_date: undefined,
        end_date: undefined,
        channels: ['email', 'social'],
        objective: undefined,
      });
    });
    expect(mockPush).toHaveBeenCalledWith('/campaigns');
  });

  it('submits with all optional fields filled', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);

    await user.type(screen.getByLabelText('Campaign Name'), 'Full Campaign');
    await user.type(screen.getByLabelText('Description'), 'A comprehensive campaign');
    await user.clear(screen.getByLabelText('Budget'));
    await user.type(screen.getByLabelText('Budget'), '5000');
    await user.click(screen.getByText('ads'));
    await user.click(screen.getByText('seo'));

    await user.click(screen.getByRole('button', { name: 'Create Campaign' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Full Campaign',
        description: 'A comprehensive campaign',
        budget_amount: 5000,
        budget_currency: 'USD',
        start_date: undefined,
        end_date: undefined,
        channels: ['ads', 'seo'],
        objective: undefined,
      });
    });
  });

  it('toggles channels on click', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);

    const emailBtn = screen.getByText('email');
    await user.click(emailBtn);
    expect(emailBtn.className).toContain('bg-primary');

    await user.click(emailBtn);
    expect(emailBtn.className).toContain('bg-secondary');
  });

  it('navigates back on cancel', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(mockBack).toHaveBeenCalled();
  });

  it('shows Creating... when submitting', async () => {
    const user = userEvent.setup();
    render(<NewCampaignPage />);

    await user.type(screen.getByLabelText('Campaign Name'), 'Campaign');
    await user.click(screen.getByText('email'));
    await user.click(screen.getByRole('button', { name: 'Create Campaign' }));

    expect(await screen.findByText('Creating...')).toBeInTheDocument();
  });
});
