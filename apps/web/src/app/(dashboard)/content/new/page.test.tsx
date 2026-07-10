import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockBack = vi.fn();
const mockMutateAsync = vi.fn().mockResolvedValue({ id: 'content-1' });

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/content/api/useContent', () => ({
  useCreateContent: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

import NewContentPage from './page';

describe('NewContentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with all fields', () => {
    render(<NewContentPage />);
    expect(screen.getByText('New Content')).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Content Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Content' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByText('Generate with AI')).toBeInTheDocument();
  });

  it('shows validation error when title is empty', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);
    await user.click(screen.getByRole('button', { name: 'Create Content' }));
    expect(await screen.findByText('Title is required')).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('submits with valid data', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);

    await user.type(screen.getByLabelText('Title'), '10 Ways AI Transforms Marketing');
    await user.click(screen.getByRole('button', { name: 'Create Content' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        title: '10 Ways AI Transforms Marketing',
        content_type: 'blog',
        body: '',
      });
    });
    expect(mockPush).toHaveBeenCalledWith('/content');
  });

  it('submits with content type and body', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);

    await user.type(screen.getByLabelText('Title'), 'Social Post');
    await user.type(screen.getByLabelText('Content'), 'Hello world!');

    const contentTypeSelect = screen.getByLabelText('Content Type');
    await user.selectOptions(contentTypeSelect, 'social');

    await user.click(screen.getByRole('button', { name: 'Create Content' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        title: 'Social Post',
        content_type: 'social',
        body: 'Hello world!',
      });
    });
  });

  it('shows validation error when title exceeds max length', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);

    const title = screen.getByLabelText('Title');
    await user.type(title, 'A'.repeat(201));
    await user.click(screen.getByRole('button', { name: 'Create Content' }));

    expect(await screen.findByText('Title is too long')).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('navigates back on cancel', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(mockBack).toHaveBeenCalled();
  });

  it('shows Creating... when submitting', async () => {
    const user = userEvent.setup();
    render(<NewContentPage />);

    await user.type(screen.getByLabelText('Title'), 'Content Title');
    await user.click(screen.getByRole('button', { name: 'Create Content' }));

    expect(await screen.findByText('Creating...')).toBeInTheDocument();
  });
});
