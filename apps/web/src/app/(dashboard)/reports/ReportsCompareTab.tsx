'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useComparePeriods } from '@/features/reports/api/useReports';

export function ReportsCompareTab({ orgId }: { orgId: string }) {
  const comparePeriods = useComparePeriods();

  const [compareResult, setCompareResult] = useState<Record<string, unknown> | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const handleCompare = async () => {
    setCompareLoading(true);
    comparePeriods.mutate({ orgId }, {
      onSuccess: (data) => setCompareResult(data as unknown as Record<string, unknown>),
      onSettled: () => setCompareLoading(false),
    });
  };

  return (
    <div className="max-w-2xl space-y-4">
      <h2 className="font-semibold">Period Comparison</h2>
      <div className="rounded-lg border bg-card p-4 space-y-4">
        <p className="text-sm text-muted-foreground">
          Compare current 30-day performance against the previous period.
        </p>
        <Button onClick={handleCompare} disabled={compareLoading}>
          {compareLoading ? 'Comparing...' : 'Compare Periods'}
        </Button>
      </div>

      {compareResult && (
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-medium mb-3">Comparison Results</h3>
          <div className="space-y-2 text-sm">
            {Object.entries(compareResult).filter(([k]) => k !== 'comparison').map(([key, val]) => (
              <div key={key} className="flex justify-between">
                <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                <span>{String(val)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
