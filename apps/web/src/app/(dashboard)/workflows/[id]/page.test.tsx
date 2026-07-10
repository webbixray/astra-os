import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'wf-1' }),
  useRouter: () => ({ push: mockPush }),
}));

const mockUpdateWorkflow = vi.fn();
const mockExecuteWorkflow = vi.fn();

vi.mock('@/features/workflows/api/useWorkflows', () => ({
  useWorkflow: () => ({
    data: {
      id: 'wf-1', name: 'Approval Flow', description: 'Content approval process',
      status: 'draft', organization_id: 'org-1',
      nodes: [{ id: 'n-1', type: 'approval', label: 'Approval', config: {}, position_x: 0, position_y: 0 }],
      edges: [],
    },
    isLoading: false,
  }),
  useUpdateWorkflow: () => ({ mutateAsync: mockUpdateWorkflow, isPending: false }),
  useExecuteWorkflow: () => ({ mutateAsync: mockExecuteWorkflow, isPending: false, data: null }),
}));

vi.mock('@/features/workflows/components/workflow-canvas', () => ({
  WorkflowCanvas: () => <div data-testid="workflow-canvas">Canvas</div>,
}));

import WorkflowDetailPage from './page';

describe('WorkflowDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workflow details', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Approval Flow')).toBeInTheDocument();
    expect(screen.getByText('Content approval process')).toBeInTheDocument();
  });

  it('shows the workflow canvas', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByTestId('workflow-canvas')).toBeInTheDocument();
  });

  it('shows status transition buttons for draft', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  it('shows run button for draft', () => {
    render(<WorkflowDetailPage />);
    expect(screen.getByText('Run')).toBeInTheDocument();
  });
});
