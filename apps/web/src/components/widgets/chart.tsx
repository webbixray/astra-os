'use client';

import { memo } from 'react';
import { cn } from '@/lib/utils';

interface ChartWidgetProps {
  type: string;
  data?: unknown;
}

export const ChartWidget = memo(function ChartWidget({ type }: ChartWidgetProps) {
  return (
    <div className="flex h-20 items-end gap-1">
      {Array.from({ length: 12 }).map((_, i) => {
        const h = Math.max(8, ((Math.sin(i * 1.5) + 1) / 2) * 80);
        return (
          <div
            key={i}
            className={cn(
              'flex-1 rounded-t transition-all',
              type === 'line_chart' ? 'bg-primary/60' : 'bg-primary/40',
            )}
            style={{ height: `${h}%` }}
          />
        );
      })}
    </div>
  );
});
