import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'ec-1' }),
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/features/email/api/useEmail', () => ({
  useEmailCampaign: () => ({
    data: {
      id: 'ec-1', name: 'Welcome Email', subject: 'Welcome!',
      sent_count: 1000, open_count: 450, click_count: 120, bounce_count: 15,
      events: [
        { id: 'e-1', event_type: 'sent', recipient_email: 'a@test.com', occurred_at: '2024-01-15T10:00:00Z' },
        { id: 'e-2', event_type: 'opened', recipient_email: 'b@test.com', occurred_at: '2024-01-15T11:00:00Z' },
      ],
    },
    isLoading: false,
  }),
}));

import EmailCampaignDetailPage from './page';

describe('EmailCampaignDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders campaign details', () => {
    render(<EmailCampaignDetailPage />);
    expect(screen.getByText('Welcome Email')).toBeInTheDocument();
    expect(screen.getByText('Welcome!')).toBeInTheDocument();
  });

  it('shows stat cards', () => {
    render(<EmailCampaignDetailPage />);
    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('45.0%')).toBeInTheDocument();
    expect(screen.getByText('12.0%')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('shows recent events', () => {
    render(<EmailCampaignDetailPage />);
    expect(screen.getByText('sent')).toBeInTheDocument();
    expect(screen.getByText('opened')).toBeInTheDocument();
    expect(screen.getByText('a@test.com')).toBeInTheDocument();
    expect(screen.getByText('b@test.com')).toBeInTheDocument();
  });

  it('has back button', () => {
    render(<EmailCampaignDetailPage />);
    expect(screen.getByText('Back to campaigns')).toBeInTheDocument();
  });
});
