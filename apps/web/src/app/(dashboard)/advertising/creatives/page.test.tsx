import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateCreative = vi.fn();

vi.mock('@/features/advertising/api/useAdvertising', () => ({
  useAdCreatives: () => ({ data: [], isLoading: false }),
  useCreateAdCreative: () => ({ mutateAsync: mockCreateCreative, isPending: false }),
}));

import CreativesPage from './page';

describe('CreativesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<CreativesPage />);
    expect(screen.getByText('Creative Library')).toBeInTheDocument();
  });

  it('opens create form', async () => {
    const user = userEvent.setup();
    render(<CreativesPage />);
    await user.click(screen.getByText('New Creative'));
    expect(screen.getByPlaceholderText('Creative Name')).toBeInTheDocument();
  });

  it('creates a creative', async () => {
    const user = userEvent.setup();
    render(<CreativesPage />);
    await user.click(screen.getByText('New Creative'));

    await user.type(screen.getByPlaceholderText('Creative Name'), 'Banner Ad');
    await user.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockCreateCreative).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Banner Ad',
        type: 'image',
      });
    });
  });
});
