import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateProvider = vi.fn();

vi.mock('@/features/email/api/useEmail', () => ({
  useEmailProviders: () => ({ data: [], isLoading: false }),
  useCreateEmailProvider: () => ({ mutateAsync: mockCreateProvider, isPending: false }),
  useDeleteEmailProvider: () => ({ mutate: vi.fn() }),
}));

vi.mock('@/features/email/types', () => ({
  PROVIDER_TYPES: ['sendgrid', 'ses', 'smtp'],
}));

import EmailSettingsPage from './page';

describe('EmailSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<EmailSettingsPage />);
    expect(screen.getByText('Email Provider Settings')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<EmailSettingsPage />);
    expect(screen.getByText('No providers configured')).toBeInTheDocument();
  });

  it('opens add provider form', async () => {
    const user = userEvent.setup();
    render(<EmailSettingsPage />);
    await user.click(screen.getByText('Add Provider'));
    expect(screen.getByPlaceholderText('Provider name')).toBeInTheDocument();
  });

  it('creates a provider', async () => {
    const user = userEvent.setup();
    render(<EmailSettingsPage />);
    await user.click(screen.getByText('Add Provider'));

    await user.type(screen.getByPlaceholderText('Provider name'), 'My SendGrid');
    await user.type(screen.getByLabelText('API Key'), 'sg-key-123');
    await user.type(screen.getByLabelText('From email'), 'hello@test.com');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(mockCreateProvider).toHaveBeenCalledWith({
        organization_id: 'org-1',
        provider_type: 'sendgrid',
        name: 'My SendGrid',
        api_key: 'sg-key-123',
        from_email: 'hello@test.com',
        from_name: '',
      });
    });
  });
});
