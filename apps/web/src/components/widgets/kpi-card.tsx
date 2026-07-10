'use client';

import { memo } from 'react';

interface KpiCardWidgetProps {
  value: unknown;
  label: string;
}

export const KpiCardWidget = memo(function KpiCardWidget({ value, label }: KpiCardWidgetProps) {
  const num = typeof value === 'number' ? value : 0;
  const formatted =
    typeof value === 'number'
      ? value > 9999
        ? num.toLocaleString()
        : num.toFixed(2)
      : String(value || '—');
  return (
    <div className="text-center">
      <p className="text-2xl font-bold">{formatted}</p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
});
