import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  metric: string;
  condition: 'gt' | 'lt' | 'gte' | 'lte' | 'eq' | 'neq';
  threshold: number;
  windowMinutes: number;
  severity: 'info' | 'warning' | 'critical';
  channels: string[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
  lastTriggeredAt: string | null;
  triggerCount: number;
}

export interface AlertInstance {
  id: string;
  ruleId: string;
  organizationId: string;
  metric: string;
  value: number;
  threshold: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  triggeredAt: string;
  resolvedAt: string | null;
  acknowledgedAt: string | null;
  acknowledgedBy: string | null;
}

export interface Anomaly {
  id: string;
  organizationId: string;
  metric: string;
  expectedValue: number;
  actualValue: number;
  deviationPercentage: number;
  severity: 'info' | 'warning' | 'critical';
  detectedAt: string;
  context: Record<string, any>;
}

export interface CostBreakdown {
  organizationId: string;
  periodStart: string;
  periodEnd: string;
  totalCostCents: number;
  byCategory: Record<string, number>;
  byCampaign: Array<{ campaignId: string; campaignName: string; costCents: number }>;
  byPlatform: Array<{ platform: string; costCents: number }>;
  modelInferenceCostCents: number;
  projectedMonthlyCostCents: number;
}

export interface SLAReport {
  organizationId: string;
  periodStart: string;
  periodEnd: string;
  availabilityPercentage: number;
  latencyP50Ms: number;
  latencyP95Ms: number;
  latencyP99Ms: number;
  errorRatePercentage: number;
  totalRequests: number;
  failedRequests: number;
  slaTarget: {
    availability: number;
    latencyP99Ms: number;
    errorRatePercentage: number;
  };
  compliance: boolean;
}

export interface GrafanaDashboard {
  uid: string;
  title: string;
  description: string;
  tags: string[];
  url: string;
}

interface ObservabilityState {
  // Alert rules
  alertRules: AlertRule[];
  alertInstances: AlertInstance[];
  
  // Anomalies
  anomalies: Anomaly[];
  
  // Costs
  costBreakdown: CostBreakdown | null;
  
  // SLA
  slaReport: SLAReport | null;
  
  // Grafana
  grafanaDashboards: GrafanaDashboard[];
  
  // Loading states
  isLoadingAlerts: boolean;
  isLoadingAnomalies: boolean;
  isLoadingCosts: boolean;
  isLoadingSLA: boolean;
  isLoadingDashboards: boolean;
  
  // Actions
  setAlertRules: (rules: AlertRule[]) => void;
  addAlertRule: (rule: AlertRule) => void;
  updateAlertRule: (id: string, updates: Partial<AlertRule>) => void;
  deleteAlertRule: (id: string) => void;
  
  setAlertInstances: (instances: AlertInstance[]) => void;
  acknowledgeAlert: (instanceId: string) => void;
  resolveAlert: (instanceId: string) => void;
  
  setAnomalies: (anomalies: Anomaly[]) => void;
  
  setCostBreakdown: (costs: CostBreakdown) => void;
  
  setSLAReport: (report: SLAReport) => void;
  
  setGrafanaDashboards: (dashboards: GrafanaDashboard[]) => void;
  
  setLoading: (key: keyof Pick<ObservabilityState, 
    'isLoadingAlerts' | 'isLoadingAnomalies' | 'isLoadingCosts' | 'isLoadingSLA' | 'isLoadingDashboards'
  >, value: boolean) => void;
  
  reset: () => void;
}

const initialState = {
  alertRules: [],
  alertInstances: [],
  anomalies: [],
  costBreakdown: null,
  slaReport: null,
  grafanaDashboards: [],
  isLoadingAlerts: false,
  isLoadingAnomalies: false,
  isLoadingCosts: false,
  isLoadingSLA: false,
  isLoadingDashboards: false,
};

export const useObservabilityStore = create<ObservabilityState>()(
  persist(
    (set) => ({
      ...initialState,
      
      setAlertRules: (rules) => set({ alertRules: rules }),
      
      addAlertRule: (rule) => set((state) => ({
        alertRules: [...state.alertRules, rule],
      })),
      
      updateAlertRule: (id, updates) => set((state) => ({
        alertRules: state.alertRules.map((r) =>
          r.id === id ? { ...r, ...updates, updatedAt: new Date().toISOString() } : r
        ),
      })),
      
      deleteAlertRule: (id) => set((state) => ({
        alertRules: state.alertRules.filter((r) => r.id !== id),
      })),
      
      setAlertInstances: (instances) => set({ alertInstances: instances }),
      
      acknowledgeAlert: (instanceId) => set((state) => ({
        alertInstances: state.alertInstances.map((i) =>
          i.id === instanceId
            ? { ...i, acknowledgedAt: new Date().toISOString() }
            : i
        ),
      })),
      
      resolveAlert: (instanceId) => set((state) => ({
        alertInstances: state.alertInstances.map((i) =>
          i.id === instanceId
            ? { ...i, resolvedAt: new Date().toISOString() }
            : i
        ),
      })),
      
      setAnomalies: (anomalies) => set({ anomalies }),
      
      setCostBreakdown: (costs) => set({ costBreakdown: costs }),
      
      setSLAReport: (report) => set({ slaReport: report }),
      
      setGrafanaDashboards: (dashboards) => set({ grafanaDashboards: dashboards }),
      
      setLoading: (key, value) => set({ [key]: value }),
      
      reset: () => set(initialState),
    }),
    {
      name: 'astra-observability',
      partialize: (state) => ({
        alertRules: state.alertRules,
        grafanaDashboards: state.grafanaDashboards,
      }),
    }
  )
);