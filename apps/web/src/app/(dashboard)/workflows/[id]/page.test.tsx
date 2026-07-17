import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'wf-1' }),
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/workflows/api/useWorkflows', () => ({
  useWorkflow: () => ({
    data: {
      id: 'wf-1',
      name: 'Campaign Approval',
      description: 'Approve campaign content',
      status: 'draft',
      organization_id: 'org-1',
      created_by: 'user-1',
      created_at: '2026-07-12T10:00:00Z',
      updated_at: '2026-07-12T10:00:00Z',
      nodes: [
        { id: 'trigger-1', type: 'trigger', label: 'Start', config: {}, position_x: 250, position_y: 0 },
        { id: 'end-1', type: 'end', label: 'End', config: {}, position_x: 250, position_y: 300 },
      ],
      edges: [
        { id: 'e1', source_id: 'trigger-1', target_id: 'end-1', label: '' },
      ],
    },
    isLoading: false,
  }),
  useUpdateWorkflow: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  useExecuteWorkflow: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock('@/features/workflows/api/useExecutions', () => ({
  useWorkflowExecutions: () => ({
    data: [
      {
        id: 'exec-1',
        workflow_id: 'wf-1',
        status: 'completed',
        steps: [
          { id: 'step-1', node_id: 'trigger-1', status: 'completed', result: { step: 'Start' }, error: null, started_at: '2026-07-12T10:00:00Z', completed_at: '2026-07-12T10:00:01Z' },
        ],
        error: null,
        created_at: '2026-07-12T10:00:00Z',
        updated_at: '2026-07-12T10:00:01Z',
      },
    ],
    isLoading: false,
  }),
}));

import WorkflowDetailPage from './page';

describe('WorkflowDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow name', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Campaign Approval')).toBeInTheDocument();
  });

  it('shows workflow description', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Approve campaign content')).toBeInTheDocument();
  });

  it('shows status badge', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('draft')).toBeInTheDocument();
  });

  it('shows Builder and Executions tabs', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Builder')).toBeInTheDocument();
    expect(screen.getByText(/Executions/)).toBeInTheDocument();
  });

  it('shows node count in canvas by default', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('End')).toBeInTheDocument();
  });

  it('shows transition buttons for draft', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  it('switches to executions tab', async () => {
    const user = userEvent.setup();
    render(<WorkflowDetailPage />);
    await user.click(screen.getByText(/Executions/));
    expect(screen.getByText('exec-1')).toBeInTheDocument();
    expect(screen.getAllByText('completed').length).toBeGreaterThan(0);
  });
});
