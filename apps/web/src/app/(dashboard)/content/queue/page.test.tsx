import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockUsePublishingQueue = vi.fn();
const mockRetryPublish = vi.fn();
const mockCancelPublish = vi.fn();

vi.mock('@/features/content/api/useContentPublishing', () => ({
  usePublishingQueue: () => mockUsePublishingQueue(),
  useRetryPublish: () => ({ mutate: mockRetryPublish }),
  useCancelPublish: () => ({ mutate: mockCancelPublish }),
}));

import PublishingQueuePage from './page';

describe('PublishingQueuePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state', () => {
    mockUsePublishingQueue.mockReturnValue({ data: null, isLoading: true, isError: false, error: null });
    const { container } = render(<PublishingQueuePage />);
    expect(screen.getByText('Publishing Queue')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('shows error state', () => {
    mockUsePublishingQueue.mockReturnValue({
      data: null, isLoading: false, isError: true, error: new Error('Failed to load'),
    });
    render(<PublishingQueuePage />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('shows empty state when no items', () => {
    mockUsePublishingQueue.mockReturnValue({ data: [], isLoading: false, isError: false, error: null });
    render(<PublishingQueuePage />);
    expect(screen.getByText('No publishing activity')).toBeInTheDocument();
  });

  it('renders queue items', () => {
    const items = [
      { id: '1', content_id: 'blog-post-id', platform: 'website', status: 'scheduled', scheduled_at: '2026-07-15T10:00:00Z' },
      { id: '2', content_id: 'social-update', platform: 'twitter', status: 'published', published_at: '2026-07-10T10:00:00Z' },
    ];
    mockUsePublishingQueue.mockReturnValue({ data: items, isLoading: false, isError: false, error: null });
    render(<PublishingQueuePage />);
    expect(screen.getByText('website')).toBeInTheDocument();
    expect(screen.getByText('twitter')).toBeInTheDocument();
  });

});
