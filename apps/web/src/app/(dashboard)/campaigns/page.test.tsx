import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockUseCampaigns = vi.fn();
const mockUseCampaignOverview = vi.fn();
const mockUseTemplates = vi.fn();

vi.mock('@/features/campaigns/api/useCampaigns', () => ({
  useCampaigns: () => mockUseCampaigns(),
}));

vi.mock('@/features/calendar/api/useCalendar', () => ({
  useCampaignOverview: () => mockUseCampaignOverview(),
}));

vi.mock('@/features/campaigns/api/useAdvancedCampaigns', () => ({
  useTemplates: () => mockUseTemplates(),
  useCreateTemplate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCloneFromTemplate: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteTemplate: () => ({ mutate: vi.fn() }),
}));

import CampaignsPage from './page';

describe('CampaignsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCampaignOverview.mockReturnValue({ data: null });
  });

  describe('campaigns tab', () => {
    it('shows loading state', () => {
      mockUseCampaigns.mockReturnValue({ data: null, isLoading: true, isError: false });
      render(<CampaignsPage />);
      expect(screen.getByText('Campaigns')).toBeInTheDocument();
    });

    it('shows error state', () => {
      mockUseCampaigns.mockReturnValue({ data: null, isLoading: false, isError: true });
      render(<CampaignsPage />);
      expect(screen.getByText('Failed to load campaigns')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('shows empty state', () => {
      mockUseCampaigns.mockReturnValue({ data: [], isLoading: false, isError: false });
      render(<CampaignsPage />);
      expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
    });

    it('renders campaign list', () => {
      mockUseCampaigns.mockReturnValue({
        data: [{ id: '1', name: 'Test Campaign', status: 'active', channels: ['email'], budget: 1000 }],
        isLoading: false, isError: false,
      });
      render(<CampaignsPage />);
      expect(screen.getByText('Test Campaign')).toBeInTheDocument();
    });
  });

  describe('templates tab', () => {
    beforeEach(() => {
      mockUseCampaigns.mockReturnValue({ data: [], isLoading: false, isError: false });
    });

    it('switches to templates tab', async () => {
      const user = userEvent.setup();
      mockUseTemplates.mockReturnValue({ data: [], isError: false });
      render(<CampaignsPage />);
      await user.click(screen.getByText('Templates'));
      expect(screen.getByText('No templates yet')).toBeInTheDocument();
    });

    it('shows template error state', async () => {
      const user = userEvent.setup();
      mockUseTemplates.mockReturnValue({ data: null, isError: true });
      render(<CampaignsPage />);
      await user.click(screen.getByText('Templates'));
      expect(screen.getByText('Failed to load templates')).toBeInTheDocument();
    });

    it('renders template list', async () => {
      const user = userEvent.setup();
      mockUseTemplates.mockReturnValue({
        data: [{ id: 'tpl-1', name: 'Spring Sale', description: 'A seasonal template', channels: ['email'], objective: 'conversion', budget_amount: 5000, budget_currency: 'USD' }],
        isError: false,
      });
      render(<CampaignsPage />);
      await user.click(screen.getByText('Templates'));
      expect(screen.getByText('Spring Sale')).toBeInTheDocument();
    });

    it('shows new template form', async () => {
      const user = userEvent.setup();
      mockUseTemplates.mockReturnValue({ data: [], isError: false });
      render(<CampaignsPage />);
      await user.click(screen.getByText('Templates'));
      await user.click(screen.getByText('New Template'));
      expect(screen.getByPlaceholderText('Template name')).toBeInTheDocument();
      expect(screen.getByText('Save Template')).toBeInTheDocument();
    });
  });
});
