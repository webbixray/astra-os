import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface DashboardSummary {
  id: string;
  name: string;
  description: string;
  layout_columns: number;
  is_default: boolean;
  widget_count: number;
  created_at: string;
}

export interface DashboardWidget {
  id: string;
  widget_type: string;
  title: string;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  config: Record<string, unknown>;
}

export interface DashboardDetail {
  id: string;
  name: string;
  description: string;
  layout_columns: number;
  is_default: boolean;
  created_at: string;
  widgets: DashboardWidget[];
}

export interface WidgetData {
  widget_id: string;
  widget_type: string;
  title: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, unknown>;
  data: { value: unknown; metric: string };
}

export interface Anomaly {
  date: string;
  value: number;
  z_score: number;
  severity: string;
  direction: string;
}

export interface Prediction {
  date: string;
  predicted_value: number;
}

export function useDashboards(orgId: string) {
  return useQuery<DashboardSummary[]>({
    queryKey: ['dashboards', orgId],
    queryFn: () => api.get<DashboardSummary[]>(`/dashboards?organization_id=${orgId}`),
  });
}

export function useDashboardDetail(dashboardId: string | undefined) {
  return useQuery<DashboardDetail>({
    queryKey: ['dashboard', dashboardId],
    queryFn: () => api.get<DashboardDetail>(`/dashboards/${dashboardId}`),
    enabled: !!dashboardId,
  });
}

export function useCreateDashboard() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { organization_id: string; name: string; description?: string }) =>
      api.post<{ id: string; name: string }>('/dashboards', body),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['dashboards', vars.organization_id] }),
  });
}

export function useDeleteDashboard() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (dashboardId: string) => api.delete(`/dashboards/${dashboardId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dashboards'] }),
  });
}

export function useAddWidget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      dashboard_id,
      ...body
    }: {
      dashboard_id: string;
      widget_type: string;
      title: string;
      pos_x?: number;
      pos_y?: number;
      width?: number;
      height?: number;
      config?: Record<string, unknown>;
    }) => api.post(`/dashboards/${dashboard_id}/widgets`, body),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['dashboard', vars.dashboard_id] }),
  });
}

export function useUpdateWidget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      widget_id,
      ...body
    }: {
      widget_id: string;
      title?: string;
      pos_x?: number;
      pos_y?: number;
      width?: number;
      height?: number;
      config?: Record<string, unknown>;
    }) => api.put(`/dashboards/widgets/${widget_id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dashboard'] }),
  });
}

export function useDeleteWidget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (widgetId: string) => api.delete(`/dashboards/widgets/${widgetId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dashboard'] }),
  });
}

export function useDashboardData(dashboardId: string | undefined, orgId: string, days = 30) {
  return useQuery<WidgetData[]>({
    queryKey: ['dashboard-data', dashboardId, orgId, days],
    queryFn: () =>
      api.get<WidgetData[]>(
        `/dashboards/${dashboardId}/data?organization_id=${orgId}&days=${days}`,
      ),
    enabled: !!dashboardId,
    refetchInterval: 60_000,
  });
}

export function useAnomalies(orgId: string, metric = 'ad_spend', days = 90) {
  return useQuery<Anomaly[]>({
    queryKey: ['dashboards-anomalies', orgId, metric, days],
    queryFn: () =>
      api.get<Anomaly[]>(
        `/dashboards/anomalies/${metric}?organization_id=${orgId}&days=${days}`,
      ),
    enabled: !!orgId,
    refetchInterval: 120_000,
  });
}

export function usePredictions(orgId: string, metric = 'ad_spend', periods = 7) {
  return useQuery<Prediction[]>({
    queryKey: ['dashboards-predictions', orgId, metric, periods],
    queryFn: () =>
      api.get<Prediction[]>(
        `/dashboards/predictions/${metric}?organization_id=${orgId}&periods=${periods}`,
      ),
    enabled: !!orgId,
    refetchInterval: 120_000,
  });
}
