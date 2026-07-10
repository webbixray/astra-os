import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/content/api/useContent', () => ({
  useContentList: () => ({
    data: [
      { id: 'c-1', title: 'Post One', content_type: 'blog', status: 'published', version: 1, body: 'Hello', generated_by_ai: false },
      { id: 'c-2', title: 'Post Two', content_type: 'social', status: 'draft', version: 1, body: 'World', generated_by_ai: true },
    ],
    isLoading: false,
  }),
}));

import ContentPage from './page';

describe('ContentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<ContentPage />);
    expect(screen.getByText('Content Studio')).toBeInTheDocument();
  });

  it('shows the new content button', () => {
    render(<ContentPage />);
    expect(screen.getByText('New Content')).toBeInTheDocument();
  });

  it('shows content items', () => {
    render(<ContentPage />);
    expect(screen.getByText('Post One')).toBeInTheDocument();
    expect(screen.getByText('Post Two')).toBeInTheDocument();
  });

  it('shows status badges', () => {
    render(<ContentPage />);
    expect(screen.getByText('published')).toBeInTheDocument();
    expect(screen.getByText('draft')).toBeInTheDocument();
  });
});
