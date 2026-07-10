import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  resource_type: string;
  resource_id: string;
  channel: string;
  is_read: boolean;
  read_at: string | null;
  archived: boolean;
  created_at: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  type: string;
  channel: string;
  title_template: string;
  body_template: string;
  variables: string[];
  created_at: string;
}

export interface Preference {
  id: string;
  notification_type: string;
  channel: string;
  enabled: boolean;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  severity: string;
  target_role: string;
  dismissed_by: string[];
  expired: boolean;
  created_at: string;
}

// ── Notifications ───────────────────────────────────────────────────────────

export function useNotifications(
  orgId: string,
  unreadOnly = false,
  limit = 50,
  channel?: string,
  archived = false,
) {
  return useQuery<Notification[]>({
    queryKey: ['notifications', orgId, unreadOnly, channel, archived],
    queryFn: () =>
      api.get<Notification[]>(
        `/notifications?organization_id=${orgId}&unread_only=${unreadOnly}&limit=${limit}&archived=${archived}${channel ? `&channel=${channel}` : ''}`,
      ),
    refetchInterval: 300_000,
    staleTime: 60_000,
  });
}

export function useUnreadCount(orgId: string, channel?: string) {
  return useQuery<{ unread_count: number }>({
    queryKey: ['notifications', 'unread-count', orgId, channel],
    queryFn: () =>
      api.get<{ unread_count: number }>(
        `/notifications/unread-count?organization_id=${orgId}${channel ? `&channel=${channel}` : ''}`,
      ),
    refetchInterval: 300_000,
    staleTime: 30_000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) =>
      api.patch(`/notifications/${notificationId}/read`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (orgId: string) =>
      api.post('/notifications/read-all', { organization_id: orgId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useArchiveNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) =>
      api.patch(`/notifications/${notificationId}/archive`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useSearchNotifications(orgId: string, q: string) {
  return useQuery<Notification[]>({
    queryKey: ['notifications', 'search', orgId, q],
    queryFn: () =>
      api.get<Notification[]>(`/notifications/search?organization_id=${orgId}&q=${encodeURIComponent(q)}`),
    enabled: q.length > 0,
  });
}

// ── Templates ───────────────────────────────────────────────────────────────

export function useNotificationTemplates(orgId: string) {
  return useQuery<NotificationTemplate[]>({
    queryKey: ['notification-templates', orgId],
    queryFn: () =>
      api.get<NotificationTemplate[]>(`/notification-templates?organization_id=${orgId}`),
  });
}

export function useCreateNotificationTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { organization_id: string; name: string; type: string; channel: string; title_template: string; body_template?: string; variables?: string[] }) =>
      api.post(`/notification-templates?organization_id=${body.organization_id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notification-templates'] }),
  });
}

export function useDeleteNotificationTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (templateId: string) => api.delete(`/notification-templates/${templateId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notification-templates'] }),
  });
}

// ── Preferences ─────────────────────────────────────────────────────────────

export function useNotificationPreferences() {
  return useQuery<Preference[]>({
    queryKey: ['notification-preferences'],
    queryFn: () => api.get<Preference[]>('/notification-preferences'),
  });
}

export function useSetNotificationPreference() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { notification_type: string; channel: string; enabled: boolean }) =>
      api.put('/notification-preferences', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notification-preferences'] }),
  });
}

// ── Announcements ────────────────────────────────────────────────────────────

export function useAnnouncements(orgId: string) {
  return useQuery<Announcement[]>({
    queryKey: ['announcements', orgId],
    queryFn: () => api.get<Announcement[]>(`/announcements?organization_id=${orgId}`),
  });
}

export function useCreateAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { organization_id: string; title: string; body?: string; severity?: string; target_role?: string }) =>
      api.post(`/announcements?organization_id=${body.organization_id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['announcements'] }),
  });
}

export function useDismissAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (announcementId: string) => api.post(`/announcements/${announcementId}/dismiss`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['announcements'] }),
  });
}

export function useDeleteAnnouncement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (announcementId: string) => api.delete(`/announcements/${announcementId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['announcements'] }),
  });
}
