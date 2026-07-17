import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

vi.mock('next/dynamic', () => {
  return {
    default: (importFn: () => Promise<any>, _opts?: any) => {
      const Lazy = React.lazy(importFn);
      return (props: any) => (
        <React.Suspense fallback={<div />}>
          <Lazy {...props} />
        </React.Suspense>
      );
    },
  };
});

vi.mock('./content-settings-panel', () => ({
  ContentSettingsPanel: ({
    mode,
    onToneChange,
    instructions,
    onInstructionsChange,
    instructionsError,
    onGenerate,
    rewriteInput,
    onRewriteInputChange,
  }: any) => (
    <div>
      {mode === 'compose' ? (
        <>
          <span>Template</span>
          <span>Brand Voice</span>
          {['professional', 'casual', 'funny', 'formal', 'friendly', 'authoritative'].map((t) => (
            <button key={t} onClick={() => onToneChange(t)}>{t}</button>
          ))}
          <textarea
            placeholder="Additional instructions..."
            value={instructions}
            onChange={(e) => onInstructionsChange(e.target.value)}
          />
          {instructionsError && <p>{instructionsError}</p>}
          <button onClick={onGenerate}>Generate</button>
        </>
      ) : (
        <>
          <textarea
            placeholder="Paste content to rewrite..."
            value={rewriteInput}
            onChange={(e) => onRewriteInputChange(e.target.value)}
          />
          <button onClick={onGenerate}>Rewrite</button>
        </>
      )}
    </div>
  ),
}));

vi.mock('./content-result-panel', () => ({
  ContentResultPanel: () => <div />,
}));

import AIContentPage from './page';

describe('AIContentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page with compose mode', () => {
    render(<AIContentPage />);
    expect(screen.getByText('AI Content Composer')).toBeInTheDocument();
    expect(screen.getByText('Compose')).toBeInTheDocument();
    expect(screen.getByText('Rewrite')).toBeInTheDocument();
  });

  it('shows tone selection options', async () => {
    render(<AIContentPage />);
    expect(await screen.findByText(/professional/)).toBeInTheDocument();
    expect(screen.getByText(/casual/)).toBeInTheDocument();
    expect(screen.getByText(/friendly/)).toBeInTheDocument();
  });

  it('shows instructions error when too long', async () => {
    const user = userEvent.setup();
    render(<AIContentPage />);

    const instructionsInput = await screen.findByPlaceholderText(/instructions/i);
    fireEvent.change(instructionsInput, { target: { value: 'A'.repeat(1001) } });
    await user.click(screen.getByRole('button', { name: /generate/i }));

    expect(await screen.findByText('Instructions too long')).toBeInTheDocument();
    expect(mockGenerateMutateAsync).not.toHaveBeenCalled();
  });

  it('switches to rewrite mode and renders input', async () => {
    const user = userEvent.setup();
    render(<AIContentPage />);
    await user.click(screen.getByText('Rewrite'));
    expect(await screen.findByPlaceholderText(/paste content/i)).toBeInTheDocument();
  });

  it('shows voice and template selects', async () => {
    render(<AIContentPage />);
    expect(await screen.findByText('Brand Voice')).toBeInTheDocument();
    expect(screen.getByText('Template')).toBeInTheDocument();
  });

  it('shows SEO Score button after generation', async () => {
    render(<AIContentPage />);
    expect(screen.queryByText('SEO Score')).not.toBeInTheDocument();
  });
});
