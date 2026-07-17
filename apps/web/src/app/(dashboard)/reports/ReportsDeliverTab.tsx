'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LegacySelect as Select } from '@/components/ui/select';
import { useDeliverReport } from '@/features/reports/api/useReports';

const REPORT_TYPES = [
  { value: 'overview', label: 'Overview' },
  { value: 'campaigns', label: 'Campaigns' },
  { value: 'ads', label: 'Ad Performance' },
  { value: 'content', label: 'Content' },
  { value: 'email', label: 'Email' },
  { value: 'platform_comparison', label: 'Platform Comparison' },
];

const FORMATS = ['csv', 'json', 'html'];
const CHANNELS = ['download', 'email', 'slack', 'webhook'];

export function ReportsDeliverTab({ orgId }: { orgId: string }) {
  const deliverReport = useDeliverReport();

  const [deliverChannel, setDeliverChannel] = useState('email');
  const [deliverRecipient, setDeliverRecipient] = useState('');
  const [deliverFormat, setDeliverFormat] = useState('csv');
  const [deliverType, setDeliverType] = useState('overview');
  const [deliverDays, setDeliverDays] = useState(30);
  const [delivering, setDelivering] = useState(false);

  const handleDeliver = () => {
    setDelivering(true);
    deliverReport.mutate({
      orgId, report_type: deliverType, channel: deliverChannel,
      recipient: deliverRecipient, format: deliverFormat, days: deliverDays,
    }, {
      onSettled: () => setDelivering(false),
      onSuccess: () => { setDeliverRecipient(''); },
    });
  };

  return (
    <div className="max-w-xl space-y-4">
      <h2 className="font-semibold">Deliver Report</h2>
      <div className="rounded-lg border bg-card p-4 space-y-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Report Type</label>
          <Select value={deliverType} onChange={(e) => setDeliverType(e.target.value)}
            options={REPORT_TYPES} />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Channel</label>
          <Select value={deliverChannel} onChange={(e) => setDeliverChannel(e.target.value)}
            options={CHANNELS.map((c) => ({ value: c, label: c }))} />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Recipient (email/@channel/URL)</label>
          <Input value={deliverRecipient}
            onChange={(e) => setDeliverRecipient(e.target.value)}
            placeholder="user@example.com" />
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="text-xs font-medium text-muted-foreground">Format</label>
            <Select value={deliverFormat} onChange={(e) => setDeliverFormat(e.target.value)}
              options={FORMATS.map((f) => ({ value: f, label: f.toUpperCase() }))} />
          </div>
          <div className="w-24">
            <label className="text-xs font-medium text-muted-foreground">Days</label>
            <Input type="number" value={deliverDays}
              onChange={(e) => setDeliverDays(Number(e.target.value))} min={1} max={365} />
          </div>
        </div>
        <Button onClick={handleDeliver} disabled={delivering || !deliverRecipient.trim()}>
          {delivering ? 'Sending...' : 'Send Report'}
        </Button>
      </div>
    </div>
  );
}
