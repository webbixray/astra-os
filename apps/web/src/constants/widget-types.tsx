import { BarChart3, LineChart, BarChart, PieChart, Table, TrendingUp } from 'lucide-react'

export interface WidgetTypeOption {
  type: string
  label: string
  icon: React.ReactNode
  defaultW: number
  defaultH: number
}

export const WIDGET_TYPE_OPTIONS: WidgetTypeOption[] = [
  { type: 'kpi_card', label: 'KPI Card', icon: <BarChart3 className="h-6 w-6" />, defaultW: 3, defaultH: 2 },
  { type: 'line_chart', label: 'Line Chart', icon: <LineChart className="h-6 w-6" />, defaultW: 6, defaultH: 4 },
  { type: 'bar_chart', label: 'Bar Chart', icon: <BarChart className="h-6 w-6" />, defaultW: 6, defaultH: 4 },
  { type: 'pie_chart', label: 'Pie Chart', icon: <PieChart className="h-6 w-6" />, defaultW: 4, defaultH: 4 },
  { type: 'data_table', label: 'Data Table', icon: <Table className="h-6 w-6" />, defaultW: 6, defaultH: 6 },
  { type: 'trend_indicator', label: 'Trend Indicator', icon: <TrendingUp className="h-6 w-6" />, defaultW: 3, defaultH: 2 },
]

export const METRIC_OPTIONS = [
  { value: 'campaigns_total', label: 'Total Campaigns' },
  { value: 'spend_total', label: 'Total Spend' },
  { value: 'impressions_total', label: 'Total Impressions' },
  { value: 'clicks_total', label: 'Total Clicks' },
  { value: 'conversions_total', label: 'Total Conversions' },
  { value: 'cpa', label: 'Cost Per Acquisition' },
  { value: 'roas', label: 'Return on Ad Spend' },
  { value: 'ctr', label: 'Click-Through Rate' },
]