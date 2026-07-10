'use client';

import { memo } from 'react';

function parseTableData(data: unknown): Record<string, unknown> {
  if (!data || typeof data !== 'object') return {};
  const obj = data as Record<string, unknown>;
  const value = obj.value;
  if (!value || typeof value !== 'object') return {};
  return value as Record<string, unknown>;
}

interface DataTableWidgetProps {
  data?: unknown;
}

export const DataTableWidget = memo(function DataTableWidget({ data }: DataTableWidgetProps) {
  const entries = Object.entries(parseTableData(data));
  return (
    <div className="max-h-40 overflow-y-auto text-xs">
      {entries.length === 0 && <p className="text-center text-muted-foreground">No data</p>}
      <table className="w-full">
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k} className="border-b last:border-0">
              <td className="py-1 pr-2 text-muted-foreground">{k}</td>
              <td className="py-1 font-medium text-right">{String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});
