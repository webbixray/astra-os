import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'camp-1' }),
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockUseCampaign = vi.fn();
const mockUseUpdateCampaign = vi.fn();
const mockUseCampaignBudget = vi.fn();
const mockUseSetCampaignBudget = vi.fn();
const mockUseRecordSpend = vi.fn();
const mockUseABTests = vi.fn();
const mockUseCreateABTest = vi.fn();
const mockUseAddVariant = vi.fn();
const mockUseStartABTest = vi.fn();
const mockUseDetermineWinner = vi.fn();

vi.mock('@/features/campaigns/api/useCampaigns', () => ({
  useCampaign: () => mockUseCampaign(),
  useUpdateCampaign: () => mockUseUpdateCampaign(),
}));

vi.mock('@/features/campaigns/api/useAdvancedCampaigns', () => ({
  useCampaignBudget: () => mockUseCampaignBudget(),
  useSetCampaignBudget: () => mockUseSetCampaignBudget(),
  useRecordSpend: () => mockUseRecordSpend(),
  useABTests: () => mockUseABTests(),
  useCreateABTest: () => mockUseCreateABTest(),
  useAddVariant: () => mockUseAddVariant(),
  useStartABTest: () => mockUseStartABTest(),
  useDetermineWinner: () => mockUseDetermineWinner(),
}));

import CampaignDetailPage from './page';

describe('CampaignDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUpdateCampaign.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseCampaignBudget.mockReturnValue({ data: null });
    mockUseSetCampaignBudget.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseRecordSpend.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseABTests.mockReturnValue({ data: [] });
    mockUseCreateABTest.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseAddVariant.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseStartABTest.mockReturnValue({ mutateAsync: vi.fn() });
    mockUseDetermineWinner.mockReturnValue({ mutateAsync: vi.fn() });
  });

  it('shows skeleton when loading', () => {
    mockUseCampaign.mockReturnValue({ data: null, isLoading: true, isError: false, error: null });
    const { container } = render(<CampaignDetailPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('shows error state on failure', () => {
    mockUseCampaign.mockReturnValue({
      data: null, isLoading: false, isError: true, error: new Error('Failed to load'),
    });
    render(<CampaignDetailPage />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
    expect(screen.getByText('Back to campaigns')).toBeInTheDocument();
  });

  it('shows not found when campaign is null', () => {
    mockUseCampaign.mockReturnValue({ data: null, isLoading: false, isError: false, error: null });
    render(<CampaignDetailPage />);
    expect(screen.getByText('Campaign not found')).toBeInTheDocument();
  });

  it('renders campaign details when data is loaded', () => {
    mockUseCampaign.mockReturnValue({
      data: { id: 'camp-1', name: 'Summer Sale', status: 'active', objective: 'conversion', budget_amount: 5000, budget_currency: 'USD', spent: 1200, channels: ['email'] },
      isLoading: false, isError: false, error: null,
    });
    render(<CampaignDetailPage />);
    expect(screen.getByText('Summer Sale')).toBeInTheDocument();
  });
});
