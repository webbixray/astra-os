import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockPush = vi.fn();
const mockSignup = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock('@/lib/auth', () => ({
  useAuth: () => ({ signup: mockSignup }),
}));

import SignupPage from './page';

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the signup form', () => {
    render(<SignupPage />);
    expect(screen.getByText('Create an account')).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
  });

  it('submits name, email, and password', async () => {
    const user = userEvent.setup();
    mockSignup.mockResolvedValue(undefined);
    render(<SignupPage />);

    await user.type(screen.getByLabelText('Name'), 'Alice');
    await user.type(screen.getByLabelText('Email'), 'alice@example.com');
    await user.type(screen.getByLabelText('Password'), 'Secure123!');
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    await waitFor(() => {
      expect(mockSignup).toHaveBeenCalledWith('alice@example.com', 'Secure123!', 'Alice');
    });
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('shows error on signup failure', async () => {
    const user = userEvent.setup();
    mockSignup.mockRejectedValue(new Error('Signup failed'));
    render(<SignupPage />);

    await user.type(screen.getByLabelText('Name'), 'Bob');
    await user.type(screen.getByLabelText('Email'), 'bob@example.com');
    await user.type(screen.getByLabelText('Password'), 'Secure123!');
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(await screen.findByText('Signup failed. Please try again.')).toBeInTheDocument();
  });

  it('shows Creating account... while loading', async () => {
    const user = userEvent.setup();
    mockSignup.mockImplementation(() => new Promise(() => {}));
    render(<SignupPage />);

    await user.type(screen.getByLabelText('Name'), 'Carol');
    await user.type(screen.getByLabelText('Email'), 'c@d.com');
    await user.type(screen.getByLabelText('Password'), 'Secure123!');
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(await screen.findByText('Creating account...')).toBeInTheDocument();
  });
});
