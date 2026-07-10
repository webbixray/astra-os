import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateRule = vi.fn();

vi.mock('@/features/campaigns/api/useAutomation', () => ({
  useBudgetRules: () => ({ data: [] }),
  useCalculateAllocation: () => ({ mutate: vi.fn() }),
  useBidRules: () => ({ data: [] }),
  useAudienceSegments: () => ({ data: [] }),
  useRecommendations: () => ({ data: [] }),
  useGenerateRecommendations: () => ({ mutate: vi.fn(), isPending: false }),
  useApplyRecommendation: () => ({ mutate: vi.fn() }),
  useAutomationRules: () => ({ data: [] }),
  useCreateAutomationRule: () => ({ mutateAsync: mockCreateRule, isPending: false }),
  useToggleAutomationRule: () => ({ mutate: vi.fn() }),
  useEvaluateRules: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteAutomationRule: () => ({ mutate: vi.fn() }),
}));

import AutomationPage from './page';

describe('AutomationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<AutomationPage />);
    expect(screen.getByText('Campaign Automation')).toBeInTheDocument();
  });

  it('shows empty rules state', () => {
    render(<AutomationPage />);
    expect(screen.getByText('No automation rules yet')).toBeInTheDocument();
  });

  it('opens new rule form', async () => {
    const user = userEvent.setup();
    render(<AutomationPage />);
    await user.click(screen.getByText('New Rule'));
    expect(screen.getByPlaceholderText('Rule name')).toBeInTheDocument();
  });

  it('creates a rule', async () => {
    const user = userEvent.setup();
    render(<AutomationPage />);
    await user.click(screen.getByText('New Rule'));

    await user.type(screen.getByPlaceholderText('Rule name'), 'Pause on low budget');
    await user.click(screen.getByText('Save Rule'));

    await waitFor(() => {
      expect(mockCreateRule).toHaveBeenCalled();
    });
  });
});
