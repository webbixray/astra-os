import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockGenerateMutateAsync = vi.fn().mockResolvedValue({
  content: 'Generated content',
  sections: {},
  template_name: 'blog-post',
  content_type: 'blog',
});
const mockRewriteMutateAsync = vi.fn().mockResolvedValue({
  content: 'Rewritten content',
  sections: {},
  template_name: '',
  content_type: '',
});

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockTemplates = [
  {
    id: 'tpl-1',
    name: 'Blog Post',
    content_type: 'blog',
    variables: ['topic', 'audience'],
  },
];

const mockVoices = [
  { id: 'voice-1', name: 'Professional', tone: 'formal' },
];

vi.mock('@/features/ai-content/api/useContentGen', () => ({
  useBrandVoices: () => ({ data: mockVoices }),
  useContentTemplates: () => ({ data: mockTemplates }),
  useGenerateContent: () => ({ mutateAsync: mockGenerateMutateAsync, isPending: false }),
  useRewriteContent: () => ({ mutateAsync: mockRewriteMutateAsync, isPending: false }),
  useSEOScore: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

import AIContentPage from './page';

describe('AIContentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page with compose mode', () => {
    render(<AIContentPage />);
    expect(screen.getByText('AI Content Generator')).toBeInTheDocument();
    expect(screen.getByText('Compose')).toBeInTheDocument();
    expect(screen.getByText('Rewrite')).toBeInTheDocument();
  });

  it('shows tone selection options', () => {
    render(<AIContentPage />);
    expect(screen.getByText('professional')).toBeInTheDocument();
    expect(screen.getByText('casual')).toBeInTheDocument();
    expect(screen.getByText('friendly')).toBeInTheDocument();
  });

  it('shows instructions error when too long', async () => {
    const user = userEvent.setup();
    render(<AIContentPage />);

    const instructionsInput = screen.getByPlaceholderText(/instructions/i);
    await user.type(instructionsInput, 'A'.repeat(1001));
    await user.click(screen.getByRole('button', { name: /generate/i }));

    expect(await screen.findByText('Instructions too long')).toBeInTheDocument();
    expect(mockGenerateMutateAsync).not.toHaveBeenCalled();
  });

  it('switches to rewrite mode and renders input', async () => {
    const user = userEvent.setup();
    render(<AIContentPage />);
    await user.click(screen.getByText('Rewrite'));
    expect(screen.getByPlaceholderText(/paste content/i)).toBeInTheDocument();
  });

  it('shows voice and template selects', () => {
    render(<AIContentPage />);
    expect(screen.getByLabelText('Brand Voice')).toBeInTheDocument();
    expect(screen.getByLabelText('Template')).toBeInTheDocument();
  });

  it('shows SEO Score button', () => {
    render(<AIContentPage />);
    expect(screen.getByText('SEO Score')).toBeInTheDocument();
  });
});
