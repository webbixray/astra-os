import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockMutate = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/organizations/api/useOrganizations', () => ({
  useMembers: () => ({
    data: [{ id: 'user-1', name: 'Alice', email: 'alice@test.com', role: 'admin' }],
    isLoading: false,
  }),
  useInvitations: () => ({ data: [] }),
  useInviteMember: () => ({ mutate: mockMutate, isPending: false }),
  useCancelInvitation: () => ({ mutate: vi.fn() }),
  useChangeMemberRole: () => ({ mutate: vi.fn() }),
  useRemoveMember: () => ({ mutate: vi.fn() }),
}));

import TeamPage from './page';

describe('TeamPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<TeamPage />);
    expect(screen.getByText('Team')).toBeInTheDocument();
  });

  it('shows team members', () => {
    render(<TeamPage />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@test.com')).toBeInTheDocument();
  });

  it('sends an invite', async () => {
    const user = userEvent.setup();
    render(<TeamPage />);

    await user.click(screen.getByText('Invite Member'));
    await user.type(screen.getByPlaceholderText('Email address'), 'new@test.com');
    await user.click(screen.getByText('Send Invite'));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        { orgId: 'org-1', email: 'new@test.com', role: 'member' },
        expect.any(Object),
      );
    });
  });
});
