import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'content-1' }),
  useRouter: () => ({ push: mockPush }),
}));

const mockUpdateContent = vi.fn();
const mockPublish = vi.fn();
const mockSchedule = vi.fn();
const mockRetry = vi.fn();
const mockCancel = vi.fn();

vi.mock('@/features/content/api/useContent', () => ({
  useContent: () => ({
    data: { id: 'content-1', title: 'Test Post', body: 'Hello world', content_type: 'blog', status: 'draft', version: 1, generated_by_ai: false },
    isLoading: false, isError: false, error: null,
  }),
  useUpdateContent: () => ({ mutateAsync: mockUpdateContent }),
}));

vi.mock('@/features/content/api/useContentPublishing', () => ({
  usePublishingHistory: () => ({ data: [] }),
  usePublishContent: () => ({ mutate: mockPublish, isPending: false }),
  useScheduleContent: () => ({ mutate: mockSchedule }),
  useRetryPublish: () => ({ mutate: mockRetry }),
  useCancelPublish: () => ({ mutate: mockCancel }),
}));

import ContentDetailPage from './page';

describe('ContentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders content details', () => {
    render(<ContentDetailPage />);
    expect(screen.getByText('Test Post')).toBeInTheDocument();
    expect(screen.getByText('blog')).toBeInTheDocument();
  });

  it('shows publish section with platform buttons', () => {
    render(<ContentDetailPage />);
    expect(screen.getByText('Publish')).toBeInTheDocument();
  });

  it('shows status transition buttons', () => {
    render(<ContentDetailPage />);
    expect(screen.getByText('review')).toBeInTheDocument();
    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  it('shows empty publishing history', () => {
    render(<ContentDetailPage />);
    expect(screen.getByText('No publishing activity yet')).toBeInTheDocument();
  });
});
