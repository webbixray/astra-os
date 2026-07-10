import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockBack = vi.fn();
const mockMutateAsync = vi.fn().mockResolvedValue({ id: 'wf-1' });

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/workflows/api/useWorkflows', () => ({
  useCreateWorkflow: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

import NewWorkflowPage from './page';

describe('NewWorkflowPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with all fields', () => {
    render(<NewWorkflowPage />);
    expect(screen.getByText('New Workflow')).toBeInTheDocument();
    expect(screen.getByLabelText('Workflow Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Workflow' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('shows validation error when name is empty on submit', async () => {
    const user = userEvent.setup();
    render(<NewWorkflowPage />);
    await user.click(screen.getByRole('button', { name: 'Create Workflow' }));
    expect(await screen.findByText('Name is required')).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('submits the form with valid data', async () => {
    const user = userEvent.setup();
    render(<NewWorkflowPage />);

    await user.type(screen.getByLabelText('Workflow Name'), 'Test Workflow');
    await user.click(screen.getByRole('button', { name: 'Create Workflow' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Test Workflow',
        description: undefined,
      });
    });
    expect(mockPush).toHaveBeenCalledWith('/workflows/wf-1');
  });

  it('submits with description', async () => {
    const user = userEvent.setup();
    render(<NewWorkflowPage />);

    await user.type(screen.getByLabelText('Workflow Name'), 'Campaign Approval');
    await user.type(screen.getByLabelText('Description'), 'Auto-approve campaigns under $500');
    await user.click(screen.getByRole('button', { name: 'Create Workflow' }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        organization_id: 'org-1',
        name: 'Campaign Approval',
        description: 'Auto-approve campaigns under $500',
      });
    });
  });

  it('navigates back on cancel', async () => {
    const user = userEvent.setup();
    render(<NewWorkflowPage />);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(mockBack).toHaveBeenCalled();
  });

  it('shows Creating... when submitting', async () => {
    const user = userEvent.setup();
    render(<NewWorkflowPage />);

    await user.type(screen.getByLabelText('Workflow Name'), 'Workflow');
    await user.click(screen.getByRole('button', { name: 'Create Workflow' }));

    expect(await screen.findByText('Creating...')).toBeInTheDocument();
  });
});
