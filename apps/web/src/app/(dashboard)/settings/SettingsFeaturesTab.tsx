'use client';

import { cn } from '@/lib/utils';
import { useSetFeatureFlag } from '@/features/organizations/api/useOrganizations';

const FEATURE_PRESETS = [
  { key: 'advanced_analytics', label: 'Advanced Analytics' },
  { key: 'custom_reports', label: 'Custom Reports' },
  { key: 'abi_testing', label: 'A/B Testing' },
  { key: 'multi_channel_publishing', label: 'Multi-Channel Publishing' },
  { key: 'email_marketing', label: 'Email Marketing' },
  { key: 'workflow_automation', label: 'Workflow Automation' },
  { key: 'api_access', label: 'API Access' },
  { key: 'white_label', label: 'White Label' },
];

interface SettingsFeaturesTabProps {
  orgId: string;
  features: any;
}

export function SettingsFeaturesTab({ orgId, features }: SettingsFeaturesTabProps) {
  const setFeatureFlag = useSetFeatureFlag();

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Feature Flags</h2>
        <p className="text-sm text-muted-foreground">Enable or disable features for this organization</p>
      </div>

      <div className="rounded-lg border bg-card">
        {FEATURE_PRESETS.map((preset) => {
          const flag = features?.find((f: any) => f.feature_key === preset.key);
          const enabled = flag?.enabled ?? false;
          return (
            <div key={preset.key} className="flex items-center justify-between border-b px-4 py-3 last:border-0">
              <span className="text-sm">{preset.label}</span>
              <button
                onClick={() => setFeatureFlag.mutate({
                  orgId,
                  feature_key: preset.key,
                  enabled: !enabled,
                })}
                className={cn(
                  'relative h-6 w-11 rounded-full transition-colors',
                  enabled ? 'bg-primary' : 'bg-muted',
                )}
              >
                <span className={cn(
                  'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-card transition-transform shadow-sm',
                  enabled && 'translate-x-5',
                )} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
