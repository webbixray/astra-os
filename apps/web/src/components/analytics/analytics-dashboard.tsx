'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  description?: string;
  className?: string;
}

export function MetricCard({ title, value, change, changeLabel, icon, description, className }: MetricCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-gray-500 dark:text-gray-400">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(change !== undefined || description) && (
          <div className="mt-1 flex items-center gap-2">
            {change !== undefined && (
              <span
                className={cn(
                  'text-xs font-medium',
                  isPositive && 'text-green-600 dark:text-green-400',
                  isNegative && 'text-red-600 dark:text-red-400',
                  !isPositive && !isNegative && 'text-gray-500 dark:text-gray-400',
                )}
              >
                {isPositive ? '+' : ''}
                {change}%
              </span>
            )}
            {(changeLabel || description) && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {changeLabel || description}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface MetricsGridProps {
  metrics: MetricCardProps[];
  className?: string;
}

export function MetricsGrid({ metrics, className }: MetricsGridProps) {
  return (
    <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-4', className)}>
      {metrics.map((metric, index) => (
        <MetricCard key={index} {...metric} />
      ))}
    </div>
  );
}

interface AnalyticsOverviewProps {
  data: {
    visitors: number;
    pageViews: number;
    bounceRate: number;
    avgSessionDuration: number;
    conversions: number;
    conversionRate: number;
    revenue: number;
    topPages: { path: string; views: number; percentage: number }[];
    trafficSources: { source: string; visitors: number; percentage: number }[];
  };
  className?: string;
}

export function AnalyticsOverview({ data, className }: AnalyticsOverviewProps) {
  return (
    <div className={cn('space-y-6', className)}>
      <MetricsGrid
        metrics={[
          {
            title: 'Total Visitors',
            value: data.visitors.toLocaleString(),
            change: 12.5,
            changeLabel: 'vs last month',
            icon: (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            ),
          },
          {
            title: 'Page Views',
            value: data.pageViews.toLocaleString(),
            change: 8.2,
            changeLabel: 'vs last month',
            icon: (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            ),
          },
          {
            title: 'Bounce Rate',
            value: `${data.bounceRate}%`,
            change: -3.1,
            changeLabel: 'vs last month',
            icon: (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
              </svg>
            ),
          },
          {
            title: 'Avg. Session',
            value: `${Math.floor(data.avgSessionDuration / 60)}m ${data.avgSessionDuration % 60}s`,
            change: 5.4,
            changeLabel: 'vs last month',
            icon: (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ),
          },
        ]}
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Pages</CardTitle>
            <CardDescription>Most visited pages this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.topPages.map((page, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1 truncate font-mono text-sm">{page.path}</div>
                  <div className="ml-4 flex items-center gap-4">
                    <span className="text-sm text-gray-500">{page.views.toLocaleString()}</span>
                    <span className="w-12 text-right text-xs text-gray-400">{page.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Traffic Sources</CardTitle>
            <CardDescription>Where your visitors come from</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.trafficSources.map((source, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{source.source}</span>
                    <span className="text-sm text-gray-500">{source.visitors.toLocaleString()}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                    <div
                      className="h-full rounded-full bg-blue-600"
                      style={{ width: `${source.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface ConversionFunnelProps {
  steps: { name: string; count: number; percentage: number }[];
  className?: string;
}

export function ConversionFunnel({ steps, className }: ConversionFunnelProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Conversion Funnel</CardTitle>
        <CardDescription>User journey through your funnel</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{step.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">{step.count.toLocaleString()}</span>
                  <span className="text-xs text-gray-400">({step.percentage}%)</span>
                </div>
              </div>
              <div className="h-8 overflow-hidden rounded bg-gray-100 dark:bg-gray-800">
                <div
                  className="flex h-full items-center rounded bg-gradient-to-r from-blue-600 to-blue-400 px-3"
                  style={{ width: `${step.percentage}%` }}
                >
                  {step.percentage > 10 && (
                    <span className="text-xs font-medium text-white">{step.percentage}%</span>
                  )}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className="flex justify-center">
                  <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface RealTimeVisitorsProps {
  currentVisitors: number;
  pagesPerMinute: number;
  topPages: { path: string; visitors: number }[];
  className?: string;
}

export function RealTimeVisitors({ currentVisitors, pagesPerMinute, topPages, className }: RealTimeVisitorsProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Real-Time Visitors</CardTitle>
            <CardDescription>Currently on your site</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-green-600 dark:text-green-400">Live</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-6 text-center">
          <div className="text-4xl font-bold">{currentVisitors}</div>
          <div className="text-sm text-gray-500">active now</div>
        </div>
        <div className="mb-4 text-center text-sm text-gray-500">
          {pagesPerMinute} pages/minute
        </div>
        <div className="space-y-2">
          {topPages.map((page, index) => (
            <div key={index} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50">
              <span className="truncate font-mono text-sm">{page.path}</span>
              <span className="ml-2 text-sm text-gray-500">{page.visitors}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
