'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { getReportExportUrl } from '@/features/reports/api/useReports';

const REPORT_TYPES = [
  { value: 'overview', label: 'Overview' },
  { value: 'campaigns', label: 'Campaigns' },
  { value: 'ads', label: 'Ad Performance' },
  { value: 'content', label: 'Content' },
  { value: 'email', label: 'Email' },
  { value: 'platform_comparison', label: 'Platform Comparison' },
];

const FORMATS = ['csv', 'json', 'html'];

export function ReportsExportTab({ orgId }: { orgId: string }) {
  const [selectedExportType, setSelectedExportType] = useState('overview');
  const [selectedFormat, setSelectedFormat] = useState('csv');
  const [exportDays, setExportDays] = useState(30);

  return (
    <div className="max-w-xl space-y-4">
      <h2 className="font-semibold">Export Report</h2>
      <div className="rounded-lg border bg-card p-4 space-y-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Report Type</label>
          <Select value={selectedExportType} onChange={(e) => setSelectedExportType(e.target.value)}
            options={REPORT_TYPES} />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Format</label>
          <div className="mt-1 flex gap-2">
            {FORMATS.map((f) => (
              <button key={f} onClick={() => setSelectedFormat(f)}
                className={cn(
                  'rounded border px-3 py-1.5 text-sm transition-colors',
                  selectedFormat === f ? 'border-primary bg-primary/10 font-medium' : 'hover:bg-accent',
                )}>
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Days</label>
          <Input type="number" value={exportDays} onChange={(e) => setExportDays(Number(e.target.value))}
            min={1} max={365} className="w-24" />
        </div>
        <a
          href={getReportExportUrl(orgId, selectedExportType, selectedFormat, exportDays)}
          target="_blank" rel="noreferrer noopener"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Download className="h-4 w-4" />
          Export {selectedFormat.toUpperCase()}
        </a>
      </div>
    </div>
  );
}
