'use client';


import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Plus,
  Trash2,
  AlertTriangle,
  TrendingUp,
  X,
  GripVertical,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useOrg } from "@/hooks/use-org";
import {
  Dashboard,
  DashboardWidget,
  DashboardWidgetCreate,
  WidgetTypeOption,
  METRIC_OPTIONS,
  WIDGET_TYPE_OPTIONS,
} from "@/types/dashboard";
import { api } from "@/lib/api";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { KpiCardWidget } from "@/components/widgets/kpi-card";
import { ChartWidget } from "@/components/widgets/chart";
import { PieChartWidget } from "@/components/widgets/pie-chart";
import { DataTableWidget } from "@/components/widgets/data-table";
import { TrendWidget } from "@/components/widgets/trend";

export default function DashboardPage() {
  const { orgId } = useOrg();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [selectedDashId, setSelectedDashId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Dashboard | null>(null);
  const [widgetData, setWidgetData] = useState<DashboardWidget[]>([]);
  const [anomalies, setAnomalies] = useState<{ date: string; direction: "up" | "down"; value: number; severity: "high" | "medium"; z_score: number }[]>([]);
  const [predictions, setPredictions] = useState<{ date: string; predicted_value: number }[]>([]);
  const [showAnomalies, setShowAnomalies] = useState(false);
  const [showPredictions, setShowPredictions] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [showWidgetPicker, setShowWidgetPicker] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const { mutate: createDash, isPending: createPending } = api.dashboards.create.useMutation({
    onSuccess: () => {
      setShowCreate(false);
      setNewName("");
      refreshDashboards();
    },
  });
  const { mutate: deleteDash } = api.dashboards.delete.useMutation({
    onSuccess: () => refreshDashboards(),
  });
  const { mutate: createWidget, isPending: widgetPending } = api.widgets.create.useMutation({
    onSuccess: () => {
      setShowWidgetPicker(false);
      refreshWidgetData();
    },
  });
  const { mutate: deleteWidget } = api.widgets.delete.useMutation({
    onSuccess: () => refreshWidgetData(),
  });

  const refreshDashboards = async () => {
    try {
      const data = await api.dashboards.list({ orgId });
      setDashboards(data);
      if (!selectedDashId && data.length > 0) {
        setSelectedDashId(data[0].id);
      }
    } catch (e) {
      console.error("Failed to load dashboards:", e);
    }
  };

  const refreshWidgetData = async () => {
    if (!selectedDashId) return;
    try {
      const [widgets, anomalyData, predictionData] = await Promise.all([
        api.widgets.list({ dashboardId: selectedDashId, orgId }),
        api.analytics.anomalies({ orgId, metric: "campaigns_total" }).catch(() => []),
        api.analytics.predict({ orgId, metric: "campaigns_total", horizon: 7 }).catch(() => []),
      ]);
      setWidgetData(widgets);
      setAnomalies(anomalyData || []);
      setPredictions(predictionData || []);
    } catch (e) {
      console.error("Failed to load widget data:", e);
    }
  };

  useEffect(() => {
    refreshDashboards();
  }, [orgId]);

  useEffect(() => {
    if (selectedDashId) {
      refreshWidgetData();
      api.dashboards.get({ id: selectedDashId, orgId }).then(setDetail).catch(() => setDetail(null));
    } else {
      setDetail(null);
      setWidgetData([]);
    }
  }, [selectedDashId, orgId]);

  const handleCreate = () => {
    if (!newName.trim()) return;
    createDash({ orgId, name: newName.trim() });
  };

  const handleAddWidget = (widgetType: string, defaultW: number, defaultH: number) => {
    if (!selectedDashId) return;
    const canvasWidgets = detail?.widgets || [];
    const maxY = canvasWidgets.length > 0 ? Math.max(...canvasWidgets.map((w) => w.pos_y + w.height)) : 0;
    addWidget.mutate({
      dashboard_id: selectedDashId,
      organization_id: orgId,
      widget_type: widgetType,
      title: WIDGET_TYPE_OPTIONS.find((o) => o.type === widgetType)?.label || widgetType,
      pos_x: 0,
      pos_y: maxY,
      width: defaultW,
      height: defaultH,
    });

      widget_type: widgetType,
      title: WIDGET_TYPE_OPTIONS.find((o) => o.type === widgetType)?.label || widgetType,
      pos_x: 0,
      pos_y: maxY,
      width: defaultW,
      height: defaultH,
      config: { metric: "campaigns_total" },
    });
  };

  const activeDash = dashboards?.find((d) => d.id === selectedDashId);
  const canvasWidgets = detail?.widgets || [];
  const cols = activeDash?.layout_columns || 12;
  const anomalyCount = anomalies?.length || 0;
  const predictionCount = predictions?.length || 0;

  return (
    <ErrorBoundary>
      <div className="flex h-full flex-col">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b px-6 py-3">
          <div className="flex items-center gap-3">
            <LayoutDashboard className="h-5 w-5" />
            <h1 className="text-lg font-semibold">Dashboards</h1>
          </div>
          <div className="flex items-center gap-2">
            {anomalyCount > 0 && (
              <Button variant="outline" size="sm" onClick={() => setShowAnomalies(!showAnomalies)}>
                <AlertTriangle className="mr-1 h-3.5 w-3.5 text-yellow-500" />
                {anomalyCount} Anomalies
              </Button>
            )}
            {predictionCount > 0 && (
              <Button variant="outline" size="sm" onClick={() => setShowPredictions(!showPredictions)}>
                <TrendingUp className="mr-1 h-3.5 w-3.5" />
                Forecast
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => setShowCreate(true)}>
              <Plus className="mr-1 h-3.5 w-3.5" />
              New
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Dashboard sidebar */}
          <div className="hidden md:block w-56 shrink-0 border-r overflow-y-auto p-3">
            <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
              My Dashboards
            </p>
            <div className="space-y-1">
              {dashboards ? dashboards.map((d) => (
                <div
                  key={d.id}
                  className={cn(
                    "group flex items-center justify-between rounded-md px-3 py-2 text-sm cursor-pointer transition-colors",
                    selectedDashId === d.id
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                  )}
                  onClick={() => handleAddWidget(opt.type, opt.defaultW, opt.defaultH)}

                >
                  <span className="truncate">
                    {d.name}
                    {d.is_default && (
                      <span className="ml-1.5 text-[10px] text-muted-foreground">(default)</span>
                    )}
                  </span>
                  <button
                    aria-label="Delete dashboard"
                    className="hidden group-hover:block text-muted-foreground hover:text-red-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTargetId(d.id);
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              )) : [1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 rounded-md px-3 py-2">
                  <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                </div>
              ))}
            </div>
            {showCreate && (
              <div className="mt-3 space-y-2 rounded-md border p-3">
                <label htmlFor="dash-name" className="text-xs font-medium text-muted-foreground">
                  Dashboard name
                </label>
                <Input
                  id="dash-name"
                  placeholder="Dashboard name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  autoFocus
                />
                <div className="flex gap-2">
                  <Button size="sm" className="flex-1" onClick={handleCreate} disabled={!newName.trim() || createPending}>
                    Create
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setShowCreate(false); setNewName(""); }}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Main canvas */}
          <div className="flex-1 overflow-y-auto p-6">
            {!selectedDashId && (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <LayoutDashboard className="mx-auto mb-3 h-12 w-12 opacity-20" />
                  <p className="text-lg font-medium">Select or create a dashboard</p>
                  <p className="mt-1 text-sm">Choose a dashboard from the sidebar or create a new one</p>
                </div>
              </div>
            )}

            {selectedDashId && (
              <>
                {/* Dashboard header */}
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">{activeDash?.name}</h2>
                    {activeDash?.description && (
                      <p className="text-sm text-muted-foreground">{activeDash.description}</p>
                    )}
                  </div>
                  <Button size="sm" onClick={() => setShowWidgetPicker(true)}>
                    <Plus className="mr-1 h-4 w-4" />
                    Add Widget
                  </Button>
                </div>

                {/* Anomaly panel */}
                {showAnomalies && anomalies && anomalies.length > 0 && (
                  <div className="mb-6 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        <span className="font-medium text-sm">Anomaly Detection</span>
                      </div>
                      <button aria-label="Close anomalies" onClick={() => setShowAnomalies(false)}>
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {anomalies.slice(0, 10).map((a, i) => (
                        <div key={i} className="flex items-center gap-3 text-sm">
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            a.severity === "high" ? "bg-red-500/10 text-red-500" : "bg-yellow-500/10 text-yellow-500"
                          )}>
                            {a.severity}
                          </span>
                          <span className="text-muted-foreground">{a.date}</span>
                          <span className="font-medium">{a.direction === "up" ? "↑" : "↓"} {a.value.toFixed(2)}</span>
                          <span className="text-xs text-muted-foreground">z={a.z_score.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Prediction panel */}
                {showPredictions && predictions && predictions.length > 0 && (
                  <div className="mb-6 rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-blue-500" />
                        <span className="font-medium text-sm">Forecast — Ad Spend</span>
                      </div>
                      <button aria-label="Close predictions" onClick={() => setShowPredictions(false)}>
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="mt-3 flex gap-4">
                      {predictions.slice(0, 7).map((p, i) => (
                        <div key={i} className="flex-1 rounded bg-card p-2 text-center text-sm">
                          <p className="text-[10px] text-muted-foreground">{p.date.slice(5)}</p>
                          <p className="mt-1 font-semibold">${p.predicted_value.toFixed(0)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Widget grid */}
                <div
                  className="grid gap-4"
                  style={{
                    gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
                    gridAutoRows: "minmax(100px, auto)",
                  }}
                >
                  {canvasWidgets.length > 0 ? (canvasWidgets.map((w) => {
                    const spanX = Math.min(w.width, cols);
                    const dataItem = widgetData?.find((wd) => wd.widget_id === w.id);
                    const rawValue = dataItem?.data?.value;
                    const metricLabel = METRIC_OPTIONS.find((m) => m.value === dataItem?.config?.metric)?.label || String(w.config?.metric ?? "") || "—";

                    return (
                      <div
                        key={w.id}
                        className="group relative rounded-lg border bg-card shadow-sm transition-shadow hover:shadow-md"
                        style={{
                          gridColumn: `span ${spanX}`,
                          gridRow: `span ${w.height}`,
                        }}
                      >
                        {/* Widget header */}
                        <div className="flex items-center justify-between border-b px-3 py-2">
                          <div className="flex items-center gap-2">
                            <GripVertical className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="text-xs font-medium text-muted-foreground">{w.title}</span>
                          </div>
                          <button
                            aria-label="Delete widget"
                            className="hidden group-hover:block text-muted-foreground hover:text-red-500"
                            onClick={() => deleteWidget.mutate({ widgetId: w.id, orgId })}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>

                        {/* Widget body */}
                        <div className="p-4">
                          {dataItem ? (
                            <>
                              {w.widget_type === "kpi_card" && (
                                <KpiCardWidget value={rawValue} label={metricLabel} />
                              )}
                              {(w.widget_type === "line_chart" || w.widget_type === "bar_chart") && (
                                <ChartWidget type={w.widget_type} data={dataItem?.data} />
                              )}
                              {w.widget_type === "pie_chart" && (
                                <PieChartWidget data={dataItem?.data} />
                              )}
                              {w.widget_type === "data_table" && (
                                <DataTableWidget data={dataItem?.data} />
                              )}
                              {w.widget_type === "trend_indicator" && (
                                <TrendWidget value={rawValue} label={metricLabel} />
                              )}
                            </>
                          ) : (
                            [1, 2, 3].map((i) => (
                              <div
                                key={i}
                                className="rounded-lg border bg-card p-4"
                                style={{ gridColumn: `span ${Math.min(4, cols)}` }}
                              >
                                <div className="h-3 w-20 animate-pulse rounded bg-muted" />
                                <div className="mt-3 h-12 animate-pulse rounded bg-muted" />
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  : (
                    <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                      <BarChart3 className="mb-3 h-10 w-10 opacity-20" />
                      <p className="font-medium">Empty dashboard</p>
                      <p className="mt-1 text-sm">Click "Add Widget" to start building</p>
                    </div>
                  )}
                </div>

                {/* Widget picker modal */}
                {showWidgetPicker && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" role="dialog" aria-modal="true" aria-label="Add Widget" onClick={() => setShowWidgetPicker(false)}>
                    <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-lg" onClick={(e) => e.stopPropagation()}>
                      <div className="mb-4 flex items-center justify-between">
                        <h3 className="font-semibold">Add Widget</h3>
                        <button aria-label="Close widget picker" onClick={() => setShowWidgetPicker(false)}}>
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        {WIDGET_TYPE_OPTIONS.map((opt) => (
                          <button
                            key={opt.type}
                            className="flex flex-col items-center gap-2 rounded-lg border p-4 text-sm hover:bg-accent transition-colors"
                            onClick={() => handleAddWidget(opt.type, opt.defaultW, opt.defaultH)}
                          >
                            <opt.icon className="h-6 w-6" />
                            <span className="font-medium">{opt.label}</span>
                            <span className="text-[10px] text-muted-foreground">{opt.defaultW}x{opt.defaultH}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <ConfirmDialog
          open={!!deleteTargetId}
          onOpenChange={(open) => { if (!open) setDeleteTargetId(null); }}
          title="Delete Dashboard"
          description="Are you sure you want to delete this dashboard? This action cannot be undone."
          confirmLabel="Delete"
          variant="destructive"
          onConfirm={() => {
            if (deleteTargetId) deleteDash({ dashboardId: deleteTargetId, orgId });
          }}
          loading={deleteDash.isPending}
        />
      </div>
    </ErrorBoundary>
  );
}
