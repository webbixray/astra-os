'use client';

import { memo } from 'react';

interface TrendWidgetProps {
  data?: unknown;
  value?: unknown;
  label?: string;
}

function extractTrend(data?: unknown, value?: unknown, label?: string): { direction?: string; displayValue?: string; displayLabel?: string } {
  if (value !== undefined) {
    return {
      direction: typeof value === 'number' ? (value >= 0 ? 'up' : 'down') : undefined,
      displayValue: String(value),
      displayLabel: label || '',
    };
  }

  if (!data || typeof data !== 'object') return {};
  const obj = data as Record<string, unknown>;
  const direction = obj.direction === 'up' || obj.direction === 'down' ? obj.direction : undefined;
  return {
    direction,
    displayValue: typeof obj.value === 'string' ? obj.value : undefined,
    displayLabel: typeof obj.label === 'string' ? obj.label : undefined,
  };
}

export const TrendWidget = memo(function TrendWidget({ data, value, label }: TrendWidgetProps) {
  const { direction, displayValue, displayLabel } = extractTrend(data, value, label);
  const isUp = direction === 'up';
  return (
    <div className="text-center">
      <p className={`text-lg font-bold ${isUp ? 'text-green-500' : 'text-red-500'}`}>
        {direction ? (isUp ? '↑' : '↓') : ''} {displayValue || '—'}
      </p>
      <p className="text-xs text-muted-foreground">{displayLabel || ''}</p>
    </div>
  );
});
