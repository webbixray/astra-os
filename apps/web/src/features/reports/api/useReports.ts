import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface TrendData {
  metric: string;
  days: number;
  start_date: string;
  end_date: string;
  daily: { date: string; value: number }[];
  average: number;
  peak: number;
  total: number;
}

export interface PlatformComparison {
  platforms: {
    platform: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    revenue: number;
    ctr: number;
    cpc: number;
    roas: number;
  }[];
  total_platforms: number;
}

export interface ReportSchedule {
  id: string;
  name: string;
  report_type: string;
  frequency: string;
  recipients: string[];
  next_run_at: string | null;
  last_run_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  report_type: string;
  config: Record<string, unknown>;
  created_at: string;
}

export interface DeliveryLog {
  id: string;
  report_type: string;
  format: string;
  channel: string;
  recipient: string;
  status: string;
  error_message: string;
  generated_at: string;
}

export interface PeriodComparison {
  report_type: string;
  comparison: string;
  current_period: { days: number; data: Record<string, unknown> };
  previous_period: { data: Record<string, unknown> };
}

export function useReportTrends(orgId: string, metric = 'spend', days = 30) {
  return useQuery<TrendData>({
    queryKey: ['reports', 'trends', orgId, metric, days],
    queryFn: () =>
      api.get<TrendData>(
        `/reports/trends?organization_id=${orgId}&metric=${metric}&days=${days}`,
      ),
  });
}

export function usePlatformComparison(orgId: string) {
  return useQuery<PlatformComparison>({
    queryKey: ['reports', 'platforms', orgId],
    queryFn: () =>
      api.get<PlatformComparison>(`/reports/platforms?organization_id=${orgId}`),
  });
}

export function useReportSchedules(orgId: string) {
  return useQuery<ReportSchedule[]>({
    queryKey: ['reports', 'schedules', orgId],
    queryFn: () =>
      api.get<ReportSchedule[]>(`/reports/schedules?organization_id=${orgId}`),
  });
}

export function useCreateReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      organization_id: string;
      name: string;
      report_type?: string;
      frequency?: string;
      is_active?: boolean;
      recipients?: string[];
      config?: Record<string, unknown>;
    }) => api.post<ReportSchedule>('/reports/schedules', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'schedules'] });
    },
  });
}

export function useDeleteReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: string) =>
      api.delete(`/reports/schedules/${scheduleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'schedules'] });
    },
  });
}

// ── Templates ───────────────────────────────────────────────────────────────

export function useReportTemplates(orgId: string) {
  return useQuery<ReportTemplate[]>({
    queryKey: ['reports', 'templates', orgId],
    queryFn: () =>
      api.get<ReportTemplate[]>(`/reports/templates?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useCreateReportTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, ...body }: {
      orgId: string; name: string; report_type?: string;
      config?: Record<string, unknown>; description?: string;
    }) =>
      api.post(`/reports/templates?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports', 'templates'] }),
  });
}

export function useDeleteReportTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (templateId: string) => api.delete(`/reports/templates/${templateId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports', 'templates'] }),
  });
}

// ── Delivery ────────────────────────────────────────────────────────────────

export function useDeliveryLogs(orgId: string) {
  return useQuery<DeliveryLog[]>({
    queryKey: ['reports', 'delivery', orgId],
    queryFn: () =>
      api.get<DeliveryLog[]>(`/reports/delivery-logs?organization_id=${orgId}`),
    enabled: !!orgId,
  });
}

export function useDeliverReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, ...body }: {
      orgId: string; report_type: string; channel: string;
      recipient: string; format: string; days?: number;
    }) => api.post(`/reports/deliver?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports', 'delivery'] }),
  });
}

// ── Period Comparison ───────────────────────────────────────────────────────

export function useComparePeriods() {
  return useMutation({
    mutationFn: ({ orgId, ...body }: {
      orgId: string; report_type?: string;
      current_days?: number; comparison?: string; custom_days?: number | null;
    }) => api.post<PeriodComparison>(`/reports/compare?organization_id=${orgId}`, body),
  });
}

// ── Generate report URL helper ──────────────────────────────────────────────

export function getReportExportUrl(orgId: string, reportType: string,
                                    format: string = 'csv', days: number = 30): string {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  return `${base}/reports/generate/${reportType}?organization_id=${orgId}&format=${format}&days=${days}`;
}
