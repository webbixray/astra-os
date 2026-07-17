import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/workflows/api/useWorkflows', () => ({
  useWorkflows: () => ({
    data: [
      { id: 'wf-1', name: 'Approval Flow', status: 'active', description: 'Approve content', nodes: [{ id: 'n-1' }], edges: [] },
      { id: 'wf-2', name: 'Draft Flow', status: 'draft', description: 'In progress', nodes: [], edges: [] },
    ],
    isLoading: false,
  }),
}));

import WorkflowsPage from './page';

describe('WorkflowsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<WorkflowsPage />);
    expect(screen.getByText('Workflows')).toBeInTheDocument();
  });

  it('shows new workflow button', () => {
    render(<WorkflowsPage />);
    expect(screen.getByText('New Workflow')).toBeInTheDocument();
  });

  it('shows workflow list', () => {
    render(<WorkflowsPage />);
    expect(screen.getByText('Approval Flow')).toBeInTheDocument();
    expect(screen.getByText('Draft Flow')).toBeInTheDocument();
  });

  it('shows node/edge counts', () => {
    render(<WorkflowsPage />);
    expect(screen.getByText('1 nodes, 0 connections')).toBeInTheDocument();
    expect(screen.getByText('0 nodes, 0 connections')).toBeInTheDocument();
  });

  it('shows status filter buttons', () => {
    render(<WorkflowsPage />);
    ['all', 'draft', 'active', 'paused', 'completed', 'archived'].forEach(s => {
      expect(screen.getByRole('button', { name: s.replace('_', ' ') })).toBeInTheDocument();
    });
  });

  it('filters by status on click', async () => {
    const user = userEvent.setup();
    render(<WorkflowsPage />);
    const draftBtn = screen.getByRole('button', { name: 'draft' });
    await user.click(draftBtn);
    expect(draftBtn).toHaveClass('bg-primary');
  });
});
