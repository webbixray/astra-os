'use client';

import { memo } from 'react';

function parsePieData(data: unknown): Record<string, number> {
  if (!data || typeof data !== 'object') return {};
  const obj = data as Record<string, unknown>;
  const value = obj.value;
  if (!value || typeof value !== 'object') return {};
  const result: Record<string, number> = {};
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    if (typeof v === 'number') {
      result[k] = v;
    }
  }
  return result;
}

interface PieChartWidgetProps {
  data?: unknown;
}

export const PieChartWidget = memo(function PieChartWidget({ data }: PieChartWidgetProps) {
  const entries = Object.entries(parsePieData(data));
  const total = entries.reduce((s, [, v]) => s + v, 0);
  return (
    <div className="flex flex-wrap gap-3 text-xs">
      {entries.length === 0 && <p className="text-center text-muted-foreground">No data</p>}
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-primary/60" />
          <span className="text-muted-foreground">{k}</span>
          <span className="font-medium">{total ? Math.round((v / total) * 100) : 0}%</span>
        </div>
      ))}
    </div>
  );
});
