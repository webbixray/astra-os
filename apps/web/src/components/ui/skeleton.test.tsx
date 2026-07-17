import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Skeleton, SkeletonCard, SkeletonRow, SkeletonLine, SkeletonTitle } from './skeleton';

describe('Skeleton', () => {
  it('renders with default classes', () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('animate-pulse');
    expect(el.className).toContain('rounded');
    expect(el.className).toContain('bg-muted');
  });

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="h-10 w-20" />);
    expect(container.firstChild).toHaveClass('h-10');
    expect(container.firstChild).toHaveClass('w-20');
  });
});

describe('SkeletonCard', () => {
  it('renders card skeleton with 4 lines', () => {
    const { container } = render(<SkeletonCard />);
    const firstChild = container.firstChild as HTMLElement;
    expect(firstChild.className).toContain('rounded-lg');
    expect(firstChild.className).toContain('border');
    expect(firstChild.querySelectorAll('.animate-pulse').length).toBe(4);
  });
});

describe('SkeletonRow', () => {
  it('renders row skeleton with avatar, lines, and action', () => {
    const { container } = render(<SkeletonRow />);
    const firstChild = container.firstChild as HTMLElement;
    expect(firstChild.className).toContain('flex');
    expect(firstChild.querySelectorAll('.animate-pulse').length).toBe(4);
  });
});

describe('SkeletonLine', () => {
  it('renders a line skeleton', () => {
    const { container } = render(<SkeletonLine />);
    expect(container.firstChild).toHaveClass('h-4');
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonLine className="w-1/2" />);
    expect(container.firstChild).toHaveClass('w-1/2');
  });
});

describe('SkeletonTitle', () => {
  it('renders a title skeleton', () => {
    const { container } = render(<SkeletonTitle />);
    expect(container.firstChild).toHaveClass('h-8');
    expect(container.firstChild).toHaveClass('w-48');
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonTitle className="w-64" />);
    expect(container.firstChild).toHaveClass('w-64');
  });
});
