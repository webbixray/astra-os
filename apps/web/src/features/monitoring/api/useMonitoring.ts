import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}

export interface JobRecord {
  id: string;
  job_type: string;
  status: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string;
  retry_count: number;
  max_retries: number;
  created_at: string;
}

export interface ApiUsageRecord {
  id: string;
  user_id: string;
  endpoint: string;
  method: string;
  status_code: number;
  ip_address: string;
  response_time_ms: number;
  created_at: string;
}

export interface UsageStats {
  period_hours: number;
  total_calls: number;
  avg_response_time_ms: number;
  max_response_time_ms: number;
  by_endpoint: { endpoint: string; method: string; count: number; avg_response_time_ms: number }[];
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  checks: Record<string, { status: string; response_time_ms?: number; error?: string }>;
}

// Audit Logs
export function useAuditLogs(orgId: string, action?: string, resourceType?: string, limit = 100) {
  const params = new URLSearchParams({ organization_id: orgId, limit: String(limit) });
  if (action) params.set('action', action);
  if (resourceType) params.set('resource_type', resourceType);
  return useQuery<AuditLogEntry[]>({
    queryKey: ['audit-logs', orgId, action, resourceType],
    queryFn: () => api.get<AuditLogEntry[]>(`/audit-logs?${params}`),
    refetchInterval: 30_000,
  });
}

export function useAuditSummary(orgId: string, hours = 24) {
  return useQuery({
    queryKey: ['audit-logs', 'summary', orgId, hours],
    queryFn: () => api.get(`/audit-logs/summary?organization_id=${orgId}&hours=${hours}`),
  });
}

// Jobs
export function useJobs(orgId: string, status?: string, jobType?: string, limit = 100) {
  const params = new URLSearchParams({ organization_id: orgId, limit: String(limit) });
  if (status) params.set('status', status);
  if (jobType) params.set('job_type', jobType);
  return useQuery<JobRecord[]>({
    queryKey: ['jobs', orgId, status, jobType],
    queryFn: () => api.get<JobRecord[]>(`/jobs?${params}`),
    refetchInterval: 15_000,
  });
}

export function useCreateJob(orgId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { job_type: string; payload?: Record<string, unknown>; max_retries?: number }) =>
      api.post(`/jobs?organization_id=${orgId}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useUpdateJobStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, status, result, error_message }: { jobId: string; status: string; result?: Record<string, unknown>; error_message?: string }) =>
      api.patch(`/jobs/${jobId}/status`, { status, result, error_message }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useRetryJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => api.post(`/jobs/${jobId}/retry`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useJobSummary(orgId: string) {
  return useQuery({
    queryKey: ['jobs', 'summary', orgId],
    queryFn: () => api.get(`/jobs/summary?organization_id=${orgId}`),
    refetchInterval: 30_000,
  });
}

// API Usage
export function useUsageRecords(orgId: string, limit = 100) {
  return useQuery<ApiUsageRecord[]>({
    queryKey: ['usage-records', orgId, limit],
    queryFn: () => api.get<ApiUsageRecord[]>(`/usage-records?organization_id=${orgId}&limit=${limit}`),
  });
}

export function useUsageStats(orgId: string, hours = 24) {
  return useQuery<UsageStats>({
    queryKey: ['usage-records', 'stats', orgId, hours],
    queryFn: () => api.get<UsageStats>(`/usage-records/stats?organization_id=${orgId}&hours=${hours}`),
    refetchInterval: 30_000,
  });
}

// Health
export function useSystemHealth() {
  return useQuery<HealthCheck>({
    queryKey: ['system', 'health'],
    queryFn: () => api.get<HealthCheck>('/system/health'),
    refetchInterval: 60_000,
  });
}
