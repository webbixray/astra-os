import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorBoundary, withErrorBoundary } from './error-boundary';

const ThrowComponent = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>Rendered content</div>;
};

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders default fallback on error', () => {
    render(
      <ErrorBoundary>
        <ThrowComponent shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom error UI</div>}>
        <ThrowComponent shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('recovers after clicking Try again', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowComponent shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    rerender(
      <ErrorBoundary>
        <ThrowComponent shouldThrow={false} />
      </ErrorBoundary>,
    );
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(screen.getByText('Rendered content')).toBeInTheDocument();
  });
});

describe('withErrorBoundary', () => {
  it('wraps component and passes props', () => {
    const Wrapped = withErrorBoundary(({ name }: { name: string }) => <div>Hello {name}</div>);
    render(<Wrapped name="World" />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('shows error fallback when wrapped component throws', () => {
    const Wrapped = withErrorBoundary(ThrowComponent);
    render(<Wrapped shouldThrow />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('displays custom displayName', () => {
    const MyComponent = () => <div />;
    MyComponent.displayName = 'MyComponent';
    const Wrapped = withErrorBoundary(MyComponent);
    expect(Wrapped.displayName).toBe('withErrorBoundary(MyComponent)');
  });
});
