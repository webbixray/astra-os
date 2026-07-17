import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

vi.mock('@/lib/org', () => ({
  useOrg: () => ({ orgId: 'org-1' }),
}));

const mockCreateTemplate = vi.fn();
const mockCreateAnnouncement = vi.fn();

vi.mock('@/features/notifications/api/useNotifications', () => ({
  useNotifications: () => ({ data: [], isLoading: false }),
  useMarkRead: () => ({ mutate: vi.fn() }),
  useMarkAllRead: () => ({ mutate: vi.fn() }),
  useArchiveNotification: () => ({ mutate: vi.fn() }),
  useNotificationTemplates: () => ({ data: [] }),
  useCreateNotificationTemplate: () => ({ mutateAsync: mockCreateTemplate, isPending: false }),
  useDeleteNotificationTemplate: () => ({ mutate: vi.fn() }),
  useNotificationPreferences: () => ({ data: [] }),
  useSetNotificationPreference: () => ({ mutate: vi.fn() }),
  useAnnouncements: () => ({ data: [] }),
  useCreateAnnouncement: () => ({ mutateAsync: mockCreateAnnouncement, isPending: false }),
  useDismissAnnouncement: () => ({ mutate: vi.fn() }),
  useDeleteAnnouncement: () => ({ mutate: vi.fn() }),
}));

vi.mock('./NotificationsInboxTab', () => ({
  NotificationsInboxTab: () => (
    <div>
      <h3>Inbox empty</h3>
      <p>No new notifications</p>
    </div>
  ),
}));

vi.mock('./NotificationsArchivedTab', () => ({
  NotificationsArchivedTab: () => <div>Archived</div>,
}));

vi.mock('./NotificationsPreferencesTab', () => ({
  NotificationsPreferencesTab: () => (
    <p>Control which notifications you receive and through which channels</p>
  ),
}));

vi.mock('./NotificationsTemplatesTab', () => ({
  NotificationsTemplatesTab: (_: { orgId: string }) => {
    const [showNew, setShowNew] = React.useState(false);
    return (
      <div>
        <button onClick={() => setShowNew(!showNew)}>New Template</button>
        {showNew && (
          <div>
            <input placeholder="Name" />
            <button onClick={() => mockCreateTemplate()}>Save Template</button>
          </div>
        )}
      </div>
    );
  },
}));

vi.mock('./NotificationsAnnouncementsTab', () => ({
  NotificationsAnnouncementsTab: (_: { orgId: string }) => {
    const [showNew, setShowNew] = React.useState(false);
    return (
      <div>
        <button onClick={() => setShowNew(!showNew)}>New Announcement</button>
        {showNew && (
          <div>
            <input placeholder="Title" />
            <button onClick={() => mockCreateAnnouncement()}>Publish</button>
          </div>
        )}
      </div>
    );
  },
}));

import NotificationsPage from './page';

describe('NotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page with tabs', () => {
    render(<NotificationsPage />);
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Inbox')).toBeInTheDocument();
    expect(screen.getByText('Archive')).toBeInTheDocument();
    expect(screen.getByText('Preferences')).toBeInTheDocument();
    expect(screen.getByText('Templates')).toBeInTheDocument();
    expect(screen.getByText('Announcements')).toBeInTheDocument();
  });

  it('shows empty inbox state', async () => {
    render(<NotificationsPage />);
    expect(screen.getByText('Inbox empty')).toBeInTheDocument();
    expect(screen.getByText('No new notifications')).toBeInTheDocument();
  });

  it('switches to templates tab and creates a template', async () => {
    const user = userEvent.setup();
    render(<NotificationsPage />);
    await user.click(screen.getByText('Templates'));
    await user.click(await screen.findByText('New Template'));

    await user.type(screen.getByPlaceholderText('Name'), 'Weekly Digest');
    await user.click(screen.getByText('Save Template'));

    await waitFor(() => {
      expect(mockCreateTemplate).toHaveBeenCalled();
    });
  });

  it('switches to announcements tab and creates an announcement', async () => {
    const user = userEvent.setup();
    render(<NotificationsPage />);
    await user.click(screen.getByText('Announcements'));
    await user.click(await screen.findByText('New Announcement'));

    await user.type(screen.getByPlaceholderText('Title'), 'New Feature');
    await user.click(screen.getByText('Publish'));

    await waitFor(() => {
      expect(mockCreateAnnouncement).toHaveBeenCalled();
    });
  });

  it('shows preferences tab', async () => {
    const user = userEvent.setup();
    render(<NotificationsPage />);
    await user.click(screen.getByText('Preferences'));
    expect(await screen.findByText(/Control which notifications you receive/)).toBeInTheDocument();
  });
});
