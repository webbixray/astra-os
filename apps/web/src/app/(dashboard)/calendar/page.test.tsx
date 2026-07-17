import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

vi.mock('@/features/calendar/api/useCalendar', () => ({
  useCalendarEvents: () => ({ data: [], isLoading: false }),
  useCreateEvent: () => ({ mutateAsync: vi.fn() }),
}));

import CalendarPage from './page';

describe('CalendarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page', () => {
    render(<CalendarPage />);
    expect(screen.getByText('Calendar')).toBeInTheDocument();
  });

  it('renders calendar navigation', () => {
    render(<CalendarPage />);
    expect(screen.getByText(/calendar/i)).toBeInTheDocument();
  });
});
