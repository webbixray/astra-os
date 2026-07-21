'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { DashboardsService } from './generated/services/DashboardsService'

// Types
export interface Dashboard {
  id: string
  organization_id: string
  name: string
  description?: string
  layout_columns: number
  is_default: boolean
  created_at: string
  updated_at: string
  widgets?: DashboardWidget[]
}

export interface DashboardWidget {
  id: string
  dashboard_id: string
  organization_id: string
  widget_type: string
  title: string
  pos_x: number
  pos_y: number
  width: number
  height: number
  config: Record<string, unknown>
  created_at: string
  updated_at: string
  // API response includes data field for widget data
  data?: Record<string, unknown>
}

export interface CreateDashboardRequest {
  organization_id: string
  name: string
  description?: string
  layout_columns?: number
}

export interface CreateWidgetRequest {
  dashboard_id: string
  organization_id: string
  widget_type: string
  title: string
  pos_x: number
  pos_y: number
  width: number
  height: number
  config: Record<string, unknown>
}

export interface Anomaly {
  date: string
  direction: 'up' | 'down'
  value: number
  severity: 'high' | 'medium'
  z_score: number
}

export interface Prediction {
  date: string
  predicted_value: number
}

// Dashboard hooks
export function useDashboards(orgId: string) {
  return useQuery({
    queryKey: ['dashboards', orgId],
    queryFn: async () => {
      const response = await DashboardsService.listDashboardsApiV1DashboardsGet(orgId)
      return response as Dashboard[]
    },
    enabled: !!orgId,
  })
}

export function useDashboard(dashboardId: string, orgId: string) {
  return useQuery({
    queryKey: ['dashboard', dashboardId, orgId],
    queryFn: async () => {
      const response = await DashboardsService.getDashboardApiV1DashboardsDashboardIdGet(dashboardId, orgId)
      return response as Dashboard
    },
    enabled: !!dashboardId && !!orgId,
  })
}

export function useCreateDashboard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateDashboardRequest) => {
      const response = await DashboardsService.createDashboardApiV1DashboardsPost(data)
      return response as Dashboard
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards', variables.organization_id] })
    },
  })
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ dashboardId, orgId }: { dashboardId: string; orgId: string }) =>
      DashboardsService.deleteDashboardApiV1DashboardsDashboardIdDelete(dashboardId, orgId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards', variables.orgId] })
    },
  })
}

// Widget hooks - get widgets from dashboard detail
export function useWidgets(dashboardId: string, orgId: string) {
  return useQuery({
    queryKey: ['widgets', dashboardId, orgId],
    queryFn: async () => {
      const response = await DashboardsService.getDashboardApiV1DashboardsDashboardIdGet(dashboardId, orgId)
      const dashboard = response as unknown as Dashboard
      return (dashboard.widgets || []) as DashboardWidget[]
    },
    enabled: !!dashboardId && !!orgId,
  })
}

export function useCreateWidget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateWidgetRequest) => {
      const response = await DashboardsService.addWidgetApiV1DashboardsDashboardIdWidgetsPost(data.dashboard_id, data.organization_id, data)
      return response as unknown as DashboardWidget
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['widgets', variables.dashboard_id, variables.organization_id] })
    },
  })
}

export function useDeleteWidget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ widgetId, orgId }: { widgetId: string; orgId: string }) =>
      DashboardsService.deleteWidgetApiV1DashboardsWidgetsWidgetIdDelete(widgetId, orgId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['widgets', variables.widgetId, variables.orgId] })
    },
  })
}

// Analytics hooks - using DashboardsService for anomalies/predictions
export function useAnomalies(orgId: string, metric: string) {
  return useQuery({
    queryKey: ['anomalies', orgId, metric],
    queryFn: async () => {
      const response = await DashboardsService.getAnomaliesApiV1DashboardsAnomaliesMetricGet(metric, orgId)
      return response as Anomaly[]
    },
    enabled: !!orgId && !!metric,
  })
}

export function usePredictions(orgId: string, metric: string, horizon: number = 7) {
  return useQuery({
    queryKey: ['predictions', orgId, metric, horizon],
    queryFn: async () => {
      const response = await DashboardsService.getPredictionsApiV1DashboardsPredictionsMetricGet(metric, orgId, horizon)
      return response as Prediction[]
    },
    enabled: !!orgId && !!metric,
  })
}

// Dashboard data hook
export function useDashboardData(dashboardId: string, orgId: string, days: number = 30) {
  return useQuery({
    queryKey: ['dashboard-data', dashboardId, orgId, days],
    queryFn: async () => {
      const response = await DashboardsService.getDashboardDataApiV1DashboardsDashboardIdDataGet(dashboardId, orgId, days)
      return response
    },
    enabled: !!dashboardId && !!orgId,
  })
}

export function useDashboardMetrics(metric: string, orgId: string, days: number = 30) {
  return useQuery({
    queryKey: ['dashboard-metric', metric, orgId, days],
    queryFn: async () => {
      const response = await DashboardsService.getMetricApiV1DashboardsMetricsMetricGet(metric, orgId, days)
      return response
    },
    enabled: !!metric && !!orgId,
  })
}