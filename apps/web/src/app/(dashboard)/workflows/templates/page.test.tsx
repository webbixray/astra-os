import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/workflows/api/useTemplates', () => ({
  useWorkflowTemplates: () => ({
    data: [
      {
        template_id: 'campaign_launch',
        name: 'Campaign Launch',
        description: 'Standard campaign launch workflow',
        category: 'campaign',
        node_count: 8,
        edge_count: 8,
        estimated_duration_minutes: 120,
        tags: ['campaign', 'launch'],
      },
      {
        template_id: 'creative_review',
        name: 'Creative Review',
        description: 'Creative asset review workflow',
        category: 'content',
        node_count: 7,
        edge_count: 7,
        estimated_duration_minutes: 60,
        tags: ['creative', 'review'],
      },
    ],
    isLoading: false,
  }),
  useInstantiateTemplate: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import WorkflowTemplatesPage from './page';

describe('WorkflowTemplatesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page title', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('Workflow Templates')).toBeInTheDocument();
  });

  it('shows template cards', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('Campaign Launch')).toBeInTheDocument();
    expect(screen.getByText('Creative Review')).toBeInTheDocument();
  });

  it('shows template descriptions', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('Standard campaign launch workflow')).toBeInTheDocument();
    expect(screen.getByText('Creative asset review workflow')).toBeInTheDocument();
  });

  it('shows category filter buttons', () => {
    render(<WorkflowTemplatesPage />);
    ['all', 'campaign', 'content', 'optimization', 'compliance'].forEach((c) => {
      expect(screen.getByRole('button', { name: c })).toBeInTheDocument();
    });
  });

  it('shows node counts', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('8 nodes')).toBeInTheDocument();
    expect(screen.getByText('7 nodes')).toBeInTheDocument();
  });

  it('shows estimated durations', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('~120 min')).toBeInTheDocument();
    expect(screen.getByText('~60 min')).toBeInTheDocument();
  });

  it('shows Use Template buttons', () => {
    render(<WorkflowTemplatesPage />);
    const buttons = screen.getAllByText('Use Template');
    expect(buttons.length).toBe(2);
  });

  it('shows back link', () => {
    render(<WorkflowTemplatesPage />);
    expect(screen.getByText('Back to Workflows')).toBeInTheDocument();
  });
});
